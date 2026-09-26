"""Orchestration between the API layer and the engine.

Holds the small amount of state the console needs (current weights, campaigns
observed at runtime) and memoises the expensive steps, since scoring forty
creators against a trend is the slow part and the UI re-asks for it constantly.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app import store
from app.data.loader import seed_brand, seed_campaigns, seed_creators, seed_trends
from app.demo import DEMO_TODAY
from app.engine.learn import learn
from app.engine.listen import ScoutedOpportunity, scout
from app.engine.match import BASELINE_WEIGHTS, ScoringContext, score_creators
from app.engine.optimize import compare_portfolios
from app.engine.predict import capture_window, fit_momentum
from app.models.brief import CampaignBrief
from app.models.campaign import PastCampaign
from app.models.creator import CreatorOpportunityScore
from app.models.learning import LearningState
from app.models.portfolio import PortfolioComparison
from app.models.trend import CaptureWindow, Trend
from app.providers.registry import get_providers

_cache: dict[str, Any] = {}


def clear_cache() -> None:
    _cache.clear()


def _key(*parts: Any) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode()).hexdigest()


def _brief_key(brief: CampaignBrief) -> str:
    return _key(brief.model_dump(mode="json"), weights_signature())


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------
def all_campaigns() -> list[PastCampaign]:
    """Seeded history plus anything fed back during this session."""
    observed = [PastCampaign.model_validate(p) for p in store.list_observed_campaigns()]
    return seed_campaigns() + observed


def learning_state() -> LearningState:
    return learn(all_campaigns(), seed_brand().avg_activation_lead_days)


def current_weights() -> dict[str, float]:
    latest = store.latest_weights()
    return latest.weights if latest else dict(BASELINE_WEIGHTS)


def weights_signature() -> str:
    return _key(current_weights())


def weights_version() -> str:
    latest = store.latest_weights()
    return latest.version if latest else "baseline"


def activation_lead_days() -> float:
    """Learned from the brand's own campaign history."""
    return learning_state().activation_lead_days


def apply_learning() -> LearningState:
    """Adopt the weights the learning loop currently recommends."""
    state = learning_state()
    store.save_weights(
        version=f"{state.current.version}-{datetime.now(timezone.utc):%H%M%S}",
        weights=state.current.weights,
        trained_on=state.campaigns_learned_from,
        method=state.current.method,
        note=state.current.note,
    )
    clear_cache()
    return learning_state()


def reset_learning() -> None:
    store.reset_learning()
    clear_cache()


# --------------------------------------------------------------------------
# pipeline steps
# --------------------------------------------------------------------------
def find_trend(trend_id: str) -> Trend | None:
    return next((t for t in seed_trends() if t.id == trend_id), None)


def run_scout(brief: CampaignBrief, limit: int = 8, today: date | None = None) -> list[ScoutedOpportunity]:
    key = _key("scout", brief.model_dump(mode="json"), limit, str(today))
    if key not in _cache:
        p = get_providers()
        _cache[key] = scout(
            brief, activation_lead_days(), p.gemini, p.trends, p.youtube,
            limit=limit, today=today or DEMO_TODAY,
        )
    return _cache[key]


def run_capture(
    trend: Trend, today: date | None = None
) -> tuple[CaptureWindow, list, list[dict]]:
    """Capture window plus the fitted curve projected forward.

    The chart needs the forecast, not just the history — the whole point is
    what happens *after* today, and a line that stops at the present cannot
    show a window closing.
    """
    p = get_providers()
    anchor = today or DEMO_TODAY
    series = p.trends.momentum(trend.query_terms)
    window = capture_window(trend, series, activation_lead_days(), today=anchor)

    fit = fit_momentum(series, category=trend.category, today=anchor)
    horizon = int(max(30.0, window.ttl_days + 20.0))
    projection = [
        {
            "day": (anchor + timedelta(days=d)).isoformat(),
            "value": round(max(0.0, min(100.0, fit.value_at(float(d)))), 2),
        }
        for d in range(0, horizon + 1)
    ]
    return window, series, projection


def run_match(
    brief: CampaignBrief, trend: Trend, today: date | None = None
) -> list[CreatorOpportunityScore]:
    key = _key("match", _brief_key(brief), trend.id, str(today))
    if key not in _cache:
        p = get_providers()
        ctx = ScoringContext(
            brief=brief,
            brand=seed_brand(),
            trend=trend,
            creators=seed_creators(),
            campaigns=all_campaigns(),
            weights=current_weights(),
            weights_version=weights_version(),
            today=today or DEMO_TODAY,
        )
        _cache[key] = score_creators(ctx, p.gemini, p.analytics)
    return _cache[key]


def run_portfolio(
    brief: CampaignBrief, trend: Trend, exclude_flagged: bool = True, today: date | None = None
) -> PortfolioComparison:
    key = _key("portfolio", _brief_key(brief), trend.id, exclude_flagged, str(today))
    if key not in _cache:
        scores = run_match(brief, trend, today=today)
        _cache[key] = compare_portfolios(
            seed_creators(), scores, brief, exclude_flagged=exclude_flagged
        )
    return _cache[key]


@dataclass
class FullRun:
    brief: CampaignBrief
    opportunities: list[ScoutedOpportunity]
    chosen: ScoutedOpportunity
    scores: list[CreatorOpportunityScore]
    portfolio: PortfolioComparison
    recommendation: str


def run_full(brief: CampaignBrief, trend_id: str | None = None, today: date | None = None) -> FullRun:
    """The whole loop in one call — what the demo's 'run it' button does."""
    opportunities = run_scout(brief, today=today)
    if not opportunities:
        raise ValueError("no trends with enough signal to evaluate")

    chosen = None
    if trend_id:
        chosen = next((o for o in opportunities if o.trend.id == trend_id), None)
    if chosen is None:
        chosen = next((o for o in opportunities if o.window.verdict.value == "ACT"), opportunities[0])

    scores = run_match(brief, chosen.trend, today=today)
    portfolio = run_portfolio(brief, chosen.trend, today=today)
    top = max(scores, key=lambda s: s.composite)

    recommendation = get_providers().gemini.write_recommendation(
        {
            "verdict": chosen.window.verdict.value,
            "trend_name": chosen.trend.name,
            "capture_window_days": chosen.window.capture_window_days,
            "brand_name": brief.brand_name,
            "top_creator": top.creator_name,
            "portfolio_size": len(portfolio.optimized.members),
            "spend": portfolio.optimized.total_cost_usd,
        }
    )
    return FullRun(
        brief=brief,
        opportunities=opportunities,
        chosen=chosen,
        scores=scores,
        portfolio=portfolio,
        recommendation=recommendation,
    )
