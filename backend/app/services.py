"""Orchestration between the API layer and the engine.

Holds the small amount of state the console needs (current weights, campaigns
observed at runtime) and memoises the expensive steps, since scoring forty
creators against a trend is the slow part and the UI re-asks for it constantly.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app import store
from app.data.loader import seed_brand, seed_campaigns, seed_creators, seed_trends
from app.demo import DEMO_TODAY
from app.engine.learn import learn
from app.engine.listen import ScoutedOpportunity, scout
from app.engine.match import BASELINE_WEIGHTS, ScoringContext, score_creators
from app.engine.optimize import build_audience_space, compare_portfolios, overlap_matrix
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


def excluded_top_picks(
    brief: CampaignBrief,
    trend: Trend,
    comparison: PortfolioComparison,
    scores: list[CreatorOpportunityScore],
    top_n: int = 5,
) -> list[dict]:
    """Highly ranked creators the optimiser did not buy, and why.

    Dropping the best-fit creator is the whole argument of this stage, but on
    screen it just looked like they disappeared. Each one comes back with the
    two numbers that actually decided it: what share of the budget they wanted,
    and how much of their audience the chosen mix already reaches.
    """
    chosen_ids = {m.creator_id for m in comparison.optimized.members}
    ranked = sorted(scores, key=lambda s: s.rank)[:top_n]
    missing = [s for s in ranked if s.creator_id not in chosen_ids]
    if not missing:
        return []

    creators = seed_creators()
    index = {c.id: i for i, c in enumerate(creators)}
    space = build_audience_space(creators, brief)
    duplication = overlap_matrix(space)
    chosen_idx = [index[cid] for cid in chosen_ids if cid in index]

    out = []
    for s in missing:
        i = index.get(s.creator_id)
        overlap = (
            float(np.mean([duplication[i, k] for k in chosen_idx])) * 100.0
            if i is not None and chosen_idx
            else 0.0
        )
        budget_share = (
            s.estimated_cost_usd / brief.budget_usd * 100.0 if brief.budget_usd else 0.0
        )
        if budget_share >= 20 and overlap >= 25:
            reason = (
                f"wanted {budget_share:.0f}% of the budget, and {overlap:.0f}% of their "
                "audience is already reached by the creators in the mix"
            )
        elif budget_share >= 20:
            reason = (
                f"wanted {budget_share:.0f}% of the budget — that money buys more new "
                "people elsewhere"
            )
        elif overlap >= 25:
            reason = (
                f"{overlap:.0f}% of their audience is already reached by the creators in "
                "the mix"
            )
        else:
            reason = "the same money reached more new people spread across other creators"

        out.append(
            {
                "creator_id": s.creator_id,
                "creator_name": s.creator_name,
                "rank": s.rank,
                "composite": s.composite,
                "cost_usd": s.estimated_cost_usd,
                "budget_share_pct": round(budget_share, 1),
                "overlap_with_mix_pct": round(overlap, 1),
                "reason": reason,
            }
        )
    return out


def build_ask_context(run: "FullRun") -> dict:
    """A compact picture of this run, small enough to sit in a prompt.

    Deliberately trimmed: the full run carries forty scored creators with every
    signal's evidence, which would crowd out the question itself.
    """
    chosen = run.chosen
    ranked = sorted(run.scores, key=lambda s: s.rank)[:6]
    return {
        "brand": run.brief.brand_name,
        "product": run.brief.product,
        "audience": (
            f"{'/'.join(run.brief.audience.genders)} {run.brief.audience.age_min}-"
            f"{run.brief.audience.age_max} in {'/'.join(run.brief.audience.geos)}"
        ),
        "budget_usd": run.brief.budget_usd,
        "activation_lead_days": chosen.window.activation_lead_days,
        "trend": {
            "name": chosen.trend.name,
            "what_it_is": chosen.trend.description,
            "verdict": chosen.window.verdict.value,
            "stage": chosen.window.stage.value,
            "ttl_days": chosen.window.ttl_days,
            "capture_window_days": chosen.window.capture_window_days,
            "rationale": chosen.window.rationale,
            "creator_supply": chosen.creator_supply_note,
        },
        "rejected_trends": [
            {"name": o.trend.name, "verdict": o.window.verdict.value,
             "window_days": o.window.capture_window_days}
            for o in run.opportunities
            if o.window.verdict.value == "PASS"
        ],
        "creators": [
            {
                "name": s.creator_name,
                "composite": s.composite,
                "rank": s.rank,
                "rank_by_reach": s.rank_by_reach,
                "subscribers": s.subscribers,
                "cost_usd": s.estimated_cost_usd,
                "brand_safety_flag": s.brand_safety_flag,
                "brand_safety_note": s.brand_safety_note,
                "signals": [
                    {"label": sig.label, "score": sig.score, "why": sig.rationale}
                    for sig in s.signals
                ],
            }
            for s in ranked
        ],
        "portfolio": {
            "size": len(run.portfolio.optimized.members),
            "spend": run.portfolio.optimized.total_cost_usd,
            "members": [m.creator_name for m in run.portfolio.optimized.members],
            "overlap_pct": run.portfolio.optimized.overlap_pct,
            "naive_overlap_pct": run.portfolio.naive.overlap_pct,
            "coverage_pct": run.portfolio.optimized.coverage_pct,
            "people_reached": run.portfolio.optimized.deduplicated_reach,
        },
        "recommendation": run.recommendation,
    }


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
