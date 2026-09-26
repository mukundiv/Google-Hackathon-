"""Seeded stand-in for the YouTube Data API.

Returns the same Creator shape the live provider builds from channels.list /
videos.list, so the engine cannot tell the difference.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.data.loader import seed_creators
from app.models.creator import Creator
from app.models.trend import MomentumPoint

VELOCITY_WINDOW_DAYS = 14


class MockYouTubeProvider:
    mode = "mock"

    def find_creators(self, niche: str, query_terms: list[str], limit: int = 40) -> list[Creator]:
        return seed_creators()[:limit]

    def get_creator(self, creator_id: str) -> Creator | None:
        return next((c for c in seed_creators() if c.id == creator_id), None)

    def topic_velocity(self, query_terms: list[str], days: int = 180) -> list[MomentumPoint]:
        """How hard the platform is publishing into a topic, day by day.

        This is creator *supply*, which is a different fact from search demand
        and lags it — creators react to a trend after people start looking for
        it. It is reported separately rather than averaged into the search
        curve, because blending a lagged copy of a signal into it pushes every
        predicted peak late.

        Each matching upload contributes for the two weeks after it lands,
        weighted by the square root of its views so a large channel counts for
        more than a small one without swamping it.
        """
        terms = [t.lower() for t in query_terms if t.strip()]
        if not terms:
            return []

        creators = seed_creators()
        # "Now" in the seeded world: the most recent upload anywhere in the
        # catalogue. Anchoring to the most recent *matching* upload instead
        # silently shifted a dead topic's curve forward to look alive.
        anchor = max(
            (v.published_at for c in creators for v in c.videos),
            default=date.today(),
        )

        contributions: list[tuple[date, float]] = []
        for creator in creators:
            for video in creator.videos:
                text = video.text().lower()
                matches = sum(1 for t in terms if t in text)
                if matches:
                    contributions.append((video.published_at, matches * (video.views ** 0.5)))

        if not contributions:
            return []

        series: list[tuple[date, float]] = []
        for offset in range(days, -1, -1):
            day = anchor - timedelta(days=offset)
            window_start = day - timedelta(days=VELOCITY_WINDOW_DAYS)
            total = sum(w for d, w in contributions if window_start < d <= day)
            series.append((day, total))

        peak = max(v for _, v in series) or 1.0
        return [MomentumPoint(day=d, value=round(v / peak * 100, 2)) for d, v in series]

    def topic_supply(self, query_terms: list[str], days: int = 30) -> dict:
        terms = [t.lower() for t in query_terms if t.strip()]
        creators = seed_creators()
        anchor = max(
            (v.published_at for c in creators for v in c.videos), default=date.today()
        )
        current_start = anchor - timedelta(days=days)
        prior_start = anchor - timedelta(days=days * 2)

        uploads = prior = views = 0
        channels: set[str] = set()
        for creator in creators:
            for video in creator.videos:
                if not any(t in video.text().lower() for t in terms):
                    continue
                if current_start < video.published_at <= anchor:
                    uploads += 1
                    views += video.views
                    channels.add(creator.id)
                elif prior_start < video.published_at <= current_start:
                    prior += 1

        change = ((uploads - prior) / prior * 100.0) if prior else (100.0 if uploads else 0.0)
        return {
            "uploads": uploads,
            "channels": len(channels),
            "views": views,
            "prior_uploads": prior,
            "change_pct": round(change, 1),
            "window_days": days,
        }
