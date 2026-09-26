"""YouTube Data API v3, live.

Quota is the binding constraint, not latency: the daily allowance is 10,000
units and `search.list` costs 100 of them, while `channels.list` and
`videos.list` cost 1 each. So searches are cached aggressively and the
expensive call is made once per topic, not once per creator.

What this provider can and cannot know matters. Public data gives real
subscriber counts, view counts, titles, tags and comments. It does *not* give
audience demographics — that is owner-only data behind OAuth. Audience
segments built here are therefore an explicit inference, flagged as ESTIMATED,
and the analytics provider overrides them for any channel whose owner has
connected it.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from app.config import Settings
from app.models.creator import AudienceSegment, Creator, CreatorVideo, Provenance
from app.models.trend import MomentumPoint
from app.store import cache_get, cache_get_stale, cache_set

log = logging.getLogger(__name__)

VIDEOS_PER_CHANNEL = 18
VELOCITY_WINDOW_DAYS = 14

# Topic-id prefixes YouTube assigns to channels, mapped onto the interest
# vocabulary the optimiser uses for coverage and overlap.
TOPIC_INTERESTS = {
    "/m/06ntj": "sports",
    "/m/037hz": "fitness",
    "/m/019_rr": "lifestyle",
    "/m/032tl": "fashion",
    "/m/027x7n": "fitness",
    "/m/06bvp": "wellness",
    "/m/05qt0": "lifestyle",
}


class LiveYouTubeProvider:
    mode = "live"

    def __init__(self, settings: Settings):
        from googleapiclient.discovery import build  # lazy: mock mode needs no SDK

        if not settings.youtube_api_key:
            raise RuntimeError("YOUTUBE_API_KEY is not set")
        self.settings = settings
        self.yt = build("youtube", "v3", developerKey=settings.youtube_api_key,
                        cache_discovery=False)

    # -- discovery ------------------------------------------------------
    def find_creators(self, niche: str, query_terms: list[str], limit: int = 40) -> list[Creator]:
        key = f"yt:creators:{niche}:{','.join(sorted(query_terms))}:{limit}"
        cached = cache_get(key)
        if cached is not None:
            return [Creator.model_validate(c) for c in cached]

        try:
            channel_ids = self._search_channels(query_terms or [niche], limit)
            creators = [c for cid in channel_ids if (c := self._build_creator(cid))]
            cache_set(key, [c.model_dump(mode="json") for c in creators])
            return creators
        except Exception:
            log.warning("live creator discovery failed", exc_info=True)
            stale = cache_get_stale(key)
            if stale is not None:
                return [Creator.model_validate(c) for c in stale]
            raise

    def _search_channels(self, terms: list[str], limit: int) -> list[str]:
        """One search per term, at 100 quota units each — hence the cache."""
        seen: list[str] = []
        for term in terms[:4]:
            key = f"yt:search:{term}"
            ids = cache_get(key, ttl_seconds=60 * 60 * 24)
            if ids is None:
                response = (
                    self.yt.search()
                    .list(q=term, part="snippet", type="video", maxResults=50,
                          relevanceLanguage="en", order="relevance")
                    .execute()
                )
                ids = [
                    item["snippet"]["channelId"]
                    for item in response.get("items", [])
                    if item.get("snippet", {}).get("channelId")
                ]
                cache_set(key, ids)
            for cid in ids:
                if cid not in seen:
                    seen.append(cid)
            if len(seen) >= limit:
                break
        return seen[:limit]

    def _build_creator(self, channel_id: str) -> Creator | None:
        key = f"yt:channel:{channel_id}"
        cached = cache_get(key, ttl_seconds=60 * 60 * 24)
        if cached is not None:
            return Creator.model_validate(cached)
        try:
            channels = (
                self.yt.channels()
                .list(part="snippet,statistics,topicDetails,contentDetails", id=channel_id)
                .execute()
            ).get("items", [])
            if not channels:
                return None
            ch = channels[0]
            stats = ch.get("statistics", {})
            subscribers = int(stats.get("subscriberCount", 0) or 0)
            if subscribers < 10_000:  # too small to be a campaign candidate
                return None

            uploads = (
                ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
            )
            videos = self._recent_videos(uploads) if uploads else []
            avg_views = int(sum(v.views for v in videos) / len(videos)) if videos else 0
            topics = _topics(ch)
            comments = self._sample_comments(videos)

            creator = Creator(
                id=f"creator-{channel_id}",
                channel_id=channel_id,
                name=ch["snippet"]["title"],
                handle=ch["snippet"].get("customUrl", "") or f"@{channel_id[:10]}",
                archetype=_archetype(topics, subscribers),
                subscribers=subscribers,
                avg_views=avg_views,
                country=ch["snippet"].get("country", "US"),
                topics=topics,
                positioning=ch["snippet"].get("description", "")[:600],
                videos=videos,
                audience_segments=_infer_segments(topics, ch["snippet"].get("country", "US")),
                audience_provenance=Provenance.ESTIMATED,
                sample_comments=comments,
                base_cpm_usd=_cpm_for(subscribers),
                analytics_connected=False,
            )
            cache_set(key, creator.model_dump(mode="json"))
            return creator
        except Exception:
            log.warning("could not build creator %s", channel_id, exc_info=True)
            return None

    def _recent_videos(self, uploads_playlist: str) -> list[CreatorVideo]:
        items = (
            self.yt.playlistItems()
            .list(part="contentDetails", playlistId=uploads_playlist,
                  maxResults=VIDEOS_PER_CHANNEL)
            .execute()
        ).get("items", [])
        ids = [i["contentDetails"]["videoId"] for i in items]
        if not ids:
            return []
        details = (
            self.yt.videos()
            .list(part="snippet,statistics,contentDetails", id=",".join(ids))
            .execute()
        ).get("items", [])

        videos = []
        for v in details:
            snip, stats = v.get("snippet", {}), v.get("statistics", {})
            videos.append(
                CreatorVideo(
                    id=v["id"],
                    title=snip.get("title", ""),
                    description=(snip.get("description", "") or "")[:900],
                    tags=snip.get("tags", [])[:12],
                    published_at=_parse_date(snip.get("publishedAt", "")),
                    views=int(stats.get("viewCount", 0) or 0),
                    likes=int(stats.get("likeCount", 0) or 0),
                    comments=int(stats.get("commentCount", 0) or 0),
                    duration_seconds=_parse_duration(
                        v.get("contentDetails", {}).get("duration", "")
                    ),
                )
            )
        return videos

    def _sample_comments(self, videos: list[CreatorVideo], limit: int = 20) -> list[str]:
        if not videos:
            return []
        try:
            response = (
                self.yt.commentThreads()
                .list(part="snippet", videoId=videos[0].id, maxResults=limit,
                      order="relevance", textFormat="plainText")
                .execute()
            )
            return [
                item["snippet"]["topLevelComment"]["snippet"]["textDisplay"][:300]
                for item in response.get("items", [])
            ]
        except Exception:
            # Comments are often disabled; that is not an error worth failing on.
            return []

    def get_creator(self, creator_id: str) -> Creator | None:
        return self._build_creator(creator_id.replace("creator-", "", 1))

    # -- topic signals --------------------------------------------------
    def topic_velocity(self, query_terms: list[str], days: int = 180) -> list[MomentumPoint]:
        videos = self._topic_videos(query_terms, days)
        if not videos:
            return []
        anchor = max(d for d, _ in videos)
        series = []
        for offset in range(days, -1, -1):
            day = anchor - timedelta(days=offset)
            start = day - timedelta(days=VELOCITY_WINDOW_DAYS)
            series.append((day, sum(w for d, w in videos if start < d <= day)))
        peak = max(v for _, v in series) or 1.0
        return [MomentumPoint(day=d, value=round(v / peak * 100, 2)) for d, v in series]

    def topic_supply(self, query_terms: list[str], days: int = 30) -> dict:
        key = f"yt:supply:{','.join(sorted(query_terms))}:{days}"
        cached = cache_get(key, ttl_seconds=60 * 60 * 6)
        if cached is not None:
            return cached
        try:
            after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            prior_after = (datetime.now(timezone.utc) - timedelta(days=days * 2)).isoformat()
            current = self._search_count(query_terms, after)
            prior = self._search_count(query_terms, prior_after, before=after)
            change = ((current["uploads"] - prior["uploads"]) / prior["uploads"] * 100
                      if prior["uploads"] else (100.0 if current["uploads"] else 0.0))
            result = {
                "uploads": current["uploads"],
                "channels": current["channels"],
                "views": current["views"],
                "prior_uploads": prior["uploads"],
                "change_pct": round(change, 1),
                "window_days": days,
            }
            cache_set(key, result)
            return result
        except Exception:
            log.warning("topic supply lookup failed", exc_info=True)
            return cache_get_stale(key) or {
                "uploads": 0, "channels": 0, "views": 0,
                "prior_uploads": 0, "change_pct": 0.0, "window_days": days,
            }

    def _search_count(self, terms: list[str], after: str, before: str | None = None) -> dict:
        ids, channels = [], set()
        for term in terms[:2]:
            params = dict(q=term, part="snippet", type="video", maxResults=50,
                          publishedAfter=after, order="date")
            if before:
                params["publishedBefore"] = before
            response = self.yt.search().list(**params).execute()
            for item in response.get("items", []):
                ids.append(item["id"]["videoId"])
                channels.add(item["snippet"]["channelId"])
        views = 0
        for batch in _chunks(ids, 50):
            details = self.yt.videos().list(part="statistics", id=",".join(batch)).execute()
            views += sum(int(v["statistics"].get("viewCount", 0) or 0)
                         for v in details.get("items", []))
        return {"uploads": len(ids), "channels": len(channels), "views": views}

    def _topic_videos(self, query_terms: list[str], days: int) -> list[tuple[date, float]]:
        key = f"yt:topicvideos:{','.join(sorted(query_terms))}:{days}"
        cached = cache_get(key, ttl_seconds=60 * 60 * 12)
        if cached is not None:
            return [(date.fromisoformat(d), w) for d, w in cached]
        try:
            after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            out: list[tuple[date, float]] = []
            for term in query_terms[:2]:
                response = (
                    self.yt.search()
                    .list(q=term, part="snippet", type="video", maxResults=50,
                          publishedAfter=after, order="date")
                    .execute()
                )
                ids = [i["id"]["videoId"] for i in response.get("items", [])]
                for batch in _chunks(ids, 50):
                    details = (
                        self.yt.videos()
                        .list(part="snippet,statistics", id=",".join(batch))
                        .execute()
                    )
                    for v in details.get("items", []):
                        published = _parse_date(v["snippet"].get("publishedAt", ""))
                        views = int(v["statistics"].get("viewCount", 0) or 0)
                        out.append((published, views ** 0.5))
            cache_set(key, [[d.isoformat(), w] for d, w in out])
            return out
        except Exception:
            log.warning("topic video lookup failed", exc_info=True)
            stale = cache_get_stale(key)
            return [(date.fromisoformat(d), w) for d, w in stale] if stale else []


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _parse_date(value: str) -> date:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except Exception:
        return date.today()


def _parse_duration(iso: str) -> int:
    """ISO 8601 durations, as YouTube returns them (PT12M34S)."""
    if not iso.startswith("PT"):
        return 0
    total, number = 0, ""
    for ch in iso[2:]:
        if ch.isdigit():
            number += ch
        else:
            value = int(number or 0)
            total += value * {"H": 3600, "M": 60, "S": 1}.get(ch, 0)
            number = ""
    return total


def _topics(channel: dict) -> list[str]:
    raw = channel.get("topicDetails", {}).get("topicCategories", []) or []
    names = [u.rsplit("/", 1)[-1].replace("_", " ").lower() for u in raw]
    return names[:6] or ["general"]


def _archetype(topics: list[str], subscribers: int) -> str:
    joined = " ".join(topics)
    if subscribers > 1_500_000:
        return "Celebrity Fitness Creator"
    if "running" in joined or "marathon" in joined:
        return "Running Community Creator"
    if "fashion" in joined:
        return "Athleisure & Style Creator"
    if "health" in joined or "wellness" in joined:
        return "Wellness & Recovery Creator"
    if "sport" in joined:
        return "Sports Creator"
    return "Fitness & Lifestyle Creator"


def _infer_segments(topics: list[str], country: str) -> list[AudienceSegment]:
    """A coarse audience estimate from public signals only.

    This is a genuine inference and is labelled as such everywhere it surfaces.
    Real demographics require the channel owner to connect their analytics; see
    `app/providers/analytics/oauth.py`. A brand should be able to see at a
    glance which creators' audience data is earned and which is guessed.
    """
    joined = " ".join(topics)
    interest = "fitness"
    for key, value in (("running", "running"), ("fashion", "fashion"),
                       ("health", "wellness"), ("lifestyle", "lifestyle"),
                       ("sport", "sports")):
        if key in joined:
            interest = value
            break

    geo = country or "US"
    spread = {
        f"female:18-24:{geo}:{interest}": 0.24,
        f"female:25-34:{geo}:{interest}": 0.21,
        f"male:18-24:{geo}:{interest}": 0.15,
        f"male:25-34:{geo}:{interest}": 0.16,
        f"female:25-34:{geo}:fitness": 0.10,
        f"male:35-44:{geo}:{interest}": 0.08,
        f"female:35-44:{geo}:{interest}": 0.06,
    }
    return [AudienceSegment(key=k, weight=v) for k, v in spread.items()]


def _cpm_for(subscribers: int) -> float:
    """Rate cards rise with audience size; these are mid-market US benchmarks."""
    if subscribers > 2_000_000:
        return 58.0
    if subscribers > 750_000:
        return 52.0
    if subscribers > 250_000:
        return 46.0
    return 38.0
