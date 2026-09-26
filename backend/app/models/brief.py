"""The brand's inputs — objectives, budget, constraints (deck: 'BRAND INPUTS')."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AudienceSpec(BaseModel):
    """Target audience for a campaign, expressed in the same segment vocabulary
    the portfolio optimizer uses for coverage and overlap."""

    age_min: int = 18
    age_max: int = 30
    genders: list[str] = Field(default_factory=lambda: ["female"])
    geos: list[str] = Field(default_factory=lambda: ["US"])
    interests: list[str] = Field(default_factory=list)

    def segment_keys(self) -> list[str]:
        """Expand the spec into the discrete segments used for coverage maths."""
        buckets = [b for b in ("18-24", "25-34", "35-44") if self._overlaps(b)]
        keys: list[str] = []
        for gender in self.genders:
            for geo in self.geos:
                for bucket in buckets:
                    for interest in self.interests or ["general"]:
                        keys.append(f"{gender}:{bucket}:{geo}:{interest}")
        return keys

    def _overlaps(self, bucket: str) -> bool:
        low, high = (int(x) for x in bucket.split("-"))
        return not (self.age_max < low or self.age_min > high)


class BrandProfile(BaseModel):
    """A returning brand. `avg_activation_lead_days` is learned from the brand's
    own campaign history and feeds directly into the Capture Window."""

    id: str
    name: str
    industry: str
    values: list[str] = Field(default_factory=list)
    positioning: str = ""
    avg_activation_lead_days: float = 9.0
    fastest_activation_lead_days: float = 6.0
    default_niche: str = ""
    brand_safety_requirements: list[str] = Field(default_factory=list)


class CampaignBrief(BaseModel):
    brand_id: str
    brand_name: str
    product: str
    objective: str
    audience: AudienceSpec
    budget_usd: float
    market: str = "US"
    niche: str = ""
    constraints: list[str] = Field(default_factory=list)
    max_creators: int = 6
    min_creators: int = 2
