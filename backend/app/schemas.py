"""Request/response shapes for the HTTP layer."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.brief import CampaignBrief
from app.models.campaign import CampaignOutcome


class BriefRequest(BaseModel):
    brief: CampaignBrief | None = None
    trend_id: str | None = None
    limit: int = Field(default=8, ge=1, le=20)
    exclude_flagged: bool = True


class ObserveRequest(BaseModel):
    """Feed a campaign result back into the engine (ACTIVATE -> OBSERVE)."""

    campaign_id: str | None = None
    name: str
    trend_name: str
    trend_category: str = "community_behaviour"
    spend_usd: float
    activation_lead_days: float = 9.0
    signal_snapshot: dict[str, float]
    predicted: CampaignOutcome
    actual: CampaignOutcome
    portfolio_overlap_pct: float = 0.0
    learnings: list[str] = Field(default_factory=list)


class ProviderState(BaseModel):
    requested: str
    active: str
    live: bool
    detail: str = ""


class HealthResponse(BaseModel):
    status: str
    any_live: bool
    providers: dict[str, ProviderState]
    weights_version: str
    activation_lead_days: float
    campaigns_in_ledger: int
