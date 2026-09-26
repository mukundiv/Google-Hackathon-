"""Provider swap layer.

The promise is that the console runs fully with no credentials, that asking
for live without a key degrades rather than crashes, and that the degradation
is visible rather than silent.
"""

from __future__ import annotations

import pytest

from app.config import Settings
from app.providers.registry import get_providers, reset_providers


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_providers()
    yield
    reset_providers()


def test_default_is_mock_everywhere():
    s = Settings(_env_file=None)
    assert s.effective_gemini_mode() == "mock"
    assert s.effective_youtube_mode() == "mock"
    assert s.effective_trends_mode() == "mock"
    assert s.effective_analytics_mode() == "mock"


@pytest.mark.parametrize(
    "kwargs,accessor",
    [
        ({"gemini_mode": "live"}, "effective_gemini_mode"),
        ({"youtube_mode": "live"}, "effective_youtube_mode"),
        ({"trends_mode": "bigquery"}, "effective_trends_mode"),
        ({"analytics_mode": "oauth"}, "effective_analytics_mode"),
    ],
)
def test_live_without_a_credential_degrades_to_mock(kwargs, accessor):
    """Asking for live with no key must not take the console down mid-demo."""
    s = Settings(_env_file=None, **kwargs)
    assert getattr(s, accessor)() == "mock"


def test_credentials_enable_the_live_mode():
    assert Settings(_env_file=None, gemini_mode="live",
                    gemini_api_key="x").effective_gemini_mode() == "live"
    assert Settings(_env_file=None, youtube_mode="live",
                    youtube_api_key="x").effective_youtube_mode() == "live"
    assert Settings(_env_file=None, trends_mode="bigquery",
                    gcp_project_id="p").effective_trends_mode() == "bigquery"


def test_registry_reports_why_a_source_is_not_live(monkeypatch):
    monkeypatch.setenv("GEMINI_MODE", "live")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    reset_providers()

    status = {s.name: s for s in get_providers().status}
    assert status["gemini"].requested == "live"
    assert status["gemini"].active == "mock"
    assert status["gemini"].live is False
    assert "GEMINI_API_KEY" in status["gemini"].detail

    get_settings.cache_clear()


def test_every_provider_satisfies_its_protocol():
    from app.providers.base import (
        AnalyticsProvider,
        GeminiProvider,
        TrendsProvider,
        YouTubeProvider,
    )

    p = get_providers()
    assert isinstance(p.gemini, GeminiProvider)
    assert isinstance(p.youtube, YouTubeProvider)
    assert isinstance(p.trends, TrendsProvider)
    assert isinstance(p.analytics, AnalyticsProvider)


def test_mock_analytics_models_the_real_consent_boundary():
    """Only channels whose owner connected them have verified demographics —
    that limit is real and the mock must not paper over it."""
    from app.data.loader import seed_creators

    p = get_providers()
    connected = [c for c in seed_creators() if p.analytics.is_connected(c.channel_id)]
    unconnected = [c for c in seed_creators() if not p.analytics.is_connected(c.channel_id)]

    assert connected, "the demo needs at least one connected channel"
    assert unconnected, "and at least one that is not"
    assert p.analytics.audience_breakdown(connected[0].channel_id) is not None
    assert p.analytics.audience_breakdown(unconnected[0].channel_id) is None


def test_live_modules_import_without_credentials():
    """They are imported lazily, but a syntax or import error in one should be
    caught here rather than the first time someone adds an API key."""
    import app.providers.analytics.oauth as oauth
    import app.providers.gemini.live as gemini
    import app.providers.trends.bigquery as bq
    import app.providers.youtube.live as yt

    for module in (gemini, yt, bq, oauth):
        assert module is not None

    with pytest.raises(RuntimeError):
        gemini.LiveGeminiProvider(Settings(_env_file=None, gemini_api_key=None))
    with pytest.raises(RuntimeError):
        yt.LiveYouTubeProvider(Settings(_env_file=None, youtube_api_key=None))
