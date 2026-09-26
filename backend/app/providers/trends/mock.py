"""Seeded stand-in for Google Trends momentum."""

from __future__ import annotations

from app.data.loader import seed_trends
from app.models.trend import MomentumPoint


class MockTrendsProvider:
    mode = "mock"

    def momentum(
        self, query_terms: list[str], market: str = "US", days: int = 180
    ) -> list[MomentumPoint]:
        """Match the query terms back to a seeded trend and return its curve."""
        wanted = {t.lower().strip() for t in query_terms}
        best, best_overlap = None, 0
        for trend in seed_trends():
            have = {t.lower().strip() for t in trend.query_terms}
            overlap = len(wanted & have)
            if overlap > best_overlap:
                best, best_overlap = trend, overlap
        if best is None:
            return []
        return best.momentum_series[-(days + 1):]
