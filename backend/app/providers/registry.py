"""Resolves the active provider for each signal source.

Live implementations are imported lazily so that mock mode never depends on a
Google SDK being installed or a credential being present. If a live provider
fails to construct, the registry falls back to mock and records why — the
console surfaces that as a degraded badge rather than a stack trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.config import Settings, get_settings
from app.providers.analytics.mock import MockAnalyticsProvider
from app.providers.base import AnalyticsProvider, GeminiProvider, TrendsProvider, YouTubeProvider
from app.providers.gemini.mock import MockGeminiProvider
from app.providers.trends.mock import MockTrendsProvider
from app.providers.youtube.mock import MockYouTubeProvider


@dataclass
class ProviderStatus:
    name: str
    requested: str
    active: str
    live: bool
    detail: str = ""


@dataclass
class Providers:
    gemini: GeminiProvider
    youtube: YouTubeProvider
    trends: TrendsProvider
    analytics: AnalyticsProvider
    status: list[ProviderStatus]

    def status_map(self) -> dict[str, dict]:
        return {
            s.name: {
                "requested": s.requested,
                "active": s.active,
                "live": s.live,
                "detail": s.detail,
            }
            for s in self.status
        }


def _resolve_gemini(settings: Settings) -> tuple[GeminiProvider, ProviderStatus]:
    requested = settings.gemini_mode
    effective = settings.effective_gemini_mode()
    if effective == "live":
        try:
            from app.providers.gemini.live import LiveGeminiProvider

            return LiveGeminiProvider(settings), ProviderStatus(
                "gemini", requested, "live", True, f"model {settings.gemini_model}"
            )
        except Exception as exc:  # pragma: no cover - depends on env
            return MockGeminiProvider(), ProviderStatus(
                "gemini", requested, "mock", False, f"live init failed: {exc}"
            )
    detail = "" if requested == "mock" else "GEMINI_API_KEY not set"
    return MockGeminiProvider(), ProviderStatus("gemini", requested, "mock", False, detail)


def _resolve_youtube(settings: Settings) -> tuple[YouTubeProvider, ProviderStatus]:
    requested = settings.youtube_mode
    if settings.effective_youtube_mode() == "live":
        try:
            from app.providers.youtube.live import LiveYouTubeProvider

            return LiveYouTubeProvider(settings), ProviderStatus(
                "youtube", requested, "live", True, "YouTube Data API v3"
            )
        except Exception as exc:  # pragma: no cover
            return MockYouTubeProvider(), ProviderStatus(
                "youtube", requested, "mock", False, f"live init failed: {exc}"
            )
    detail = "" if requested == "mock" else "YOUTUBE_API_KEY not set"
    return MockYouTubeProvider(), ProviderStatus("youtube", requested, "mock", False, detail)


def _resolve_trends(settings: Settings) -> tuple[TrendsProvider, ProviderStatus]:
    requested = settings.trends_mode
    if settings.effective_trends_mode() == "bigquery":
        try:
            from app.providers.trends.bigquery import BigQueryTrendsProvider

            return BigQueryTrendsProvider(settings), ProviderStatus(
                "trends", requested, "bigquery", True, "bigquery-public-data.google_trends"
            )
        except Exception as exc:  # pragma: no cover
            return MockTrendsProvider(), ProviderStatus(
                "trends", requested, "mock", False, f"live init failed: {exc}"
            )
    detail = "" if requested == "mock" else "GCP_PROJECT_ID not set"
    return MockTrendsProvider(), ProviderStatus("trends", requested, "mock", False, detail)


def _resolve_analytics(settings: Settings) -> tuple[AnalyticsProvider, ProviderStatus]:
    requested = settings.analytics_mode
    if settings.effective_analytics_mode() == "oauth":
        try:
            from app.providers.analytics.oauth import OAuthAnalyticsProvider

            return OAuthAnalyticsProvider(settings), ProviderStatus(
                "analytics", requested, "oauth", True, "YouTube Analytics API (connected channels)"
            )
        except Exception as exc:  # pragma: no cover
            return MockAnalyticsProvider(), ProviderStatus(
                "analytics", requested, "mock", False, f"live init failed: {exc}"
            )
    detail = "" if requested == "mock" else "OAuth client secrets not configured"
    return MockAnalyticsProvider(), ProviderStatus("analytics", requested, "mock", False, detail)


@lru_cache
def get_providers() -> Providers:
    settings = get_settings()
    gemini, g_status = _resolve_gemini(settings)
    youtube, y_status = _resolve_youtube(settings)
    trends, t_status = _resolve_trends(settings)
    analytics, a_status = _resolve_analytics(settings)
    return Providers(
        gemini=gemini,
        youtube=youtube,
        trends=trends,
        analytics=analytics,
        status=[g_status, y_status, t_status, a_status],
    )


def reset_providers() -> None:
    """Drop the cached registry — used by tests and by config changes."""
    get_providers.cache_clear()
