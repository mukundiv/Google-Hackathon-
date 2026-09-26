import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.loader import seed_brand, seed_campaigns, seed_creators, seed_trends, trend_truth  # noqa: E402
from app.demo import DEMO_TODAY, default_brief  # noqa: E402
from app.engine.match import BASELINE_WEIGHTS, ScoringContext, score_creators  # noqa: E402
from app.providers.registry import get_providers  # noqa: E402


@pytest.fixture(scope="session")
def providers():
    return get_providers()


@pytest.fixture(scope="session")
def brief():
    return default_brief()


@pytest.fixture(scope="session")
def brand():
    return seed_brand()


@pytest.fixture(scope="session")
def creators():
    return seed_creators()


@pytest.fixture(scope="session")
def campaigns():
    return seed_campaigns()


@pytest.fixture(scope="session")
def trends():
    return seed_trends()


@pytest.fixture(scope="session")
def truth():
    return trend_truth()


@pytest.fixture(scope="session")
def running_clubs(trends):
    return next(t for t in trends if t.name == "Social Running Clubs")


@pytest.fixture(scope="session")
def scores(providers, brief, brand, running_clubs, creators, campaigns):
    ctx = ScoringContext(
        brief=brief, brand=brand, trend=running_clubs, creators=creators,
        campaigns=campaigns, weights=BASELINE_WEIGHTS, today=DEMO_TODAY,
    )
    return score_creators(ctx, providers.gemini, providers.analytics)
