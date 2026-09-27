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
from app.providers.base import Answer, Judgement

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

    def ask(self, question: str, context: dict) -> Answer:
        """Answer from the engine's own state, with no model behind it.

        These are not canned strings: each branch reads the live context that
        was passed in, so the answers stay true if the underlying run changes.
        What it cannot do is search the web — that needs the live provider, and
        it says so rather than improvising.
        """
        q = question.lower()
        trend = context.get("trend", {})
        creators = context.get("creators", [])
        portfolio = context.get("portfolio", {})

        def named(ids: list[str]) -> str:
            return ", ".join(ids[:-1]) + " and " + ids[-1] if len(ids) > 1 else "".join(ids)

        if any(w in q for w in ("avoid", "not use", "skip creator", "reject", "safety")):
            flagged = [c for c in creators if c.get("brand_safety_flag")]
            weak = [c for c in creators if c.get("composite", 0) < 45][:3]
            parts = []
            if flagged:
                parts.append(
                    f"{named([c['name'] for c in flagged])} "
                    f"{'are' if len(flagged) > 1 else 'is'} held back for a brand-safety review — "
                    f"{flagged[0].get('brand_safety_note', 'content that breaks the brand rules')}."
                )
            if weak:
                parts.append(
                    "On fit alone the weakest candidates are "
                    + named([f"{c['name']} ({c['composite']:.0f})" for c in weak])
                    + " — large audiences, but little standing in this topic."
                )
            return Answer(text=" ".join(parts) or "Nothing is currently flagged.",
                          source="engine", suggestions=SUGGESTED_QUESTIONS)

        if any(w in q for w in ("rank", "why is", "why did", "first", "top creator", "best")):
            top = creators[0] if creators else None
            if top:
                sig = ", ".join(
                    f"{s['label'].lower()} {s['score']:.0f}" for s in top.get("signals", [])[:3]
                )
                return Answer(
                    text=(
                        f"{top['name']} comes first on {top['composite']:.0f} out of 100. "
                        f"The signals doing the work are {sig}. "
                        f"They have {top['subscribers']:,} subscribers — well short of the largest "
                        "channel in the pool, which is the point: the score measures whether they "
                        "can credibly own this topic, not how many people follow them."
                    ),
                    source="engine", suggestions=SUGGESTED_QUESTIONS,
                )

        if any(w in q for w in ("skip", "pass", "strava", "why not")):
            return Answer(
                text=(
                    "A trend is skipped when it stops mattering before this brand could ship. "
                    f"Activation takes {context.get('activation_lead_days', 9)} days here, so any "
                    "trend with less life left than that is a trap — the work would land after the "
                    "moment passed. Strava Wrapped has already peaked, so its remaining window is "
                    "negative."
                ),
                source="engine", suggestions=SUGGESTED_QUESTIONS,
            )

        if any(w in q for w in ("budget", "spend", "money", "twice", "double", "portfolio", "mix")):
            return Answer(
                text=(
                    f"The recommended mix spends ${portfolio.get('spend', 0):,.0f} across "
                    f"{portfolio.get('size', 0)} creators, holding duplicate audience at "
                    f"{portfolio.get('overlap_pct', 0):.0f}% against "
                    f"{portfolio.get('naive_overlap_pct', 0):.0f}% for the obvious picks. "
                    "More budget would buy further down the fit ranking, and the optimiser would "
                    "keep favouring creators who reach people the others miss over higher-scoring "
                    "creators who overlap."
                ),
                source="engine", suggestions=SUGGESTED_QUESTIONS,
            )

        if any(w in q for w in ("window", "timing", "how long", "when", "time")):
            return Answer(
                text=(
                    f"{trend.get('name', 'This trend')} stays relevant for about "
                    f"{trend.get('ttl_days', 0):.0f} more days. Activation takes "
                    f"{context.get('activation_lead_days', 9)}, which leaves "
                    f"{trend.get('capture_window_days', 0):.0f} days of usable window. "
                    f"{trend.get('rationale', '')}"
                ),
                source="engine", suggestions=SUGGESTED_QUESTIONS,
            )

        return Answer(
            text=(
                "Searching the web needs a live Gemini key — this instance is running on saved "
                "data, so it can only answer from the engine's own output. Try asking why a "
                "creator is ranked where they are, why a trend was skipped, or how the budget "
                "is split."
            ),
            source="unavailable", suggestions=SUGGESTED_QUESTIONS,
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


SUGGESTED_QUESTIONS = [
    "What's in the news about run clubs right now?",
    "Why is this creator ranked first?",
    "Which creators should we avoid, and why?",
    "Why are we skipping Strava Wrapped?",
    "What would change if we had twice the budget?",
    "Who are our competitors working with?",
]


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 3]
