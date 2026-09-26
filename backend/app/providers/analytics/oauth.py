"""YouTube Analytics for channels whose owner has connected them.

This is the honest boundary of the whole product. Audience demographics,
watch time and retention are private to the channel owner: no API key buys
them, and no third-party vendor can bypass that — unified creator-data
platforms like Phyllo wrap this same OAuth flow rather than removing it.

So the engine works both ways. A connected channel yields verified
demographics. Everyone else gets a public-signal estimate, and the console
labels which is which rather than blending them into one confident-looking
number.

Tokens are written by `scripts/connect_channel.py` into the directory below,
one file per channel.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import BACKEND_ROOT, Settings
from app.models.creator import AudienceSegment
from app.store import cache_get, cache_set

log = logging.getLogger(__name__)

TOKEN_DIR = BACKEND_ROOT / ".tokens"

# YouTube Analytics reports age in its own buckets; these map onto the
# segment vocabulary the optimiser uses.
AGE_BUCKETS = {
    "age13-17": "13-17",
    "age18-24": "18-24",
    "age25-34": "25-34",
    "age35-44": "35-44",
    "age45-54": "45-54",
    "age55-64": "55-64",
    "age65-": "65+",
}


class OAuthAnalyticsProvider:
    mode = "oauth"

    def __init__(self, settings: Settings):
        if not settings.google_oauth_client_secrets:
            raise RuntimeError("Google OAuth client secrets are not configured")
        self.settings = settings
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)

    def _token_path(self, channel_id: str) -> Path:
        return TOKEN_DIR / f"{channel_id}.json"

    def is_connected(self, channel_id: str) -> bool:
        return self._token_path(channel_id).exists()

    def audience_breakdown(self, channel_id: str) -> list[AudienceSegment] | None:
        if not self.is_connected(channel_id):
            return None

        key = f"analytics:audience:{channel_id}"
        cached = cache_get(key, ttl_seconds=60 * 60 * 24)
        if cached is not None:
            return [AudienceSegment.model_validate(s) for s in cached]

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_info(
                json.loads(self._token_path(channel_id).read_text())
            )
            analytics = build("youtubeAnalytics", "v2", credentials=creds,
                              cache_discovery=False)
            response = (
                analytics.reports()
                .query(
                    ids=f"channel=={channel_id}",
                    startDate="2020-01-01",
                    endDate="2030-01-01",
                    metrics="viewerPercentage",
                    dimensions="ageGroup,gender",
                    sort="-viewerPercentage",
                )
                .execute()
            )
            segments = _to_segments(response, self._country(channel_id))
            cache_set(key, [s.model_dump(mode="json") for s in segments])
            return segments
        except Exception:
            log.warning("analytics lookup failed for %s", channel_id, exc_info=True)
            # A failure here must read as "not verified", never as a guess
            # dressed up as verified data.
            return None

    def _country(self, channel_id: str) -> str:
        meta = TOKEN_DIR / f"{channel_id}.meta.json"
        if meta.exists():
            try:
                return json.loads(meta.read_text()).get("country", "US")
            except Exception:
                pass
        return "US"


def _to_segments(response: dict, country: str) -> list[AudienceSegment]:
    """Map ageGroup × gender viewer percentages onto audience segments.

    Analytics has no interest dimension, so the interest slot is left general
    and the creator's public topic signals fill it in during scoring.
    """
    rows = response.get("rows", []) or []

    # Analytics reports whole percentages; AudienceSegment weights are
    # fractions that sum to ~1. Normalise before constructing, not after —
    # building the model with a raw percentage is a validation error, and the
    # rows do not reliably sum to 100 once "other" genders are dropped.
    raw: list[tuple[str, float]] = []
    total = 0.0
    for row in rows:
        age_raw, gender_raw, pct = row[0], row[1], float(row[2])
        age = AGE_BUCKETS.get(age_raw, age_raw)
        gender = {"male": "male", "female": "female"}.get(gender_raw.lower(), "other")
        if gender == "other" or pct <= 0:
            continue
        raw.append((f"{gender}:{age}:{country}:general", pct))
        total += pct

    if total <= 0:
        return []
    return [AudienceSegment(key=k, weight=round(pct / total, 4)) for k, pct in raw]
