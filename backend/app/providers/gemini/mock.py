"""Deterministic stand-in for Gemini.

Nothing here pretends to be a language model. Each method is an explicit,
inspectable heuristic that produces the same *shape* of output the live
provider does, so the engine and the console are identical in both modes.
"""

from __future__ import annotations

import re

from sklearn.feature_extraction.text import TfidfVectorizer

from app.data.loader import seed_trends
from app.models.brief import BrandProfile, CampaignBrief
from app.models.creator import Creator
from app.models.trend import Trend
from app.providers.base import Judgement

POSITIVE_MARKERS = {
    "love", "great", "best", "amazing", "useful", "helpful", "exactly", "changed",
    "genuinely", "finally", "no regrets", "favourite", "favorite", "thank",
}
NEGATIVE_MARKERS = {
    "ads", "commercial", "boring", "not for", "disappointing", "shill", "sellout", "worse",
}
SAFETY_MARKERS = {
    "deficit": "restrictive-diet framing",
    "transformation": "before/after body framing",
    "supplement": "unlicensed supplement promotion",
    "detox": "detox claims",
}


class MockGeminiProvider:
    mode = "mock"

    # -- listen ---------------------------------------------------------
    def scout_trends(
        self, niche: str, market: str, audience_summary: str, limit: int = 6
    ) -> list[Trend]:
        """Return the seeded trend set, ranked by term overlap with the niche."""
        niche_terms = set(_words(niche))
        scored: list[tuple[float, Trend]] = []
        for trend in seed_trends():
            hay = set(_words(f"{trend.name} {trend.description} {trend.niche} {trend.category}"))
            overlap = len(niche_terms & hay) / (len(niche_terms) or 1)
            recency = trend.values()[-1] / 100.0 if trend.values() else 0.0
            scored.append((overlap * 0.6 + recency * 0.4, trend))
        scored.sort(key=lambda p: p[0], reverse=True)
        return [t for _, t in scored[:limit]]

    # -- embeddings -----------------------------------------------------
    def embed(self, texts: list[str]) -> list[list[float]]:
        """TF-IDF vectors over the supplied batch.

        Fitting on the batch is the right call here: callers always pass the
        trend description together with the creator corpora being compared, so
        the vocabulary and the IDF weighting are scoped to that comparison.
        """
        if not texts:
            return []
        vec = TfidfVectorizer(
            stop_words="english", max_features=4096, ngram_range=(1, 2), sublinear_tf=True
        )
        matrix = vec.fit_transform(texts)
        return matrix.toarray().tolist()

    # -- reasoning ------------------------------------------------------
    def assess_brand_fit(self, brand: BrandProfile, creator: Creator) -> Judgement:
        corpus = creator.corpus().lower()
        value_terms = {w for v in brand.values for w in _words(v)}
        hits = sorted({t for t in value_terms if t in corpus})
        alignment = min(1.0, len(hits) / max(3.0, len(value_terms) * 0.45))

        flags = [note for marker, note in SAFETY_MARKERS.items() if marker in corpus]
        base = 40 + alignment * 52
        if flags:
            base -= 16

        evidence = [f"shared language: {', '.join(hits[:5])}"] if hits else []
        evidence.append(f"positioning: {creator.positioning[:110]}")
        if flags:
            evidence.append(f"safety review: {'; '.join(flags)}")

        return Judgement(
            score=round(max(0.0, min(100.0, base)), 1),
            rationale=(
                f"Creator's positioning overlaps {len(hits)} of the brand's stated values"
                + (f"; flagged for {flags[0]}" if flags else "; no brand-safety concerns detected")
            ),
            evidence=evidence,
            confidence=0.62,
            flag=bool(flags),
            note="; ".join(flags),
        )

    def explain_audience_fit(
        self, brief: CampaignBrief, creator: Creator, computed_score: float
    ) -> str:
        band = "strong" if computed_score >= 75 else "partial" if computed_score >= 50 else "weak"
        return (
            f"{band.capitalize()} match: {computed_score:.0f}% of this creator's audience "
            f"sits inside {brief.audience.genders[0]} {brief.audience.age_min}-"
            f"{brief.audience.age_max} in {'/'.join(brief.audience.geos)}."
        )

    def assess_sentiment(self, comments: list[str]) -> Judgement:
        if not comments:
            return Judgement(score=50.0, rationale="No comments sampled.", confidence=0.2)
        pos = neg = 0
        for c in comments:
            low = c.lower()
            if any(m in low for m in POSITIVE_MARKERS):
                pos += 1
            elif any(m in low for m in NEGATIVE_MARKERS):
                neg += 1
        # Share of *all* sampled comments that read positive. Dividing by only
        # the polarised ones let any creator with no detractors score 100,
        # which made the signal useless for ranking.
        pct = (pos / len(comments) * 100) if comments else 50.0
        neutral = len(comments) - pos - neg
        return Judgement(
            score=round(pct, 1),
            rationale=(
                f"{pos} positive, {neg} negative and {neutral} neutral "
                f"of {len(comments)} sampled comments."
            ),
            evidence=comments[:3],
            confidence=0.55,
        )

    def write_recommendation(self, context: dict) -> str:
        verdict = context.get("verdict", "ACT")
        trend = context.get("trend_name", "this opportunity")
        window = context.get("capture_window_days", 0)
        top = context.get("top_creator", "the lead creator")
        count = context.get("portfolio_size", 0)
        spend = context.get("spend", 0)
        if verdict == "PASS":
            return (
                f"Do not activate against {trend}. The opportunity closes before "
                f"{context.get('brand_name', 'this brand')} can realistically ship — "
                f"the capture window is {window:.0f} days, which is less than the "
                f"activation lead time. Redirect the budget to a live opportunity."
            )
        return (
            f"Activate against {trend}. The capture window is {window:.0f} days, so "
            f"there is room to produce and land content while the trend still matters. "
            f"Lead with {top} and build a {count}-creator portfolio at "
            f"${spend:,.0f}, chosen to cover the target audience without paying "
            f"twice for the same viewers."
        )


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 3]
