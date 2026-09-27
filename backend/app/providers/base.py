"""Provider contracts.

Each external signal source in the deck's architecture is defined here as a
Protocol with exactly two implementations: `mock` (deterministic, no
credentials, rich enough to run the whole product) and a live one. Swapping is
a config change, never a code change — see `app/providers/registry.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.models.brief import BrandProfile, CampaignBrief
from app.models.creator import AudienceSegment, Creator
from app.models.trend import MomentumPoint, Trend


@dataclass
class Answer:
    """A reply to a free-form question, with whatever it was grounded in.

    `searched` records whether Gemini actually went to the web for this one,
    so the console can show the citations panel only when there is something
    to show and never imply sourcing that did not happen.
    """

    text: str
    citations: list = field(default_factory=list)
    searched: bool = False
    source: str = "gemini"
    suggestions: list[str] = field(default_factory=list)


@dataclass
class Judgement:
    """A qualitative assessment with its reasoning attached. Gemini returns
    these for the signals that need synthesis rather than arithmetic."""

    score: float
    rationale: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.7
    flag: bool = False
    note: str = ""


@runtime_checkable
class GeminiProvider(Protocol):
    """The deck's INTELLIGENCE column: classify, synthesize, reason, structure."""

    mode: str

    def scout_trends(
        self, niche: str, market: str, audience_summary: str, limit: int = 6
    ) -> list[Trend]:
        """Discover what is emerging in a niche right now, with citations."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts for content-fit similarity."""
        ...

    def assess_brand_fit(self, brand: BrandProfile, creator: Creator) -> Judgement:
        """Brand values and positioning vs creator content and tone.
        Sets `flag` when brand safety needs a human look."""
        ...

    def explain_audience_fit(
        self, brief: CampaignBrief, creator: Creator, computed_score: float
    ) -> str:
        """Narrate an audience-fit score the engine computed from segment data.

        The number itself is arithmetic over audience segments — verified from
        the channel owner's analytics where connected, estimated otherwise — so
        the model explains the result rather than inventing it.
        """
        ...

    def assess_sentiment(self, comments: list[str]) -> Judgement:
        """Share of positive audience sentiment, 0-100."""
        ...

    def write_recommendation(self, context: dict) -> str:
        """The plain-language 'here is what to do' for the decision output."""
        ...

    def ask(self, question: str, context: dict) -> Answer:
        """Answer a free-form question about the market or about this run.

        One call covers both jobs: the engine's current state goes in as
        context and web search is available, so the model answers from the
        recommendation when the question is about the recommendation and
        searches when the question is about the world. Routing it ourselves
        would only get in the way.
        """
        ...


@runtime_checkable
class YouTubeProvider(Protocol):
    """Deck: YOUTUBE DATA API — video + channel signals."""

    mode: str

    def find_creators(self, niche: str, query_terms: list[str], limit: int = 40) -> list[Creator]:
        ...

    def get_creator(self, creator_id: str) -> Creator | None:
        ...

    def topic_velocity(self, query_terms: list[str], days: int = 180) -> list[MomentumPoint]:
        """Publishing velocity for a topic, normalised to its own peak.

        Useful as a shape for charting; not comparable between topics.
        """
        ...

    def topic_supply(self, query_terms: list[str], days: int = 30) -> dict:
        """Absolute creator coverage of a topic in the recent window.

        Returns upload count, distinct channels, total views and the change
        against the previous window. Counts are comparable between topics in
        a way that a self-normalised curve is not.
        """
        ...


@runtime_checkable
class TrendsProvider(Protocol):
    """Deck: GOOGLE TRENDS — cultural momentum."""

    mode: str

    def momentum(self, query_terms: list[str], market: str = "US", days: int = 180) -> list[MomentumPoint]:
        ...


@runtime_checkable
class AnalyticsProvider(Protocol):
    """Deck: YOUTUBE ANALYTICS — campaign + audience performance.

    Only ever returns data for channels whose owner has connected them. For
    everyone else this returns None and the engine falls back to an inferred
    estimate, clearly labelled as such.
    """

    mode: str

    def audience_breakdown(self, channel_id: str) -> list[AudienceSegment] | None:
        ...

    def is_connected(self, channel_id: str) -> bool:
        ...
