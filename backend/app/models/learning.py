"""Learning Loop state (deck slide 9: PREDICT -> ACTIVATE -> OBSERVE -> LEARN)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SignalWeights(BaseModel):
    version: str
    created_at: datetime
    weights: dict[str, float]
    trained_on_campaigns: int = 0
    method: str = "baseline"
    note: str = ""

    def normalised(self) -> dict[str, float]:
        total = sum(self.weights.values()) or 1.0
        return {k: v / total for k, v in self.weights.items()}


class CalibrationEntry(BaseModel):
    signal: str
    label: str
    mean_abs_error: float
    bias: float = Field(description="Positive means the signal under-predicted outcomes")
    correlation_with_outcome: float
    samples: int
    weight_before: float
    weight_after: float

    @property
    def weight_delta(self) -> float:
        return self.weight_after - self.weight_before


class LearningState(BaseModel):
    current: SignalWeights
    history: list[SignalWeights] = Field(default_factory=list)
    calibration: list[CalibrationEntry] = Field(default_factory=list)
    prediction_error_trend: list[dict] = Field(default_factory=list)
    activation_lead_days: float = 9.0
    campaigns_learned_from: int = 0
    summary: str = ""
