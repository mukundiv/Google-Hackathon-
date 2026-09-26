"""Stage 01 — Listen: the Trend Scout.

Gemini searches the live web for what is emerging in a niche and returns
candidate trends with citations. Those candidates are then quantified against
Google Trends search momentum and YouTube platform velocity, and handed to the
Capture Window predictor.

Discovery and measurement are deliberately separate jobs. The model is good at
noticing that something is happening and terrible at knowing how fast; the
time-series data is the reverse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.engine.predict import capture_window
from app.models.brief import CampaignBrief
from app.models.trend import CaptureWindow, MomentumPoint, Trend
from app.providers.base import GeminiProvider, TrendsProvider, YouTubeProvider

# Window length past which more runway adds nothing to how attractive an
# opportunity is — you only need enough time to ship.
USEFUL_WINDOW_DAYS = 14.0


@dataclass
class ScoutedOpportunity:
    trend: Trend
    window: CaptureWindow
    search_momentum: list[MomentumPoint]
    platform_momentum: list[MomentumPoint]
    creator_supply_index: float
    creator_supply_note: str

    @property
    def strength(self) -> float:
        """How good an opportunity this actually is, 0-100.

        Ranking purely by the longest capture window was wrong: it promoted
        trends that are barely off the ground, because a trend nobody has
        noticed yet has all the runway in the world. A usable opportunity
        needs three things at once — people already searching for it,
        creators already making content about it, and enough window left to
        ship into. Past roughly a fortnight, extra runway stops being worth
        anything.
        """
        momentum_now = self.window.current_momentum
        adequacy = min(1.0, max(0.0, self.window.capture_window_days) / USEFUL_WINDOW_DAYS)
        return round(
            0.40 * momentum_now + 0.30 * self.creator_supply_index + 0.30 * adequacy * 100.0, 1
        )

    @property
    def sort_key(self) -> tuple:
        """Actionable first, then by opportunity strength."""
        rank = {"ACT": 0, "MARGINAL": 1, "PASS": 2}[self.window.verdict.value]
        return (rank, -self.strength)


def audience_summary(brief: CampaignBrief) -> str:
    a = brief.audience
    return (
        f"{'/'.join(a.genders)} aged {a.age_min}-{a.age_max} in {'/'.join(a.geos)}"
        f"{', interested in ' + ', '.join(a.interests) if a.interests else ''}"
    )


def creator_supply(supply: dict) -> tuple[float, str]:
    """How much content creators are currently making about a topic.

    A brand activating through creators needs creators already working in the
    space. High search interest with no creator supply is a different
    situation from high interest with a crowded field, and the brand should
    see which one it is.

    Scored from absolute counts rather than a self-normalised curve: every
    topic is at 100% of its own peak at some point, which tells a planner
    nothing about whether anyone is actually publishing.
    """
    uploads = int(supply.get("uploads", 0))
    channels = int(supply.get("channels", 0))
    change = float(supply.get("change_pct", 0.0))
    window = int(supply.get("window_days", 30))

    # Saturates at heavy coverage: ~120 uploads from ~32 distinct channels in
    # the window. Set high enough that a genuinely busy topic still has
    # headroom above a merely active one.
    volume = min(1.0, uploads / 120.0)
    breadth = min(1.0, channels / 32.0)
    index = round((0.55 * volume + 0.45 * breadth) * 100.0, 1)

    if index >= 65:
        note = "Creators are publishing heavily into this topic — a crowded but proven field."
    elif index >= 35:
        note = "Steady creator coverage: enough existing content to ride, not yet saturated."
    elif index >= 12:
        note = "Thin creator coverage. Early enough to own, but little momentum to borrow."
    else:
        note = (
            "Almost no creator coverage. Search interest is not being served by content — "
            "a first-mover position, and a slower one to activate."
        )
    note += f" {uploads} upload(s) from {channels} channel(s) in the last {window} days"
    if change > 200:
        note += ", more than tripling the previous window."
    elif change > 20:
        note += f", up {change:.0f}% on the previous window."
    elif change < -20:
        note += f", down {abs(change):.0f}% on the previous window."
    else:
        note += ", roughly flat on the previous window."
    return index, note


def scout(
    brief: CampaignBrief,
    activation_lead_days: float,
    gemini: GeminiProvider,
    trends: TrendsProvider,
    youtube: YouTubeProvider,
    limit: int = 6,
    today: date | None = None,
) -> list[ScoutedOpportunity]:
    candidates = gemini.scout_trends(
        niche=brief.niche,
        market=brief.market,
        audience_summary=audience_summary(brief),
        limit=limit,
    )

    out: list[ScoutedOpportunity] = []
    for trend in candidates:
        search = trends.momentum(trend.query_terms, market=brief.market)
        platform = youtube.topic_velocity(trend.query_terms)
        if len(search) < 12:
            # Not enough signal to say anything responsible about timing.
            continue
        # Timing is fitted on search demand alone. Creator supply lags it, and
        # folding a lagged series into the same curve moved every predicted
        # peak later — it is reported alongside instead.
        window = capture_window(trend, search, activation_lead_days, today=today)
        supply, note = creator_supply(youtube.topic_supply(trend.query_terms))
        out.append(
            ScoutedOpportunity(
                trend=trend,
                window=window,
                search_momentum=search,
                platform_momentum=platform,
                creator_supply_index=supply,
                creator_supply_note=note,
            )
        )

    out.sort(key=lambda o: o.sort_key)
    return out
