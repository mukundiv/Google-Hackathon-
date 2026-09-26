"""Learning Loop."""

from __future__ import annotations

import pytest

from app.engine.learn import fit_weights, learn, learned_activation_lead
from app.engine.match import BASELINE_WEIGHTS

# The relationship the seeded ledger actually encodes (see scripts/_brand.py).
TRUE_WEIGHTS = {
    "content_fit": 0.34,
    "audience_fit": 0.24,
    "brand_fit": 0.10,
    "momentum": 0.24,
    "proven_performance": 0.08,
}


def test_weights_stay_normalised(campaigns):
    weights, _, _ = fit_weights(campaigns)
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-6)
    assert all(w >= 0 for w in weights.values())


def test_learning_moves_every_signal_toward_the_truth(campaigns):
    """The ledger was generated under a different weighting than the engine
    starts with. Learning should discover it from outcomes alone."""
    learned, _, _ = fit_weights(campaigns)
    for signal, true_w in TRUE_WEIGHTS.items():
        baseline_err = abs(BASELINE_WEIGHTS[signal] - true_w)
        learned_err = abs(learned[signal] - true_w)
        assert learned_err < baseline_err, (
            f"{signal}: learned {learned[signal]:.3f} is no closer to {true_w} "
            f"than the baseline {BASELINE_WEIGHTS[signal]:.3f}"
        )


def test_learning_gets_the_direction_right(campaigns):
    learned, _, _ = fit_weights(campaigns)
    assert learned["content_fit"] > BASELINE_WEIGHTS["content_fit"]
    assert learned["momentum"] > BASELINE_WEIGHTS["momentum"]
    assert learned["brand_fit"] < BASELINE_WEIGHTS["brand_fit"]
    assert learned["proven_performance"] < BASELINE_WEIGHTS["proven_performance"]


def test_thin_evidence_leaves_the_prior_alone(campaigns):
    """Two campaigns should not be allowed to rewrite the model."""
    weights, blend, n = fit_weights(campaigns[:2])
    assert n == 2 and blend == 0.0
    assert weights == BASELINE_WEIGHTS


def test_more_evidence_shifts_further(campaigns):
    _, blend_few, _ = fit_weights(campaigns[:4])
    _, blend_many, _ = fit_weights(campaigns)
    assert blend_many > blend_few


def test_activation_lead_is_learned_from_history(campaigns, brand):
    lead = learned_activation_lead(campaigns, brand.avg_activation_lead_days)
    assert 5.0 < lead < 14.0
    observed = [c.activation_lead_days for c in campaigns]
    assert min(observed) <= lead <= max(observed)


def test_calibration_reports_every_signal(campaigns, brand):
    state = learn(campaigns, brand.avg_activation_lead_days)
    assert {e.signal for e in state.calibration} == set(BASELINE_WEIGHTS)
    for e in state.calibration:
        assert -1.0 <= e.correlation_with_outcome <= 1.0
        assert e.samples == len(campaigns)


def test_state_carries_history_and_a_readable_summary(campaigns, brand):
    state = learn(campaigns, brand.avg_activation_lead_days)
    assert state.campaigns_learned_from == len(campaigns)
    assert state.history[0].version == "baseline"
    assert state.current.version != "baseline"
    assert len(state.prediction_error_trend) == len(campaigns)
    assert "weighted" in state.summary


def test_signals_that_predicted_well_gain_weight(campaigns, brand):
    """The calibration table should agree with what the weights did."""
    state = learn(campaigns, brand.avg_activation_lead_days)
    by_signal = {e.signal: e for e in state.calibration}
    best = max(by_signal.values(), key=lambda e: e.correlation_with_outcome)
    worst = min(by_signal.values(), key=lambda e: e.correlation_with_outcome)
    assert best.weight_delta > 0
    assert worst.weight_delta < 0
