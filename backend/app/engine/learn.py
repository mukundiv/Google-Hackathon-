"""Stage 05 — Learn: the Learning Loop.

PREDICT -> ACTIVATE -> OBSERVE -> LEARN. Campaign results come back, and the
engine re-weights the Creator Opportunity Score so the next recommendation is
better than the last.

Two things are learned from the ledger:

  * **Signal weights.** A ridge regression of each campaign's signal profile
    against what the campaign actually delivered. With single-digit campaigns
    and five correlated signals, the fit is heavily regularised and then
    blended with the baseline in proportion to how much evidence exists —
    eight campaigns should nudge the model, not rewrite it.
  * **Activation lead time.** How long this brand really takes to get live,
    which feeds straight back into the Capture Window. Campaigns teach the
    engine how fast the brand can move.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
from sklearn.linear_model import Ridge

from app.engine.match import BASELINE_WEIGHTS, SIGNAL_LABELS
from app.models.campaign import PastCampaign
from app.models.learning import CalibrationEntry, LearningState, SignalWeights

SIGNAL_ORDER = list(BASELINE_WEIGHTS.keys())

# Campaigns needed before the fitted weights are trusted as much as the
# baseline. Keeps a short ledger from swinging the model around.
EVIDENCE_HALF_LIFE = 8.0
RIDGE_ALPHA = 1.0


def _design_matrix(campaigns: list[PastCampaign]) -> tuple[np.ndarray, np.ndarray]:
    rows, targets = [], []
    for c in campaigns:
        if not c.signal_snapshot:
            continue
        rows.append([float(c.signal_snapshot.get(s, 50.0)) for s in SIGNAL_ORDER])
        targets.append(float(c.actual.performance_index))
    return np.array(rows, dtype=float), np.array(targets, dtype=float)


def fit_weights(campaigns: list[PastCampaign]) -> tuple[dict[str, float], float, int]:
    """Regress signal profiles against delivered performance.

    Returns (weights, blend_factor, n_campaigns). Weights are non-negative and
    sum to 1; a signal that never helped should carry no weight, not a
    negative one, since the score is a weighted average rather than a
    regression output.
    """
    X, y = _design_matrix(campaigns)
    n = len(y)
    if n < 3:
        return dict(BASELINE_WEIGHTS), 0.0, n

    mu, sigma = X.mean(axis=0), X.std(axis=0)
    sigma[sigma == 0] = 1.0
    Xs = (X - mu) / sigma

    model = Ridge(alpha=RIDGE_ALPHA, fit_intercept=True)
    model.fit(Xs, y)

    # Back out per-unit importance, then treat magnitude as weight.
    coefs = np.clip(model.coef_ / sigma, 0.0, None)
    if coefs.sum() <= 0:
        return dict(BASELINE_WEIGHTS), 0.0, n
    fitted = coefs / coefs.sum()

    blend = n / (n + EVIDENCE_HALF_LIFE)
    baseline = np.array([BASELINE_WEIGHTS[s] for s in SIGNAL_ORDER])
    blended = (1.0 - blend) * baseline + blend * fitted
    blended = blended / blended.sum()

    return {s: float(round(w, 4)) for s, w in zip(SIGNAL_ORDER, blended)}, float(blend), n


def calibration(
    campaigns: list[PastCampaign], before: dict[str, float], after: dict[str, float]
) -> list[CalibrationEntry]:
    """How well each signal tracked reality, and how its weight moved."""
    X, y = _design_matrix(campaigns)
    entries: list[CalibrationEntry] = []
    if len(y) < 2:
        return entries

    for i, signal in enumerate(SIGNAL_ORDER):
        col = X[:, i]
        corr = float(np.corrcoef(col, y)[0, 1]) if col.std() > 0 else 0.0
        errors = y - col
        entries.append(
            CalibrationEntry(
                signal=signal,
                label=SIGNAL_LABELS[signal],
                mean_abs_error=round(float(np.mean(np.abs(errors))), 2),
                bias=round(float(np.mean(errors)), 2),
                correlation_with_outcome=round(corr if np.isfinite(corr) else 0.0, 3),
                samples=len(y),
                weight_before=round(before.get(signal, 0.0), 4),
                weight_after=round(after.get(signal, 0.0), 4),
            )
        )
    entries.sort(key=lambda e: abs(e.weight_delta), reverse=True)
    return entries


def learned_activation_lead(campaigns: list[PastCampaign], fallback: float) -> float:
    """What this brand's activation actually takes, weighted toward recent runs."""
    if not campaigns:
        return fallback
    ordered = sorted(campaigns, key=lambda c: c.launched_at)
    leads = np.array([c.activation_lead_days for c in ordered], dtype=float)
    weights = np.linspace(0.6, 1.4, len(leads))
    return float(round(np.average(leads, weights=weights), 1))


def error_trend(campaigns: list[PastCampaign]) -> list[dict]:
    out = []
    for c in sorted(campaigns, key=lambda c: c.launched_at):
        out.append(
            {
                "campaign_id": c.id,
                "name": c.name,
                "launched_at": c.launched_at.isoformat(),
                "predicted": round(c.predicted.performance_index, 1),
                "actual": round(c.actual.performance_index, 1),
                "error": round(c.prediction_error, 1),
                "abs_error": round(abs(c.prediction_error), 1),
            }
        )
    return out


def learn(campaigns: list[PastCampaign], fallback_lead: float = 9.0) -> LearningState:
    weights, blend, n = fit_weights(campaigns)
    baseline = SignalWeights(
        version="baseline",
        created_at=datetime.now(timezone.utc),
        weights=dict(BASELINE_WEIGHTS),
        trained_on_campaigns=0,
        method="hand-set prior",
        note="Starting weights before any campaign feedback.",
    )
    current = SignalWeights(
        version=f"v{n}" if n else "baseline",
        created_at=datetime.now(timezone.utc),
        weights=weights,
        trained_on_campaigns=n,
        method="ridge regression on campaign outcomes, blended with the prior",
        note=(
            f"Fitted on {n} campaign(s); the fit carries {blend * 100:.0f}% of the "
            "weight against the prior, scaled by how much evidence exists."
        ),
    )
    entries = calibration(campaigns, baseline.weights, weights)

    return LearningState(
        current=current,
        history=[baseline, current] if n else [baseline],
        calibration=entries,
        prediction_error_trend=error_trend(campaigns),
        activation_lead_days=learned_activation_lead(campaigns, fallback_lead),
        campaigns_learned_from=n,
        summary=_summary(entries, n),
    )


def _summary(entries: list[CalibrationEntry], n: int) -> str:
    if not entries or n < 3:
        return "Not enough campaign history yet to re-weight the model."
    up = [e for e in entries if e.weight_delta > 0.005]
    down = [e for e in entries if e.weight_delta < -0.005]
    parts = []
    if up:
        parts.append(
            "up-weighted " + ", ".join(f"{e.label} (+{e.weight_delta * 100:.1f}pts)" for e in up[:2])
        )
    if down:
        parts.append(
            "down-weighted "
            + ", ".join(f"{e.label} ({e.weight_delta * 100:.1f}pts)" for e in down[:2])
        )
    if not parts:
        return f"After {n} campaigns the weighting is holding steady."
    return f"After {n} campaigns the engine has " + " and ".join(parts) + "."
