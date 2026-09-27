"""Stage 03 — Match: the Creator Opportunity Score.

The deck's five signals, scored 0-100 each and combined under a weighting the
learning loop can revise:

    Content Fit         does this creator already make content about this?
    Audience Fit        is their audience the one the brief is buying?
    Brand Fit           do the brand's values and theirs survive contact?
    Momentum            is their trend-adjacent content outperforming their own baseline?
    Proven Performance  what happened last time this brand worked with them?

Every signal carries its own provenance and evidence. A number a brand cannot
interrogate is not decision intelligence, it is a horoscope.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from app.models.brief import BrandProfile, CampaignBrief
from app.models.campaign import PastCampaign
from app.models.creator import (
    Creator,
    CreatorOpportunityScore,
    CreatorVideo,
    Provenance,
    SignalScore,
)
from app.models.trend import Trend
from app.providers.base import AnalyticsProvider, GeminiProvider

BASELINE_WEIGHTS: dict[str, float] = {
    "content_fit": 0.28,
    "audience_fit": 0.22,
    "brand_fit": 0.16,
    "momentum": 0.19,
    "proven_performance": 0.15,
}

SIGNAL_LABELS = {
    "content_fit": "Content Fit",
    "audience_fit": "Audience Fit",
    "brand_fit": "Brand Fit",
    "momentum": "Momentum",
    "proven_performance": "Proven Performance",
}

# A creator with this share of their audience inside the target segments is
# treated as a complete audience match.
AUDIENCE_SATURATION = 0.85
MOMENTUM_WINDOW_DAYS = 90

# Similarity at or above which a catalogue is treated as a complete topical
# match, used as a floor so a weak pool cannot manufacture a perfect score.
ABSOLUTE_STRONG_SIMILARITY = 0.10
# Both fit signals are compressed rather than linear; see the notes at each use.
CONTENT_FIT_EXPONENT = 0.55
AUDIENCE_FIT_EXPONENT = 0.75


@dataclass
class ScoringContext:
    brief: CampaignBrief
    brand: BrandProfile
    trend: Trend
    creators: list[Creator]
    campaigns: list[PastCampaign]
    weights: dict[str, float]
    weights_version: str = "baseline"
    today: date | None = None


# --------------------------------------------------------------------------
# individual signals
# --------------------------------------------------------------------------
def content_fit_scores(
    trend: Trend, creators: list[Creator], gemini: GeminiProvider
) -> dict[str, tuple[float, float]]:
    """Semantic similarity between the trend and each creator's catalogue.

    Returns creator_id -> (score 0-100, raw cosine similarity).
    """
    trend_text = " ".join(
        [trend.name, trend.description, trend.why_now, " ".join(trend.query_terms)]
    )
    texts = [trend_text] + [c.corpus() for c in creators]
    vectors = np.array(gemini.embed(texts), dtype=float)

    trend_vec = vectors[0]
    creator_vecs = vectors[1:]
    norms = np.linalg.norm(creator_vecs, axis=1) * (np.linalg.norm(trend_vec) or 1.0)
    sims = (creator_vecs @ trend_vec) / np.where(norms == 0, 1.0, norms)

    # Scale against the strong end of this pool rather than the single best
    # creator, so one outlier cannot compress everyone else — but never below
    # an absolute reference, or a pool with no good match would still crown a
    # "perfect" one.
    reference = max(float(np.percentile(sims, 92)), ABSOLUTE_STRONG_SIMILARITY)
    ratio = np.clip(sims / reference, 0.0, 1.0)
    # Compressive: cosine similarity between short trend text and a long
    # creator catalogue falls away steeply, and a linear map turned a creator
    # with real adjacent content into a near-zero. The exponent keeps the
    # ordering and restores a usable gradient across the middle of the pool.
    scaled = np.power(ratio, CONTENT_FIT_EXPONENT) * 100.0

    return {c.id: (float(scaled[i]), float(sims[i])) for i, c in enumerate(creators)}


def audience_fit_score(
    brief: CampaignBrief, creator: Creator, analytics: AnalyticsProvider
) -> tuple[float, Provenance, float, list[str]]:
    """Share of the creator's audience that sits inside the brief's target.

    Uses the channel owner's verified analytics when the channel is connected
    and an inferred estimate otherwise. The two are never silently mixed — the
    provenance travels with the number.
    """
    target = set(brief.audience.segment_keys())

    verified = analytics.audience_breakdown(creator.channel_id)
    if verified is not None:
        segments, provenance = verified, Provenance.VERIFIED
    else:
        segments, provenance = creator.audience_segments, Provenance.ESTIMATED

    in_target = sum(s.weight for s in segments if s.key in target)
    ratio = min(1.0, in_target / AUDIENCE_SATURATION)
    score = (ratio**AUDIENCE_FIT_EXPONENT) * 100.0

    top = sorted(segments, key=lambda s: s.weight, reverse=True)[:3]
    evidence = [f"{s.key} {s.weight * 100:.0f}%" for s in top]
    if provenance is Provenance.VERIFIED:
        evidence.append("source: channel owner's YouTube Analytics")
    else:
        evidence.append("source: inferred from public signals — not owner-verified")

    return score, provenance, in_target, evidence


def momentum_score(
    trend: Trend, creator: Creator, today: date | None = None
) -> tuple[float, str, list[str]]:
    """Is this creator's trend-adjacent content outperforming their own baseline?

    Measured against the creator's own average rather than against other
    creators, so a small channel breaking out reads as momentum and a large
    channel coasting does not.
    """
    anchor = today or max((v.published_at for v in creator.videos), default=date.today())
    cutoff = anchor - timedelta(days=MOMENTUM_WINDOW_DAYS)
    terms = [t.lower() for t in trend.query_terms]

    adjacent = [
        v for v in creator.videos if any(t in v.text().lower() for t in terms)
    ]
    recent_adjacent = [v for v in adjacent if v.published_at >= cutoff]

    if not adjacent:
        return (
            12.0,
            "No content covering this trend — the creator has no standing in it.",
            [f"0 of {len(creator.videos)} sampled videos mention the trend's terms"],
        )

    baseline = creator.avg_views or 1
    if recent_adjacent:
        lift = float(np.mean([v.views for v in recent_adjacent])) / baseline
        cadence = len(recent_adjacent)
    else:
        lift = float(np.mean([v.views for v in adjacent])) / baseline
        cadence = 0

    lift_component = float(np.clip((lift - 0.6) / 0.9, 0.0, 1.0))
    cadence_component = float(np.clip(cadence / 4.0, 0.0, 1.0))
    score = 100.0 * (0.6 * lift_component + 0.4 * cadence_component)

    evidence = [
        f"{len(recent_adjacent)} trend-adjacent uploads in the last {MOMENTUM_WINDOW_DAYS} days",
        f"those videos average {lift:.2f}x this creator's own baseline views",
    ]
    if cadence == 0:
        evidence.append("no recent coverage — momentum is historical only")
    return score, f"Trend-adjacent content is running at {lift:.2f}x baseline.", evidence


def proven_performance_score(
    creator: Creator, campaigns: list[PastCampaign], pool: list[Creator]
) -> tuple[float, Provenance, str, list[str]]:
    """What happened last time, if there was a last time."""
    results = [
        r
        for c in campaigns
        for r in c.creator_results
        if r.creator_id == creator.id
    ]
    if results:
        mean_actual = float(np.mean([r.actual_performance_index for r in results]))
        mean_pred = float(np.mean([r.predicted_score for r in results]))
        delta = mean_actual - mean_pred
        evidence = [
            f"{len(results)} prior campaign(s) with this brand",
            f"average delivered index {mean_actual:.0f} against {mean_pred:.0f} predicted",
            f"{'over' if delta >= 0 else 'under'}-delivered by {abs(delta):.0f} points",
        ]
        return (
            float(np.clip(mean_actual, 0, 100)),
            Provenance.MEASURED,
            f"Worked with this brand {len(results)} time(s); delivered an index of {mean_actual:.0f}.",
            evidence,
        )

    # No history: fall back to a prior from engagement rate percentile.
    rates = np.array([c.engagement_rate for c in pool])
    pct = float((rates < creator.engagement_rate).mean()) if len(rates) else 0.5
    score = 35.0 + pct * 40.0  # deliberately compressed — this is a guess, not a record
    return (
        score,
        Provenance.ESTIMATED,
        "No campaign history with this brand; scored from an engagement-rate prior.",
        [
            f"engagement rate {creator.engagement_rate * 100:.1f}% "
            f"({pct * 100:.0f}th percentile of the pool)",
            "no prior campaign record — this signal is a prior, not a measurement",
        ],
    )


# --------------------------------------------------------------------------
# composite
# --------------------------------------------------------------------------
def score_creators(
    ctx: ScoringContext, gemini: GeminiProvider, analytics: AnalyticsProvider
) -> list[CreatorOpportunityScore]:
    weights = {**BASELINE_WEIGHTS, **(ctx.weights or {})}
    total_w = sum(weights.values()) or 1.0
    weights = {k: v / total_w for k, v in weights.items()}

    content = content_fit_scores(ctx.trend, ctx.creators, gemini)
    results: list[CreatorOpportunityScore] = []

    for creator in ctx.creators:
        c_score, c_sim = content[creator.id]
        a_score, a_prov, a_mass, a_evidence = audience_fit_score(ctx.brief, creator, analytics)
        b = gemini.assess_brand_fit(ctx.brand, creator)
        m_score, m_rationale, m_evidence = momentum_score(ctx.trend, creator, ctx.today)
        p_score, p_prov, p_rationale, p_evidence = proven_performance_score(
            creator, ctx.campaigns, ctx.creators
        )
        sentiment = gemini.assess_sentiment(creator.sample_comments)

        signals = [
            SignalScore(
                name="content_fit",
                label=SIGNAL_LABELS["content_fit"],
                score=round(c_score, 1),
                weight=weights["content_fit"],
                provenance=Provenance.MEASURED,
                confidence=0.8,
                rationale=(
                    f"Catalogue similarity to this trend is {c_sim:.3f}, "
                    f"{'well above' if c_score > 75 else 'around' if c_score > 45 else 'below'} "
                    "the level of the strongest creators in the pool."
                ),
                evidence=_top_matching_videos(ctx.trend, creator),
            ),
            SignalScore(
                name="audience_fit",
                label=SIGNAL_LABELS["audience_fit"],
                score=round(a_score, 1),
                weight=weights["audience_fit"],
                provenance=a_prov,
                confidence=0.9 if a_prov is Provenance.VERIFIED else 0.55,
                rationale=gemini.explain_audience_fit(ctx.brief, creator, a_mass * 100),
                evidence=a_evidence,
            ),
            SignalScore(
                name="brand_fit",
                label=SIGNAL_LABELS["brand_fit"],
                score=round(b.score, 1),
                weight=weights["brand_fit"],
                provenance=Provenance.ESTIMATED,
                confidence=b.confidence,
                rationale=b.rationale,
                evidence=b.evidence,
            ),
            SignalScore(
                name="momentum",
                label=SIGNAL_LABELS["momentum"],
                score=round(m_score, 1),
                weight=weights["momentum"],
                provenance=Provenance.MEASURED,
                confidence=0.75,
                rationale=m_rationale,
                evidence=m_evidence,
            ),
            SignalScore(
                name="proven_performance",
                label=SIGNAL_LABELS["proven_performance"],
                score=round(p_score, 1),
                weight=weights["proven_performance"],
                provenance=p_prov,
                confidence=0.85 if p_prov is Provenance.MEASURED else 0.4,
                rationale=p_rationale,
                evidence=p_evidence,
            ),
        ]

        composite = sum(s.score * s.weight for s in signals)
        results.append(
            CreatorOpportunityScore(
                creator_id=creator.id,
                creator_name=creator.name,
                trend_id=ctx.trend.id,
                composite=round(float(np.clip(composite, 0, 100)), 1),
                signals=signals,
                sentiment_positive_pct=round(sentiment.score, 1),
                brand_safety_flag=b.flag,
                brand_safety_note=b.note,
                subscribers=creator.subscribers,
                estimated_cost_usd=creator.estimated_cost(),
                weights_version=ctx.weights_version,
            )
        )

    _rank(results)
    return results


def _rank(scores: list[CreatorOpportunityScore]) -> None:
    """Assign opportunity rank and reach rank, and label the gap between them."""
    for i, s in enumerate(sorted(scores, key=lambda x: x.composite, reverse=True), start=1):
        s.rank = i
    for i, s in enumerate(sorted(scores, key=lambda x: x.subscribers, reverse=True), start=1):
        s.rank_by_reach = i

    for s in scores:
        if s.composite >= 85:
            s.tier = "Strongest fit"
        elif s.composite >= 72:
            s.tier = "Strong fit"
        elif s.composite >= 55:
            s.tier = "Considered"
        else:
            s.tier = "Weak fit"

        delta = s.reach_relevance_delta
        if delta >= 6:
            s.headline = f"Punches above its size — {delta} places better on fit than on reach."
        elif delta <= -6:
            s.headline = f"Reach ≠ relevance — {abs(delta)} places worse on fit than on reach."
        else:
            s.headline = s.tier


def top_matching_videos(trend: Trend, creator: Creator, limit: int = 3) -> list[CreatorVideo]:
    """This creator's best-performing videos that actually mention the trend.

    Shared with the API layer, which shows them to the brand as the evidence
    behind the content-fit score. Falls back to their most-watched videos when
    nothing matches, so the panel is never empty — a creator with no coverage
    of the trend is exactly the case a brand wants to see for themselves.
    """
    terms = [t.lower() for t in trend.query_terms]
    hits = [v for v in creator.videos if any(t in v.text().lower() for t in terms)]
    if not hits:
        hits = list(creator.videos)
    return sorted(hits, key=lambda v: v.views, reverse=True)[:limit]


def _top_matching_videos(trend: Trend, creator: Creator, limit: int = 3) -> list[str]:
    terms = [t.lower() for t in trend.query_terms]
    if not any(any(t in v.text().lower() for t in terms) for v in creator.videos):
        return ["no videos in the sampled catalogue mention this trend"]
    return [
        f'"{v.title}" — {v.views:,} views ({v.published_at})'
        for v in top_matching_videos(trend, creator, limit)
    ]
