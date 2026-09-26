"""Past campaigns — the Brand Portal ledger that powers the Learning Loop."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class CampaignOutcome(BaseModel):
    reach: int = 0
    views: int = 0
    engagement_rate: float = 0.0
    sentiment_positive_pct: float = 0.0
    consideration_lift_pct: float = 0.0
    performance_index: float = Field(
        default=0.0,
        description="Normalised 0-100 blend of the outcome metrics; the target "
        "variable the learning loop regresses signals against.",
    )


class CreatorResult(BaseModel):
    creator_id: str
    creator_name: str
    predicted_score: float
    actual_performance_index: float
    spend_usd: float

    @property
    def error(self) -> float:
        return self.actual_performance_index - self.predicted_score


class PastCampaign(BaseModel):
    id: str
    brand_id: str
    name: str
    product: str
    trend_name: str
    trend_category: str
    launched_at: date
    objective: str
    audience_summary: str
    spend_usd: float
    activation_lead_days: float
    predicted: CampaignOutcome
    actual: CampaignOutcome
    creator_results: list[CreatorResult] = Field(default_factory=list)
    signal_snapshot: dict[str, float] = Field(
        default_factory=dict,
        description="Mean value of each Opportunity Score signal across the "
        "portfolio, paired with `actual.performance_index` for re-weighting.",
    )
    portfolio_overlap_pct: float = 0.0
    learnings: list[str] = Field(default_factory=list)

    @property
    def prediction_error(self) -> float:
        return self.actual.performance_index - self.predicted.performance_index
