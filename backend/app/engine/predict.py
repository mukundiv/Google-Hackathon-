"""Stage 02 — Predict: the Capture Window.

The deck's central claim, made arithmetic:

    capture window = time-to-live  -  activation lead time

A trend is only an opportunity if it outlives the brand's own
Identify -> Analyze -> Select -> Approve -> Produce -> Launch chain. Momentum
alone says a trend is hot; the capture window says whether being hot is any
use to *this* brand.

Two separate numbers come out of the fit and they answer different questions:

    capture_window_days   how long the opportunity stays worth having
    launch_within_hours   how long you can deliberate and still land content
                          before the peak, after which the same content
                          underperforms
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np
from scipy.optimize import curve_fit

from app.engine.momentum_model import (
    SATURATION,
    PRIOR_BAND,
    S,
    decay_prior,
    momentum_curve,
    peak_day,
    peak_value,
)
from app.models.trend import CaptureWindow, LifecycleStage, MomentumPoint, Trend, Verdict

RELEVANCE_FRACTION = 0.40
ACT_THRESHOLD_DAYS = 7.0
SEARCH_HORIZON_DAYS = 365
# Days of observed decline at which the measured decay constant is trusted
# about as much as the category prior.
DECAY_SHRINKAGE_DAYS = 20.0

# Measurement-noise model: a small floor plus a component that scales with
# the momentum level. Used to weight the curve fit.
NOISE_FLOOR = 0.35
NOISE_SCALE = 0.045


@dataclass
class MomentumFit:
    L: float
    k: float
    t0: float
    tau: float
    r_squared: float
    peak_value: float
    peak_day: float
    current_value: float
    decay_regime: str
    param_confidence: float

    @property
    def params(self) -> tuple[float, float, float, float]:
        return (self.L, self.k, self.t0, self.tau)

    def value_at(self, t: float) -> float:
        return float(momentum_curve(t, *self.params))


def blend_momentum(
    search: list[MomentumPoint],
    platform: list[MomentumPoint],
    search_weight: float = 0.6,
) -> list[MomentumPoint]:
    """Combine search interest with YouTube publishing/viewing velocity.

    Search says people are curious; platform velocity says creators are already
    making the content. A trend needs both to be worth a creator campaign.
    """
    if not search:
        return platform
    if not platform:
        return search

    by_day: dict[date, list[tuple[float, float]]] = {}
    for p in search:
        by_day.setdefault(p.day, []).append((p.value, search_weight))
    for p in platform:
        by_day.setdefault(p.day, []).append((p.value, 1.0 - search_weight))

    blended = []
    for day in sorted(by_day):
        pairs = by_day[day]
        total_w = sum(w for _, w in pairs)
        blended.append(
            MomentumPoint(day=day, value=round(sum(v * w for v, w in pairs) / total_w, 2))
        )
    return blended


def _has_turned_over(t: np.ndarray, y: np.ndarray) -> bool:
    """Is the decline actually in the data?

    Only then is the decay constant measurable; otherwise it has to come from
    the prior.
    """
    if len(y) < 30:
        return False
    peak_i = int(np.argmax(y))
    days_since_peak = float(t[-1] - t[peak_i])
    recent = float(np.mean(y[-14:]))
    observed_peak = float(y[peak_i])

    if days_since_peak >= 6.0 and recent < 0.92 * observed_peak:
        return True

    # Or: the last three weeks are falling faster than the noise floor.
    tail = t >= (t.max() - 21)
    if int(np.sum(tail)) >= 10:
        slope = float(np.polyfit(t[tail], y[tail], 1)[0])
        noise = float(np.std(np.diff(y[tail]))) or 1.0
        if slope < 0 and abs(slope) > noise * 0.25:
            return True
    return False


def fit_momentum(
    points: list[MomentumPoint], category: str = "", today: date | None = None
) -> MomentumFit:
    """Fit (L, k, t0, tau). Decay onset is derived from the rise, never fitted."""
    if len(points) < 12:
        raise ValueError("need at least 12 momentum observations to fit a curve")

    anchor = today or max(p.day for p in points)
    t = np.array([(p.day - anchor).days for p in points], dtype=float)
    y = np.array([p.value for p in points], dtype=float)

    prior = decay_prior(category)
    post_peak = _has_turned_over(t, y)
    post_peak_days = float(t[-1] - t[int(np.argmax(y))]) if post_peak else 0.0
    if post_peak:
        tau_bounds = (1.0, 400.0)
        regime = "decay_observed"
    else:
        tau_bounds = (prior * PRIOR_BAND[0], prior * PRIOR_BAND[1])
        regime = "decay_from_prior"

    observed_peak = float(np.max(y))
    half = observed_peak / 2.0
    rising = np.where(y >= half)[0]
    t_half = float(t[rising[0]]) if len(rising) else float(t[0])

    # The momentum index is normalised to 0-100 and the curve peaks at
    # SATURATION * L, so a ceiling above 100/SATURATION is impossible by
    # construction. Without this bound the fit runs away on early-stage trends,
    # where the data carries almost no information about where the rise
    # saturates, and an inflated ceiling drags the predicted peak with it.
    l_max = 100.0 / SATURATION
    p0 = [
        float(np.clip(observed_peak / SATURATION, 12.0, l_max)),
        0.09,
        t_half,
        float(np.clip(prior, *tau_bounds)),
    ]
    bounds = (
        [12.0, 0.010, float(t.min()) - 200.0, tau_bounds[0]],
        [l_max, 0.900, float(t.max()) + 200.0, tau_bounds[1]],
    )

    try:
        # Weighted fit: momentum measurement noise grows with the level, so
        # equal weighting lets the long low-signal tail outvote the part of the
        # curve that actually determines where it saturates.
        #
        # Two passes, because deriving the weights from the observed values
        # biases the result: a point that happened to land high gets a larger
        # sigma and is therefore trusted less, so upward noise is systematically
        # discounted and the whole curve is dragged down. That cost about a day
        # of peak-position accuracy. The second pass recomputes the weights from
        # the first pass's fitted values, which carry no noise of their own.
        model = lambda tt, L, k, t0, tau: momentum_curve(tt, L, k, t0, tau)  # noqa: E731
        sigma = NOISE_FLOOR + NOISE_SCALE * np.maximum(y, 0.0)
        params, pcov = curve_fit(
            model, t, y, p0=p0, bounds=bounds, sigma=sigma, absolute_sigma=True, maxfev=60000
        )
        fitted = momentum_curve(t, *params)
        sigma = NOISE_FLOOR + NOISE_SCALE * np.maximum(fitted, 0.0)
        params, pcov = curve_fit(
            model, t, y, p0=list(params), bounds=bounds, sigma=sigma,
            absolute_sigma=True, maxfev=60000,
        )
        L, k, t0, tau = (float(v) for v in params)
        residuals = y - momentum_curve(t, L, k, t0, tau)
        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((y - y.mean()) ** 2)) or 1.0
        r2 = max(0.0, 1.0 - ss_res / ss_tot)

        errs = np.sqrt(np.clip(np.diag(pcov), 0.0, None))
        k_rel = float(errs[1]) / max(k, 1e-6)
        tau_rel = float(errs[3]) / max(tau, 1e-6)
        param_conf = float(np.clip(1.0 - 0.5 * k_rel - 0.5 * min(tau_rel, 2.0), 0.0, 1.0))
        if not post_peak:
            # tau was assumed, not measured — do not claim confidence we lack.
            param_conf *= 0.75
        # The earlier a trend is in its rise, the less the data says about where
        # that rise saturates, and the peak position inherits that uncertainty.
        maturity = float(np.clip(momentum_curve(0.0, L, k, t0, tau) / peak_value(L), 0.0, 1.0))
        if maturity < 0.6:
            param_conf *= 0.55 + 0.45 * (maturity / 0.6)
    except Exception:
        # Coarse linear extrapolation over the recent window, clearly flagged.
        recent = t >= (t.max() - 21)
        slope, intercept = np.polyfit(t[recent], y[recent], 1)
        current = float(intercept)
        k, t0, tau = 0.08, float(t_half), prior
        L = max(observed_peak / 0.85, current / 0.85, 12.0)
        return MomentumFit(
            L=L, k=k, t0=t0, tau=tau,
            r_squared=0.0,
            peak_value=peak_value(L),
            peak_day=peak_day(k, t0),
            current_value=current,
            decay_regime="linear_fallback",
            param_confidence=0.15,
        )

    if post_peak:
        # A decay constant read off a handful of post-peak days is not worth
        # much: Strava Wrapped had nine days of decline, and the unshrunk fit
        # overshot tau by 25%, which was enough on its own to turn a PASS into
        # a MARGINAL. Shrink toward the category prior in proportion to how
        # much decline has actually been observed.
        trust = post_peak_days / (post_peak_days + DECAY_SHRINKAGE_DAYS)
        shrunk = trust * tau + (1.0 - trust) * prior
        if trust < 0.8:
            regime = "decay_observed_shrunk"
            param_conf *= 0.6 + 0.4 * trust
        tau = shrunk

    return MomentumFit(
        L=L, k=k, t0=t0, tau=tau,
        r_squared=r2,
        peak_value=peak_value(L),
        peak_day=peak_day(k, t0),
        current_value=float(momentum_curve(0.0, L, k, t0, tau)),
        decay_regime=regime,
        param_confidence=param_conf,
    )


def time_to_live(fit: MomentumFit) -> tuple[float, float, float]:
    """Days until momentum drops below 40% of peak, with a confidence band."""
    threshold = fit.peak_value * RELEVANCE_FRACTION

    # Only a trend that has already peaked can be written off for being below
    # the threshold today. A trend still on its way up is *supposed* to sit
    # below 40% of a peak it has not reached yet — treating that as "expired"
    # was rejecting exactly the early opportunities the engine exists to find.
    if fit.peak_day <= 0.0 and fit.current_value < threshold:
        return 0.0, 0.0, 0.0

    ttl = float(SEARCH_HORIZON_DAYS)
    start = max(0.0, fit.peak_day)
    for day in np.arange(start, SEARCH_HORIZON_DAYS, 0.25):
        if fit.value_at(float(day)) < threshold:
            ttl = float(day)
            break

    spread = max(1.5, ttl * (1.0 - fit.param_confidence) * 0.5)
    return ttl, max(0.0, ttl - spread), ttl + spread


def classify_stage(fit: MomentumFit) -> LifecycleStage:
    """Place the trend on the deck's culture curve."""
    days_to_peak = fit.peak_day
    ratio = fit.current_value / fit.peak_value if fit.peak_value else 0.0
    if days_to_peak > 3.0:
        return LifecycleStage.EMERGING if ratio < 0.55 else LifecycleStage.ACCELERATING
    if days_to_peak >= -3.0:
        return LifecycleStage.PEAKING
    return LifecycleStage.DECLINING


def capture_window(
    trend: Trend,
    momentum_points: list[MomentumPoint],
    activation_lead_days: float,
    today: date | None = None,
) -> CaptureWindow:
    fit = fit_momentum(momentum_points, category=trend.category, today=today)
    ttl, ttl_low, ttl_high = time_to_live(fit)
    stage = classify_stage(fit)

    window = ttl - activation_lead_days

    # Deliberation budget: how long the brand can wait and still land content
    # before the peak. Content arriving after the peak competes with the decline.
    slack_to_peak = fit.peak_day - activation_lead_days
    launch_within_hours = max(0.0, slack_to_peak) * 24.0

    if window >= ACT_THRESHOLD_DAYS:
        verdict = Verdict.ACT
    elif window > 0:
        verdict = Verdict.MARGINAL
    else:
        verdict = Verdict.PASS

    confidence = float(
        np.clip(0.30 + 0.45 * fit.r_squared + 0.25 * fit.param_confidence, 0.0, 1.0)
    )

    # How much of the trend's total useful life is still ahead of us.
    elapsed = max(0.0, -fit.peak_day) + 1e-9
    remaining = round(min(100.0, max(0.0, ttl / (ttl + elapsed) * 100.0)), 1) if ttl else 0.0

    return CaptureWindow(
        trend_id=trend.id,
        trend_name=trend.name,
        stage=stage,
        current_momentum=round(fit.current_value, 1),
        peak_momentum=round(fit.peak_value, 1),
        relevance_threshold=round(fit.peak_value * RELEVANCE_FRACTION, 1),
        opportunity_remaining_pct=remaining,
        ttl_days=round(ttl, 1),
        ttl_low_days=round(ttl_low, 1),
        ttl_high_days=round(ttl_high, 1),
        activation_lead_days=round(activation_lead_days, 1),
        capture_window_days=round(window, 1),
        verdict=verdict,
        launch_within_hours=round(launch_within_hours, 0) if launch_within_hours > 0 else None,
        confidence=round(confidence, 2),
        fit_quality=round(fit.r_squared, 3),
        method=fit.decay_regime,
        rationale=_rationale(
            trend, stage, ttl, activation_lead_days, window, verdict, launch_within_hours, fit
        ),
    )


def _rationale(
    trend: Trend,
    stage: LifecycleStage,
    ttl: float,
    lead: float,
    window: float,
    verdict: Verdict,
    launch_hours: float,
    fit: MomentumFit,
) -> str:
    assumed = fit.decay_regime in ("decay_from_prior", "decay_observed_shrunk")
    base = (
        f"{trend.name} is {stage.value}. Momentum stays above the relevance "
        f"threshold for about {ttl:.0f} more days"
        + (
            (
                f" (decay rate assumed from the {trend.category or 'default'} prior, "
                "since the peak has not happened yet)"
                if fit.decay_regime == "decay_from_prior"
                else " (decay rate part-measured, part-assumed — the decline is "
                "too short to read on its own)"
            )
            if assumed
            else " (decay rate measured from the observed decline)"
        )
        + f", and {lead:.0f} days of that is consumed by activation lead time."
    )
    if verdict is Verdict.PASS:
        return base + (
            f" That leaves {window:.0f} days of usable window — the moment passes "
            "before anything could ship, so this is a trap rather than an opportunity."
        )
    if verdict is Verdict.MARGINAL:
        return base + (
            f" That leaves only {window:.0f} days of usable window. Viable solely "
            "with an accelerated approval path."
        )
    if launch_hours:
        return base + (
            f" That leaves {window:.0f} days of usable window, but content should land "
            f"before the peak — commit within {launch_hours:.0f} hours to make it."
        )
    return base + f" That leaves {window:.0f} days of usable window."
