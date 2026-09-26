"""Brand profile and campaign-history seed.

The ledger is synthetic but not arbitrary: outcomes are generated from a
*different* weighting than the engine's baseline. Content fit and momentum
actually drive results harder than the baseline assumes, while brand fit and
proven performance matter less. The learning loop has to discover that from
the data, and the console shows the weights moving toward it.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

TODAY = date(2026, 9, 26)

BASELINE_WEIGHTS = {
    "content_fit": 0.28,
    "audience_fit": 0.22,
    "brand_fit": 0.16,
    "momentum": 0.19,
    "proven_performance": 0.15,
}

# The relationship the ledger actually encodes.
TRUE_WEIGHTS = {
    "content_fit": 0.34,
    "audience_fit": 0.24,
    "brand_fit": 0.10,
    "momentum": 0.24,
    "proven_performance": 0.08,
}

BRAND = {
    "id": "brand-momentum-athletics",
    "name": "Momentum Athletics",
    "industry": "Athletic apparel and footwear",
    "values": [
        "community over hero worship",
        "performance without elitism",
        "inclusive by default",
        "built to be used, not displayed",
    ],
    "positioning": (
        "Technical running product for people who came to running through other "
        "people. We sponsor the group run, not the podium."
    ),
    "default_niche": "women's running and athletic apparel",
    "brand_safety_requirements": [
        "no extreme-deficit or restrictive-diet content",
        "no unlicensed supplement promotion",
        "no body-transformation before/after framing",
    ],
}

CAMPAIGN_SPECS = [
    ("camp-2024-trail-capsule", "Trail Capsule Launch", "Trail Capsule",
     "Trail Running Resurgence", "community_behaviour", 430, 11.0, 185_000,
     {"content_fit": 78, "audience_fit": 72, "brand_fit": 81, "momentum": 64, "proven_performance": 70},
     0.31, ["Trail audience converted well but skewed older than target.",
            "Long lead time meant we launched after the seasonal peak."]),
    ("camp-2024-city-half", "City Half Marathon Push", "Tempo Racer",
     "Half Marathon Boom", "community_behaviour", 372, 9.5, 210_000,
     {"content_fit": 84, "audience_fit": 79, "brand_fit": 77, "momentum": 76, "proven_performance": 66},
     0.24, ["Race-adjacent content outperformed studio content by a wide margin.",
            "Mid-tier creators beat the one large creator on cost per engaged view."]),
    ("camp-2025-winter-layer", "Winter Layer System", "Thermal Layer",
     "Cold Weather Running", "seasonal_product", 298, 12.0, 160_000,
     {"content_fit": 66, "audience_fit": 68, "brand_fit": 88, "momentum": 52, "proven_performance": 74},
     0.38, ["Strong brand fit did not rescue weak topical momentum.",
            "Overlap was too high — three creators reached the same audience."]),
    ("camp-2025-track-club", "Track Club Collection", "Club Kit",
     "Track Club Fashion", "style", 455, 8.0, 240_000,
     {"content_fit": 88, "audience_fit": 83, "brand_fit": 74, "momentum": 86, "proven_performance": 62},
     0.19, ["Style-led creators drove the highest consideration lift to date.",
            "Momentum was the signal that best predicted which creators overdelivered."]),
    ("camp-2025-recovery-line", "Recovery Line", "Recovery Range",
     "Recovery Culture", "wellness", 341, 9.5, 175_000,
     {"content_fit": 74, "audience_fit": 86, "brand_fit": 84, "momentum": 61, "proven_performance": 80},
     0.22, ["Audience fit carried this one; the product was niche but well targeted.",
            "Creators with prior results underdelivered relative to their scores."]),
    ("camp-2026-spring-tempo", "Spring Tempo Drop", "Tempo 2",
     "Speed Work Content", "training_method", 388, 7.0, 225_000,
     {"content_fit": 86, "audience_fit": 77, "brand_fit": 72, "momentum": 82, "proven_performance": 58},
     0.21, ["Fastest activation we have run, and it showed in the results.",
            "Creators new to us outperformed repeat partners."]),
    ("camp-2026-run-club-pilot", "Run Club Pilot", "Club Singlet",
     "Social Running Clubs", "community_behaviour", 218, 6.0, 95_000,
     {"content_fit": 92, "audience_fit": 88, "brand_fit": 86, "momentum": 90, "proven_performance": 55},
     0.17, ["Small budget, best efficiency of any campaign in the ledger.",
            "Community creators with no prior brand history were the top performers."]),
    ("camp-2026-summer-singlet", "Summer Singlet", "Featherweight Singlet",
     "Hot Weather Training", "seasonal_product", 262, 9.0, 150_000,
     {"content_fit": 70, "audience_fit": 71, "brand_fit": 79, "momentum": 58, "proven_performance": 77},
     0.29, ["Launched two weeks after the heat wave broke — timing cost us.",
            "Confirms that momentum at launch matters more than creator size."]),
]


def _index(signals: dict[str, float], weights: dict[str, float]) -> float:
    return sum(signals[k] * weights[k] for k in weights)


def build_brand_and_campaigns(creators: list[dict]) -> tuple[dict, list[dict]]:
    r = random.Random(777)
    campaigns = []
    pool = [c for c in creators]

    for i, (cid, name, product, trend_name, category, days_ago_x10,
            lead, spend, signals, overlap, learnings) in enumerate(CAMPAIGN_SPECS):
        predicted_index = round(_index(signals, BASELINE_WEIGHTS), 2)
        actual_index = round(min(100.0, max(0.0, _index(signals, TRUE_WEIGHTS) + r.gauss(0, 2.4))), 2)

        launched = TODAY - timedelta(days=days_ago_x10)
        scale = spend / 1000.0
        predicted = {
            "reach": int(scale * 9_400),
            "views": int(scale * 14_800),
            "engagement_rate": round(0.045 + predicted_index / 4000, 4),
            "sentiment_positive_pct": round(72 + predicted_index / 12, 1),
            "consideration_lift_pct": round(predicted_index / 14, 2),
            "performance_index": predicted_index,
        }
        ratio = actual_index / predicted_index if predicted_index else 1.0
        actual = {
            "reach": int(scale * 9_400 * ratio * r.uniform(0.94, 1.07)),
            "views": int(scale * 14_800 * ratio * r.uniform(0.93, 1.09)),
            "engagement_rate": round((0.045 + actual_index / 4000) * r.uniform(0.95, 1.06), 4),
            "sentiment_positive_pct": round(72 + actual_index / 12, 1),
            "consideration_lift_pct": round(actual_index / 14, 2),
            "performance_index": actual_index,
        }

        members = [pool[(i * 4 + j) % len(pool)] for j in range(r.randint(3, 5))]
        per_spend = spend * 1000 / len(members)
        creator_results = []
        for m in members:
            pred = round(min(98.0, max(40.0, _index(signals, BASELINE_WEIGHTS) + r.gauss(0, 6))), 1)
            act = round(min(99.0, max(35.0, _index(signals, TRUE_WEIGHTS) + r.gauss(0, 7))), 1)
            creator_results.append(
                {
                    "creator_id": m["id"],
                    "creator_name": m["name"],
                    "predicted_score": pred,
                    "actual_performance_index": act,
                    "spend_usd": round(per_spend, 2),
                }
            )

        campaigns.append(
            {
                "id": cid,
                "brand_id": BRAND["id"],
                "name": name,
                "product": product,
                "trend_name": trend_name,
                "trend_category": category,
                "launched_at": launched.isoformat(),
                "objective": "Awareness + consideration",
                "audience_summary": "Women 18-30, US",
                "spend_usd": spend * 1000.0,
                "activation_lead_days": lead,
                "predicted": predicted,
                "actual": actual,
                "creator_results": creator_results,
                "signal_snapshot": signals,
                "portfolio_overlap_pct": round(overlap * 100, 1),
                "learnings": learnings,
            }
        )

    campaigns.sort(key=lambda c: c["launched_at"])
    leads = [c["activation_lead_days"] for c in campaigns]
    brand = dict(BRAND)
    brand["avg_activation_lead_days"] = round(sum(leads) / len(leads), 1)
    brand["fastest_activation_lead_days"] = min(leads)
    return brand, campaigns
