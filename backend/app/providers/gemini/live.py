"""Gemini, live.

Four jobs, matching the deck's INTELLIGENCE column:

    classify    which cultural themes are emerging in this niche
    synthesize  pull signals across sources into one view
    reason      brand fit, audience fit, sentiment
    structure   decision-ready JSON rather than prose

Trend scouting uses Grounding with Google Search, so the model searches the
live web and returns `groundingMetadata` with real citations. Displaying those
citations is a condition of using the tool, so they are carried all the way
through to the trend cards rather than dropped at the API boundary.

Every call is cached and falls back to the mock provider on error: a hackathon
demo must not die because a quota ran out mid-sentence.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import Settings
from app.models.brief import BrandProfile, CampaignBrief
from app.models.creator import Creator
from app.models.trend import LifecycleStage, Trend, TrendCitation
from app.providers.base import Judgement
from app.providers.gemini.mock import MockGeminiProvider
from app.store import cache_get, cache_get_stale, cache_set

log = logging.getLogger(__name__)

TREND_SCHEMA = {
    "type": "object",
    "properties": {
        "trends": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "why_now": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "community_behaviour",
                            "training_method",
                            "style",
                            "seasonal_product",
                            "wellness_fad",
                        ],
                    },
                    "stage": {
                        "type": "string",
                        "enum": ["emerging", "accelerating", "peaking", "declining"],
                    },
                    "query_terms": {"type": "array", "items": {"type": "string"}},
                    "seasonal": {"type": "boolean"},
                },
                "required": ["name", "description", "why_now", "category", "query_terms"],
            },
        }
    },
    "required": ["trends"],
}

JUDGEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "rationale": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "flag": {"type": "boolean"},
        "note": {"type": "string"},
    },
    "required": ["score", "rationale"],
}


class LiveGeminiProvider:
    mode = "live"

    def __init__(self, settings: Settings):
        from google import genai  # imported lazily so mock mode needs no SDK

        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self._fallback = MockGeminiProvider()

    # -- listen ---------------------------------------------------------
    def scout_trends(
        self, niche: str, market: str, audience_summary: str, limit: int = 6
    ) -> list[Trend]:
        key = f"gemini:scout:{niche}:{market}:{audience_summary}:{limit}"
        cached = cache_get(key)
        if cached is not None:
            return [Trend.model_validate(t) for t in cached]

        prompt = (
            f"You are a cultural strategist for brands. Search the web for what is "
            f"genuinely emerging RIGHT NOW in this niche: {niche}.\n"
            f"Market: {market}. Target audience: {audience_summary}.\n\n"
            f"Return the {limit} most significant trends. For each, give a short name, "
            "a two-sentence description of what is actually happening, why it matters "
            "for a brand right now, the lifecycle stage, and 3-5 search terms people "
            "would actually type. Prefer specific behavioural shifts over broad "
            "categories: 'social running clubs' is useful, 'fitness' is not. "
            "Exclude anything that has clearly already peaked unless it is a recurring "
            "seasonal moment, in which case mark it seasonal."
        )

        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.settings.gemini_grounded_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.4,
                ),
            )
            payload = _extract_json(response.text or "")
            citations = _citations_from(response)
            trends = _to_trends(payload, niche, citations)
            if not trends:
                raise ValueError("model returned no usable trends")
            cache_set(key, [t.model_dump(mode="json") for t in trends])
            return trends
        except Exception:
            log.warning("live trend scouting failed; falling back", exc_info=True)
            stale = cache_get_stale(key)
            if stale is not None:
                return [Trend.model_validate(t) for t in stale]
            return self._fallback.scout_trends(niche, market, audience_summary, limit)

    # -- embeddings -----------------------------------------------------
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        key = f"gemini:embed:{self.settings.gemini_embedding_model}:{hash(tuple(texts))}"
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            # Catalogue text is long; truncating keeps the request inside limits
            # without losing the topical signal, which is front-loaded.
            trimmed = [t[:8000] for t in texts]
            result = self.client.models.embed_content(
                model=self.settings.gemini_embedding_model, contents=trimmed
            )
            vectors = [list(e.values) for e in result.embeddings]
            cache_set(key, vectors)
            return vectors
        except Exception:
            log.warning("live embedding failed; falling back to local vectors", exc_info=True)
            return self._fallback.embed(texts)

    # -- reasoning ------------------------------------------------------
    def assess_brand_fit(self, brand: BrandProfile, creator: Creator) -> Judgement:
        prompt = (
            f"Brand: {brand.name} ({brand.industry}).\n"
            f"Positioning: {brand.positioning}\n"
            f"Values: {'; '.join(brand.values)}\n"
            f"Brand safety requirements: {'; '.join(brand.brand_safety_requirements)}\n\n"
            f"Creator: {creator.name} ({creator.archetype}).\n"
            f"Positioning: {creator.positioning}\n"
            f"Recent video titles: {'; '.join(v.title for v in creator.videos[:12])}\n\n"
            "Score 0-100 for how well this creator's values, tone and content fit this "
            "brand. Set flag=true and explain in note if any content would breach the "
            "brand safety requirements. Be strict: a large audience is not brand fit."
        )
        return self._judge(f"brandfit:{brand.id}:{creator.id}", prompt, 0.65,
                           lambda: self._fallback.assess_brand_fit(brand, creator))

    def explain_audience_fit(
        self, brief: CampaignBrief, creator: Creator, computed_score: float
    ) -> str:
        # The number is arithmetic over audience segments, so there is nothing
        # for a model to add beyond phrasing — and a model call per creator here
        # would cost far more than the sentence is worth.
        return self._fallback.explain_audience_fit(brief, creator, computed_score)

    def assess_sentiment(self, comments: list[str]) -> Judgement:
        if not comments:
            return Judgement(score=50.0, rationale="No comments sampled.", confidence=0.2)
        joined = "\n".join(f"- {c}" for c in comments[:40])
        prompt = (
            "Classify the sentiment of these audience comments toward the creator.\n"
            f"{joined}\n\n"
            "Return score = the percentage of comments that read positive (0-100). "
            "Count neutral questions as neutral, not positive."
        )
        return self._judge(f"sentiment:{hash(tuple(comments))}", prompt, 0.7,
                           lambda: self._fallback.assess_sentiment(comments))

    def write_recommendation(self, context: dict) -> str:
        key = f"gemini:rec:{hash(json.dumps(context, sort_keys=True, default=str))}"
        cached = cache_get(key)
        if cached is not None:
            return cached
        prompt = (
            "Write the recommendation a creator-marketing lead would act on. "
            "Three sentences at most, no preamble, no bullet points. State the "
            "decision, the timing and the mix.\n\n"
            f"{json.dumps(context, indent=2, default=str)}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.settings.gemini_model, contents=prompt
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("empty recommendation")
            cache_set(key, text)
            return text
        except Exception:
            log.warning("live recommendation failed; falling back", exc_info=True)
            return self._fallback.write_recommendation(context)

    # -- shared ---------------------------------------------------------
    def _judge(self, cache_key: str, prompt: str, confidence: float, fallback) -> Judgement:
        key = f"gemini:{cache_key}"
        cached = cache_get(key)
        if cached is not None:
            return Judgement(**cached)
        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=JUDGEMENT_SCHEMA,
                    temperature=0.2,
                ),
            )
            data = _extract_json(response.text or "")
            judgement = Judgement(
                score=float(max(0.0, min(100.0, float(data.get("score", 50))))),
                rationale=str(data.get("rationale", "")),
                evidence=[str(e) for e in data.get("evidence", [])][:5],
                confidence=float(data.get("confidence", confidence)),
                flag=bool(data.get("flag", False)),
                note=str(data.get("note", "")),
            )
            cache_set(key, judgement.__dict__)
            return judgement
        except Exception:
            log.warning("live judgement failed (%s); falling back", cache_key, exc_info=True)
            return fallback()


# --------------------------------------------------------------------------
# response parsing
# --------------------------------------------------------------------------
def _extract_json(text: str) -> dict[str, Any]:
    """Grounded responses come back as prose around the JSON, because the
    search tool and a response schema cannot both be set on one call."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _citations_from(response: Any) -> list[TrendCitation]:
    """Pull the grounding sources out of the response.

    Google's terms require these to be displayed alongside any grounded claim,
    so a trend that arrives without them is shown without a sources panel
    rather than silently presented as if unsourced.
    """
    citations: list[TrendCitation] = []
    try:
        for candidate in response.candidates or []:
            metadata = getattr(candidate, "grounding_metadata", None)
            for chunk in getattr(metadata, "grounding_chunks", None) or []:
                web = getattr(chunk, "web", None)
                if web and getattr(web, "uri", None):
                    citations.append(
                        TrendCitation(
                            title=getattr(web, "title", "") or web.uri,
                            url=web.uri,
                            publisher=getattr(web, "domain", "") or "",
                            snippet="",
                        )
                    )
    except Exception:  # pragma: no cover - metadata shape varies by model
        log.debug("could not read grounding metadata", exc_info=True)
    # de-duplicate, keeping order
    seen, unique = set(), []
    for c in citations:
        if c.url not in seen:
            seen.add(c.url)
            unique.append(c)
    return unique


def _to_trends(payload: dict, niche: str, citations: list[TrendCitation]) -> list[Trend]:
    out: list[Trend] = []
    for i, item in enumerate(payload.get("trends", [])):
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        stage = str(item.get("stage", "")).lower()
        out.append(
            Trend(
                id=f"trend-live-{_slug(name)}",
                name=name,
                description=str(item.get("description", "")),
                why_now=str(item.get("why_now", "")),
                niche=niche,
                category=str(item.get("category", "community_behaviour")),
                query_terms=[str(t) for t in item.get("query_terms", [])][:6] or [name],
                citations=citations[i * 2 : i * 2 + 3] or citations[:2],
                momentum_series=[],
                source="gemini_grounded",
                seasonal=bool(item.get("seasonal", False))
                or stage == LifecycleStage.DECLINING.value,
            )
        )
    return out


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-")[:48]
