"""The Learning Loop: observe results, re-weight, reset."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from app import services, store
from app.schemas import ObserveRequest

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("")
def state():
    st = services.learning_state()
    applied = services.weights_version()
    # Applying stamps the version with a time suffix (v9 -> v9-223818), so a
    # straight equality check reported "a newer weighting is available"
    # forever, including immediately after adopting it. Compare the base.
    pending = applied.split("-", 1)[0] != st.current.version
    return {
        **st.model_dump(mode="json"),
        "applied_weights": services.current_weights(),
        "applied_version": applied,
        "pending_change": pending,
    }


@router.post("/observe")
def observe(req: ObserveRequest):
    """Feed a campaign result back in — the OBSERVE half of the loop."""
    campaign_id = req.campaign_id or f"observed-{date.today().isoformat()}-{req.name[:16]}"
    payload = {
        "id": campaign_id,
        "brand_id": "brand-momentum-athletics",
        "name": req.name,
        "product": req.name,
        "trend_name": req.trend_name,
        "trend_category": req.trend_category,
        "launched_at": date.today().isoformat(),
        "objective": "Awareness + consideration",
        "audience_summary": "Women 18-30, US",
        "spend_usd": req.spend_usd,
        "activation_lead_days": req.activation_lead_days,
        "predicted": req.predicted.model_dump(mode="json"),
        "actual": req.actual.model_dump(mode="json"),
        "creator_results": [],
        "signal_snapshot": req.signal_snapshot,
        "portfolio_overlap_pct": req.portfolio_overlap_pct,
        "learnings": req.learnings,
    }
    store.add_observed_campaign(campaign_id, payload)
    services.clear_cache()
    return {"ok": True, "campaign_id": campaign_id, "state": state()}


@router.post("/apply")
def apply():
    """Adopt the recommended weights for future scoring."""
    st = services.apply_learning()
    return {"ok": True, "state": {**st.model_dump(mode="json"),
                                  "applied_weights": services.current_weights(),
                                  "applied_version": services.weights_version()}}


@router.post("/reset")
def reset():
    services.reset_learning()
    return {"ok": True, "state": state()}
