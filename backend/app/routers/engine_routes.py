"""The five-stage loop, exposed over HTTP."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import services
from app.demo import default_brief
from app.engine.listen import ScoutedOpportunity
from app.providers.registry import get_providers
from app.schemas import AskRequest, AskResponse, BriefRequest

router = APIRouter(prefix="/api", tags=["engine"])


def _brief(req: BriefRequest | None):
    return (req.brief if req and req.brief else None) or default_brief()


def _opportunity_payload(o: ScoutedOpportunity, include_series: bool = True) -> dict:
    payload = {
        "trend": o.trend.model_dump(mode="json", exclude={"momentum_series"}),
        "window": o.window.model_dump(mode="json"),
        "creator_supply_index": o.creator_supply_index,
        "creator_supply_note": o.creator_supply_note,
        "strength": o.strength,
    }
    if include_series:
        payload["search_momentum"] = [p.model_dump(mode="json") for p in o.search_momentum]
        payload["platform_momentum"] = [p.model_dump(mode="json") for p in o.platform_momentum]
    return payload


@router.post("/scout")
def scout_trends(req: BriefRequest | None = None):
    """Stage 01 — what is emerging in this niche, and is there still time?"""
    brief = _brief(req)
    opportunities = services.run_scout(brief, limit=req.limit if req else 8)
    return {
        "brief": brief.model_dump(mode="json"),
        "activation_lead_days": services.activation_lead_days(),
        "opportunities": [_opportunity_payload(o) for o in opportunities],
    }


@router.get("/capture/{trend_id}")
def capture(trend_id: str):
    """Stage 02 — the Capture Window for one trend, with its momentum curve."""
    trend = services.find_trend(trend_id)
    if trend is None:
        raise HTTPException(status_code=404, detail=f"unknown trend {trend_id}")
    window, series, projection = services.run_capture(trend)
    return {
        "trend": trend.model_dump(mode="json", exclude={"momentum_series"}),
        "window": window.model_dump(mode="json"),
        "momentum": [p.model_dump(mode="json") for p in series],
        "projection": projection,
    }


@router.post("/creators/score")
def score_creators_route(req: BriefRequest):
    """Stage 03 — the Creator Opportunity Score for every creator in the pool."""
    brief = _brief(req)
    trend = services.find_trend(req.trend_id or "")
    if trend is None:
        raise HTTPException(status_code=404, detail=f"unknown trend {req.trend_id}")
    scores = services.run_match(brief, trend)
    from app.data.loader import seed_creators
    from app.engine.match import top_matching_videos

    creators = {c.id: c for c in seed_creators()}
    return {
        "trend": trend.model_dump(mode="json", exclude={"momentum_series"}),
        "weights_version": services.weights_version(),
        "weights": services.current_weights(),
        "scores": [
            {
                **s.model_dump(mode="json"),
                "archetype": creators[s.creator_id].archetype,
                "handle": creators[s.creator_id].handle,
                "avg_views": creators[s.creator_id].avg_views,
                "thumbnail_url": creators[s.creator_id].thumbnail_url,
                "reach_relevance_delta": s.reach_relevance_delta,
                # What this creator actually makes about this trend. It is the
                # evidence behind the content-fit signal, so it belongs next to
                # the score rather than buried in a tooltip.
                "top_videos": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "views": v.views,
                        "published_at": v.published_at.isoformat(),
                        "duration_seconds": v.duration_seconds,
                        "thumbnail_url": v.thumbnail_url,
                    }
                    for v in top_matching_videos(trend, creators[s.creator_id], limit=3)
                ],
            }
            for s in sorted(scores, key=lambda s: s.rank)
        ],
    }


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Ask Gemini about this campaign or about the world.

    The engine's state and the web-search tool go in together and the model
    decides which it needs — so "why is this creator first?" is answered from
    the scoring and "what's in the news about run clubs?" is searched, through
    one endpoint.
    """
    brief = default_brief()
    try:
        run = services.run_full(brief, trend_id=req.trend_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    context = services.build_ask_context(run)
    answer = get_providers().gemini.ask(req.question, context)
    return AskResponse(
        text=answer.text,
        citations=list(answer.citations),
        searched=answer.searched,
        source=answer.source,
        suggestions=list(answer.suggestions),
    )


@router.post("/portfolio")
def portfolio(req: BriefRequest):
    """Stage 04 — the best mix, against the naive top-ranked baseline."""
    brief = _brief(req)
    trend = services.find_trend(req.trend_id or "")
    if trend is None:
        raise HTTPException(status_code=404, detail=f"unknown trend {req.trend_id}")
    comparison = services.run_portfolio(brief, trend, exclude_flagged=req.exclude_flagged)
    return comparison.model_dump(mode="json")


@router.post("/run")
def run_everything(req: BriefRequest | None = None):
    """The whole loop in one call: scout, predict, match, optimise."""
    brief = _brief(req)
    try:
        result = services.run_full(brief, trend_id=req.trend_id if req else None)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    top = sorted(result.scores, key=lambda s: s.rank)[:10]
    return {
        "brief": brief.model_dump(mode="json"),
        "recommendation": result.recommendation,
        "activation_lead_days": services.activation_lead_days(),
        "opportunities": [_opportunity_payload(o, include_series=False) for o in result.opportunities],
        "chosen": _opportunity_payload(result.chosen),
        "top_creators": [s.model_dump(mode="json") for s in top],
        "portfolio": result.portfolio.model_dump(mode="json"),
    }
