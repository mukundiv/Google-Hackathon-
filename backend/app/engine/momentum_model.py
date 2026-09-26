"""The momentum model shared by the predictor and the seed generator.

A trend's momentum is modelled as a logistic rise that begins decaying once
adoption reaches a fixed fraction of its ceiling:

    m(t) = L / (1 + e^(-k(t - t0)))  *  e^(-max(0, t - tp) / tau)
    tp   = t0 + logit(SATURATION) / k

The important design choice is that **the decay onset `tp` is derived, not
fitted**. An earlier version made it a free parameter and the fit was
degenerate: for a trend that has not peaked yet the future peak is simply not
in the data, so the optimiser could place it anywhere and still match the
observed rise (r^2 ~ 0.98 with the peak 50 days out of position). Deriving `tp`
from the rise removes that freedom.

The decay constant `tau` has the same problem in reverse — it is only
observable *after* the peak. So:

  * past the peak, the data determines tau;
  * before the peak, tau comes from a category prior, and the fit may only
    move it inside a bounded band around that prior.

That is an assumption, and the engine says so: every CaptureWindow reports
which regime produced it. Pretending to measure an unobservable is how you get
a confident wrong answer.
"""

from __future__ import annotations

import math

import numpy as np

# Decay begins once the rise reaches this fraction of its ceiling.
SATURATION = 0.85
S = math.log(SATURATION / (1.0 - SATURATION))  # 1.7346

# Prior decay constants in days, by trend category. Calibrated from the decay
# observed in the brand's own campaign ledger; documented as an assumption.
DECAY_PRIORS: dict[str, float] = {
    "community_behaviour": 11.0,
    "training_method": 13.0,
    "style": 11.0,
    "seasonal_product": 15.0,
    "wellness_fad": 10.0,
    "wellness": 12.0,
}
DEFAULT_DECAY_PRIOR = 13.0

# How far the fit may move tau away from its prior when the data is pre-peak.
PRIOR_BAND = (0.5, 2.0)


def decay_prior(category: str) -> float:
    return DECAY_PRIORS.get(category, DEFAULT_DECAY_PRIOR)


def peak_day(k: float, t0: float) -> float:
    """When decay begins — the curve's maximum."""
    return t0 + S / k


def momentum_curve(t, L: float, k: float, t0: float, tau: float):
    """Vectorised momentum curve. `t` is days relative to today."""
    t = np.asarray(t, dtype=float)
    tp = t0 + S / k
    rise = L / (1.0 + np.exp(-np.clip(k * (t - t0), -500.0, 500.0)))
    decay = np.exp(-np.maximum(0.0, t - tp) / tau)
    return rise * decay


def peak_value(L: float) -> float:
    """The curve's maximum is always SATURATION * L, by construction."""
    return SATURATION * L


def solve_from_narrative(current: float, days_to_peak: float, k: float, tau: float) -> dict:
    """Closed-form parameters for a trend described in plain terms.

    Used by the seed generator: given where a trend is today, when it peaks and
    how steeply it rises, there is exactly one (L, t0) that fits.
    """
    t0 = days_to_peak - S / k
    rise_at_zero = 1.0 / (1.0 + math.exp(-k * (0.0 - t0)))
    decay_at_zero = math.exp(-max(0.0, 0.0 - days_to_peak) / tau)
    L = current / (rise_at_zero * decay_at_zero)
    return {"L": L, "k": k, "t0": t0, "tau": tau}
