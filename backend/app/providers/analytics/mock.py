"""Stand-in for YouTube Analytics.

Mirrors the real constraint rather than papering over it: analytics exist only
for channels whose owner has connected them. Two seeded creators are treated as
connected so the console can show verified and estimated audience data side by
side; every other creator returns None and the engine falls back to an
inferred estimate, labelled as such.
"""

from __future__ import annotations

from app.data.loader import seed_creators
from app.models.creator import AudienceSegment

# Stands in for "these channel owners completed the OAuth flow".
CONNECTED_CREATOR_IDS = {"creator-run_community-1", "creator-marathon_coach-1"}


class MockAnalyticsProvider:
    mode = "mock"

    def _channel_to_creator(self, channel_id: str):
        return next((c for c in seed_creators() if c.channel_id == channel_id), None)

    def is_connected(self, channel_id: str) -> bool:
        creator = self._channel_to_creator(channel_id)
        return bool(creator and creator.id in CONNECTED_CREATOR_IDS)

    def audience_breakdown(self, channel_id: str) -> list[AudienceSegment] | None:
        creator = self._channel_to_creator(channel_id)
        if creator is None or creator.id not in CONNECTED_CREATOR_IDS:
            return None
        # Verified data is sharper than the public-signal estimate: the real
        # split is slightly more concentrated than an outsider would guess.
        sharpened = []
        total = 0.0
        for seg in creator.audience_segments:
            w = seg.weight ** 1.18
            sharpened.append((seg.key, w))
            total += w
        return [AudienceSegment(key=k, weight=round(w / total, 4)) for k, w in sharpened]
