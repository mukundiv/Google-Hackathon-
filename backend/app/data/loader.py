"""Loads the seeded world into typed models, once per process."""

from __future__ import annotations

import json
from functools import lru_cache

from app.config import SEED_DIR
from app.models.brief import BrandProfile
from app.models.campaign import PastCampaign
from app.models.creator import Creator
from app.models.trend import Trend


def _read(name: str):
    path = SEED_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Seed file {name} is missing. Run `python scripts/generate_seed.py` "
            "from the backend directory."
        )
    return json.loads(path.read_text())


@lru_cache
def seed_trends() -> list[Trend]:
    return [Trend.model_validate(t) for t in _read("trends.json")]


@lru_cache
def seed_creators() -> list[Creator]:
    return [Creator.model_validate(c) for c in _read("creators.json")]


@lru_cache
def seed_brand() -> BrandProfile:
    return BrandProfile.model_validate(_read("brand.json"))


@lru_cache
def seed_campaigns() -> list[PastCampaign]:
    return [PastCampaign.model_validate(c) for c in _read("campaigns.json")]


@lru_cache
def trend_truth() -> dict[str, dict]:
    """Ground-truth curve parameters retained by the generator, used by tests to
    check that the predictor recovers what the generator encoded."""
    return {t["id"]: t.get("_truth", {}) for t in _read("trends.json")}
