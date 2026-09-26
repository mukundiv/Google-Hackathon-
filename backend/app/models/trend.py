"""Trends, momentum and the Capture Window (deck slides 4 and 5)."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class LifecycleStage(StrEnum):
    """The deck's culture curve: EMERGES -> ACCELERATES -> PEAKS -> DECLINES."""

    EMERGING = "emerging"
    ACCELERATING = "accelerating"
    PEAKING = "peaking"
    DECLINING = "declining"


class Verdict(StrEnum):
    ACT = "ACT"
    MARGINAL = "MARGINAL"
    PASS = "PASS"


class TrendCitation(BaseModel):
    """A grounding source. Google's Search-grounding terms require these to be
    displayed, so every trend card renders them."""

    title: str
    url: str
    snippet: str = ""
    publisher: str = ""


class MomentumPoint(BaseModel):
    day: date
    value: float = Field(ge=0, le=100)


class Trend(BaseModel):
    id: str
    name: str
    description: str
    why_now: str = ""
    niche: str = ""
    category: str = ""
    query_terms: list[str] = Field(default_factory=list)
    citations: list[TrendCitation] = Field(default_factory=list)
    momentum_series: list[MomentumPoint] = Field(default_factory=list)
    source: str = "seed"
    seasonal: bool = False

    def values(self) -> list[float]:
        return [p.value for p in self.momentum_series]


class CaptureWindow(BaseModel):
    """Capture Window = time-to-live - activation lead time.

    The deck's central claim made arithmetic: a trend is only actionable if it
    outlives the brand's own Identify -> Launch chain.
    """

    trend_id: str
    trend_name: str
    stage: LifecycleStage
    current_momentum: float
    peak_momentum: float
    relevance_threshold: float
    opportunity_remaining_pct: float

    ttl_days: float
    ttl_low_days: float
    ttl_high_days: float

    activation_lead_days: float
    capture_window_days: float
    verdict: Verdict
    launch_within_hours: float | None = None
    confidence: float = Field(ge=0, le=1)
    fit_quality: float = Field(default=0.0, description="R^2 of the momentum fit")
    method: str = "logistic_decay"
    rationale: str = ""
