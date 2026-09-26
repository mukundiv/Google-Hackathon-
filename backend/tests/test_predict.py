"""Capture Window: does the predictor recover what the generator encoded?"""

from __future__ import annotations

import pytest

from app.demo import DEMO_TODAY
from app.engine.predict import (
    ACT_THRESHOLD_DAYS,
    capture_window,
    classify_stage,
    fit_momentum,
    time_to_live,
)
from app.models.trend import LifecycleStage, Verdict


def _series(providers, trend):
    return providers.trends.momentum(trend.query_terms)


def test_recovers_time_to_live_across_all_trends(providers, trends, truth):
    """The generator builds each curve from a stated TTL; the predictor only
    ever sees noisy observations. It should get back close to the truth."""
    for trend in trends:
        fit = fit_momentum(_series(providers, trend), category=trend.category, today=DEMO_TODAY)
        ttl, _, _ = time_to_live(fit)
        expected = truth[trend.id]["ttl_days"]
        assert ttl == pytest.approx(expected, abs=max(6.0, expected * 0.22)), (
            f"{trend.name}: predicted TTL {ttl:.1f}d against a true {expected:.1f}d"
        )


def test_recovers_peak_day(providers, trends, truth):
    errors = []
    for trend in trends:
        fit = fit_momentum(_series(providers, trend), category=trend.category, today=DEMO_TODAY)
        errors.append(abs(fit.peak_day - truth[trend.id]["days_to_peak"]))
    assert sum(errors) / len(errors) < 4.0, f"mean peak-day error too high: {errors}"


def test_deck_scenario_social_running_clubs(providers, running_clubs, brand):
    """The deck's headline: a ~13-day capture window, verdict ACT."""
    window = capture_window(
        running_clubs, _series(providers, running_clubs),
        brand.avg_activation_lead_days, today=DEMO_TODAY,
    )
    assert window.verdict is Verdict.ACT
    assert window.capture_window_days == pytest.approx(13.0, abs=2.0)
    assert window.stage is LifecycleStage.ACCELERATING
    assert window.launch_within_hours and window.launch_within_hours > 0


def test_deck_scenario_strava_wrapped_is_a_pass(providers, trends, brand):
    """A trend that has already peaked must be rejected, not merely ranked low."""
    strava = next(t for t in trends if t.name == "Strava Wrapped")
    window = capture_window(
        strava, _series(providers, strava), brand.avg_activation_lead_days, today=DEMO_TODAY
    )
    assert window.verdict is Verdict.PASS
    assert window.capture_window_days <= 0
    assert window.stage is LifecycleStage.DECLINING


def test_capture_window_is_ttl_minus_activation_lead(providers, running_clubs):
    """The core identity the whole stage rests on."""
    for lead in (0.0, 5.0, 9.0, 40.0):
        w = capture_window(running_clubs, _series(providers, running_clubs), lead, today=DEMO_TODAY)
        assert w.capture_window_days == pytest.approx(w.ttl_days - lead, abs=0.11)


def test_slower_brand_loses_the_opportunity(providers, running_clubs):
    """Same trend, same data — a brand that cannot move fast enough gets a PASS.
    This is the Activation Gap made operational."""
    fast = capture_window(running_clubs, _series(providers, running_clubs), 5.0, today=DEMO_TODAY)
    slow = capture_window(running_clubs, _series(providers, running_clubs), 45.0, today=DEMO_TODAY)
    assert fast.verdict is Verdict.ACT
    assert slow.verdict is Verdict.PASS


def test_verdict_thresholds(providers, running_clubs):
    series = _series(providers, running_clubs)
    ttl = capture_window(running_clubs, series, 0.0, today=DEMO_TODAY).ttl_days
    assert capture_window(
        running_clubs, series, ttl - ACT_THRESHOLD_DAYS - 1, today=DEMO_TODAY
    ).verdict is Verdict.ACT
    assert capture_window(
        running_clubs, series, ttl - 1.0, today=DEMO_TODAY
    ).verdict is Verdict.MARGINAL
    assert capture_window(
        running_clubs, series, ttl + 1.0, today=DEMO_TODAY
    ).verdict is Verdict.PASS


def test_rising_trend_below_threshold_is_not_written_off(providers, trends):
    """A trend on its way up sits below 40% of a peak it has not reached yet.
    Treating that as expired rejected exactly the early opportunities the
    engine exists to surface."""
    early = next(t for t in trends if t.name == "Run-Commuting")
    fit = fit_momentum(_series(providers, early), category=early.category, today=DEMO_TODAY)
    ttl, _, _ = time_to_live(fit)
    assert fit.current_value < fit.peak_value * 0.6, "expected a genuinely early-stage trend"
    assert ttl > 20.0


def test_decay_regime_is_reported_honestly(providers, trends):
    """Before the peak the decay rate is assumed, not measured, and the engine
    has to say so."""
    rising = next(t for t in trends if t.name == "Hybrid Training")
    peaked = next(t for t in trends if t.name == "Silent Walking")
    assert fit_momentum(
        _series(providers, rising), category=rising.category, today=DEMO_TODAY
    ).decay_regime == "decay_from_prior"
    assert "observed" in fit_momentum(
        _series(providers, peaked), category=peaked.category, today=DEMO_TODAY
    ).decay_regime


def test_stage_classification_matches_generated_truth(providers, trends, truth):
    for trend in trends:
        fit = fit_momentum(_series(providers, trend), category=trend.category, today=DEMO_TODAY)
        stage = classify_stage(fit)
        true_peak = truth[trend.id]["days_to_peak"]
        if true_peak < -8:
            assert stage is LifecycleStage.DECLINING, trend.name
        elif true_peak > 8:
            assert stage in (LifecycleStage.EMERGING, LifecycleStage.ACCELERATING), trend.name


def test_short_series_is_refused(providers, running_clubs):
    with pytest.raises(ValueError):
        fit_momentum(_series(providers, running_clubs)[:5], today=DEMO_TODAY)
