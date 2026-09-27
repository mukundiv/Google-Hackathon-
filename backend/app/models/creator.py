"""Creators and the Creator Opportunity Score (deck slides 6 and 7)."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field


class Provenance(StrEnum):
    """How a number was obtained. Surfaced in the UI so a brand always knows
    which figures are earned and which are inferred.

    VERIFIED  - from the channel owner's own YouTube Analytics (OAuth).
    MEASURED  - computed from public YouTube Data API facts.
    ESTIMATED - inferred by Gemini or by a statistical prior.
    """

    VERIFIED = "verified"
    MEASURED = "measured"
    ESTIMATED = "estimated"


class CreatorVideo(BaseModel):
    id: str
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    published_at: date
    views: int = 0
    likes: int = 0
    comments: int = 0
    duration_seconds: int = 0
    thumbnail_url: str | None = None

    def text(self) -> str:
        return " ".join([self.title, self.description, " ".join(self.tags)])


class AudienceSegment(BaseModel):
    """A slice of a creator's audience. `weight` values sum to ~1.0 per creator
    and drive both coverage and overlap in the portfolio optimizer."""

    key: str  # "<gender>:<age bucket>:<geo>:<interest>"
    weight: float = Field(ge=0, le=1)


class Creator(BaseModel):
    id: str
    channel_id: str
    name: str
    handle: str
    archetype: str
    subscribers: int
    avg_views: int
    country: str = "US"
    topics: list[str] = Field(default_factory=list)
    positioning: str = ""
    videos: list[CreatorVideo] = Field(default_factory=list)
    audience_segments: list[AudienceSegment] = Field(default_factory=list)
    audience_provenance: Provenance = Provenance.ESTIMATED
    sample_comments: list[str] = Field(default_factory=list)
    base_cpm_usd: float = 25.0
    analytics_connected: bool = False
    # Real channel art in live mode. Left unset for the seeded creators, who
    # are fictional people — the console draws a generated avatar instead of
    # inventing a photograph of someone who does not exist.
    thumbnail_url: str | None = None

    @property
    def engagement_rate(self) -> float:
        """Likes + comments per view across the sampled catalogue."""
        views = sum(v.views for v in self.videos)
        if not views:
            return 0.0
        interactions = sum(v.likes + v.comments for v in self.videos)
        return interactions / views

    def corpus(self) -> str:
        return " ".join([self.positioning, " ".join(self.topics)] + [v.text() for v in self.videos])

    # A brand partnership is not one video: the standard package is several
    # pieces of content plus usage rights, exclusivity and whitelisting, which
    # is what actually consumes a campaign budget.
    ASSETS_PER_DEAL: ClassVar[int] = 3
    USAGE_RIGHTS_MULTIPLIER: ClassVar[float] = 1.75

    def estimated_cost(self, assets: int | None = None) -> float:
        """CPM-style rate-card estimate for a full partnership package."""
        n = assets if assets is not None else self.ASSETS_PER_DEAL
        base = (self.avg_views / 1000.0) * self.base_cpm_usd * n
        return round(base * self.USAGE_RIGHTS_MULTIPLIER, 2)


class SignalScore(BaseModel):
    """One of the deck's five signals, with the evidence behind it. Decision
    intelligence means every number can be interrogated."""

    name: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float
    provenance: Provenance
    confidence: float = Field(default=0.7, ge=0, le=1)
    rationale: str = ""
    evidence: list[str] = Field(default_factory=list)

    @property
    def contribution(self) -> float:
        return self.score * self.weight


class CreatorOpportunityScore(BaseModel):
    creator_id: str
    creator_name: str
    trend_id: str
    composite: float = Field(ge=0, le=100)
    signals: list[SignalScore] = Field(default_factory=list)
    sentiment_positive_pct: float | None = None
    brand_safety_flag: bool = False
    brand_safety_note: str = ""
    subscribers: int = 0
    estimated_cost_usd: float = 0.0
    rank: int = 0
    rank_by_reach: int = 0
    tier: str = ""
    headline: str = ""
    weights_version: str = "baseline"

    @property
    def reach_relevance_delta(self) -> int:
        """Positive means the creator ranks better on opportunity than on reach
        alone - the deck's 'REACH != RELEVANCE' point, quantified."""
        return self.rank_by_reach - self.rank
