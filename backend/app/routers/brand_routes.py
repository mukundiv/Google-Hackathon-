"""The Brand Portal — a returning brand's own campaign history and what it
implies for the next campaign."""

from __future__ import annotations

from collections import defaultdict

import numpy as np
from fastapi import APIRouter

from app import services
from app.data.loader import seed_brand, seed_creators
from app.demo import default_brief

router = APIRouter(prefix="/api/brand", tags=["brand"])


@router.get("")
def brand_portal():
    brand = seed_brand()
    campaigns = services.all_campaigns()
    creators = {c.id: c for c in seed_creators()}

    by_archetype: dict[str, list[float]] = defaultdict(list)
    by_category: dict[str, list[float]] = defaultdict(list)
    for c in campaigns:
        by_category[c.trend_category].append(c.actual.performance_index)
        for r in c.creator_results:
            creator = creators.get(r.creator_id)
            if creator:
                by_archetype[creator.archetype].append(r.actual_performance_index)

    overlaps = [c.portfolio_overlap_pct for c in campaigns]
    outcomes = [c.actual.performance_index for c in campaigns]
    overlap_corr = (
        float(np.corrcoef(overlaps, outcomes)[0, 1])
        if len(campaigns) > 2 and np.std(overlaps) > 0
        else 0.0
    )

    leads = [c.activation_lead_days for c in campaigns]
    recent = sorted(campaigns, key=lambda c: c.launched_at)[-4:]

    return {
        "brand": brand.model_dump(mode="json"),
        "campaigns": [c.model_dump(mode="json") for c in campaigns],
        "suggested_brief": default_brief().model_dump(mode="json"),
        "insights": {
            "campaigns_run": len(campaigns),
            "total_spend_usd": round(sum(c.spend_usd for c in campaigns), 2),
            "mean_performance_index": round(float(np.mean(outcomes)), 1),
            "mean_prediction_error": round(
                float(np.mean([abs(c.prediction_error) for c in campaigns])), 2
            ),
            "activation_lead_days": {
                "all_time": round(float(np.mean(leads)), 1),
                "recent": round(float(np.mean([c.activation_lead_days for c in recent])), 1),
                "fastest": min(leads),
                "learned": services.activation_lead_days(),
            },
            "overlap_vs_performance_correlation": round(overlap_corr, 3),
            "overlap_finding": (
                "Campaigns with more duplicated audience have performed worse."
                if overlap_corr < -0.3
                else "No clear link between audience overlap and outcome yet."
            ),
            "best_archetypes": sorted(
                (
                    {"archetype": k, "mean_index": round(float(np.mean(v)), 1), "campaigns": len(v)}
                    for k, v in by_archetype.items()
                ),
                key=lambda d: -d["mean_index"],
            )[:5],
            "best_trend_categories": sorted(
                (
                    {"category": k, "mean_index": round(float(np.mean(v)), 1), "campaigns": len(v)}
                    for k, v in by_category.items()
                ),
                key=lambda d: -d["mean_index"],
            ),
        },
    }
