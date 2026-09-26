"""Portfolio construction (deck slide 8: 'FROM BEST CREATORS -> BEST CREATOR MIX')."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PortfolioMember(BaseModel):
    creator_id: str
    creator_name: str
    archetype: str
    subscribers: int
    opportunity_score: float
    cost_usd: float
    marginal_coverage: float = Field(
        default=0.0,
        description="Share of the target audience this creator adds that no "
        "earlier member of the portfolio already reaches.",
    )


class Portfolio(BaseModel):
    label: str
    strategy: str
    members: list[PortfolioMember] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    budget_usd: float = 0.0
    avg_opportunity_score: float = 0.0
    coverage_pct: float = Field(default=0.0, description="Union of target-audience segments reached")
    overlap_pct: float = Field(default=0.0, description="Mean pairwise audience overlap")
    gross_reach: int = 0
    deduplicated_reach: int = 0
    objective_value: float = 0.0
    solver: str = ""
    notes: list[str] = Field(default_factory=list)

    @property
    def budget_used_pct(self) -> float:
        return (self.total_cost_usd / self.budget_usd * 100) if self.budget_usd else 0.0


class PortfolioComparison(BaseModel):
    """The deck's side-by-side: naive top-ranked picks vs the optimized mix at
    the same budget."""

    naive: Portfolio
    optimized: Portfolio
    overlap_reduction_pts: float = 0.0
    coverage_gain_pts: float = 0.0
    incremental_reach: int = 0
    verdict: str = ""
