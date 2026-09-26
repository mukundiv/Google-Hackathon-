"""The canonical demo scenario — the deck's hypothetical campaign."""

from __future__ import annotations

from datetime import date

from app.data.loader import seed_brand
from app.models.brief import AudienceSpec, CampaignBrief

DEMO_TODAY = date(2026, 9, 26)


def default_brief() -> CampaignBrief:
    """Athletic apparel brand launching a women's running shoe.

    Audience: women 18-30, US. Budget: $250K. Objective: awareness +
    consideration. Straight from the pitch deck.
    """
    brand = seed_brand()
    return CampaignBrief(
        brand_id=brand.id,
        brand_name=brand.name,
        product="Women's running shoe launch",
        objective="Awareness + consideration",
        audience=AudienceSpec(
            age_min=18,
            age_max=30,
            genders=["female"],
            geos=["US"],
            interests=["running", "fitness", "wellness", "lifestyle"],
        ),
        budget_usd=250_000.0,
        market="US",
        niche=brand.default_niche,
        constraints=list(brand.brand_safety_requirements),
        max_creators=6,
        min_creators=2,
    )
