"""Deterministic seed-data generator for mock mode.

Mock mode has to be good enough to design the product against, so this builds
a coherent world rather than random noise:

* Momentum curves are solved *backwards* from the narrative properties we want
  (current level, days-to-peak, time-to-live) using the same logistic-rise /
  exponential-decay family the predictor fits. The predictor then re-derives
  those properties from the data alone, so the engine is doing real work even
  on synthetic input.
* Creators are built from archetypes with audience distributions that make the
  portfolio optimiser's coverage/overlap trade-off meaningful.

Run: python scripts/generate_seed.py
"""

from __future__ import annotations

import json
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.engine.momentum_model import (  # noqa: E402
    decay_prior,
    momentum_curve,
    peak_value,
    solve_from_narrative,
)

SEED_DIR = Path(__file__).resolve().parent.parent / "app" / "data" / "seed"
TODAY = date(2026, 9, 26)
HISTORY_DAYS = 180
RELEVANCE_FRACTION = 0.40  # a trend is "still relevant" above 40% of its peak

rng = random.Random(20260926)


# --------------------------------------------------------------------------
# momentum curve — uses the engine's own model so the mock world and the
# predictor agree on what a trend looks like
# --------------------------------------------------------------------------
def series(params: dict) -> list[dict]:
    """Daily observations for the last HISTORY_DAYS, with measurement noise.

    Noise scales with the signal, as real search/velocity measurement does.
    Flat homoscedastic noise was wrong in a way that mattered: for a trend that
    only started rising recently, most of the history sits near zero, and
    clipping the negative half of a fixed-width Gaussian at zero left a
    positive floor across that whole stretch. The fitter read the floor as an
    earlier, shallower onset and pushed every predicted peak several days late.
    """
    out = []
    for i in range(HISTORY_DAYS + 1):
        t = -HISTORY_DAYS + i
        clean = float(momentum_curve(t, params["L"], params["k"], params["t0"], params["tau"]))
        sigma = 0.35 + 0.045 * clean
        observed = max(0.0, min(100.0, clean + rng.gauss(0, sigma)))
        out.append({"day": (TODAY + timedelta(days=t)).isoformat(), "value": round(observed, 2)})
    return out


def derived_ttl(days_to_peak: float, tau: float) -> float:
    """Days until momentum falls to 40% of peak."""
    return days_to_peak + tau * math.log(1.0 / RELEVANCE_FRACTION)


# --------------------------------------------------------------------------
# trends
# --------------------------------------------------------------------------
TREND_SPECS = [
    {
        "id": "trend-social-running-clubs",
        "name": "Social Running Clubs",
        "category": "community_behaviour",
        "description": (
            "Run clubs have shifted from training groups to social infrastructure — "
            "people join to meet people, and the run is the excuse. City-level clubs "
            "are spawning weekly, with post-run coffee as the actual product."
        ),
        "why_now": (
            "Club formation and 'join a run club' intent are both climbing fast and "
            "have not peaked. Content in this space is community-led, so credibility "
            "beats production value — brands can enter without feeling like an ad."
        ),
        "query_terms": ["run club", "social running club", "running community", "run club london"],
        "current": 67, "days_to_peak": 12, "k": 0.085, "seasonal": False,
        "citations": [
            ("Run clubs are the new dating app", "https://www.theguardian.com/lifeandstyle/run-clubs-social", "Guardian", "Attendance at urban run clubs has roughly tripled year on year, with organisers reporting that social motivation now outranks fitness goals."),
            ("The rise of the social run club", "https://www.runnersworld.com/news/social-run-club-boom", "Runner's World", "New club registrations are up sharply, concentrated in the 18-30 bracket and skewing female for the first time."),
            ("Why brands are showing up at run clubs", "https://www.businessoffashion.com/articles/marketing/run-club-brand-activation", "Business of Fashion", "Athletic brands are moving budget from stadium sponsorship toward neighbourhood run club partnerships."),
        ],
    },
    {
        "id": "trend-strava-wrapped",
        "name": "Strava Wrapped",
        "category": "seasonal_product",
        "description": (
            "The annual year-in-review recap moment, where athletes share their "
            "yearly mileage cards across social. Enormous spike, extremely short tail."
        ),
        "why_now": (
            "This one has already peaked. The recap cycle has passed its sharing "
            "window and conversation is decaying quickly — the engine flags it as a "
            "trap rather than an opportunity."
        ),
        "query_terms": ["strava wrapped", "year in sport", "strava recap"],
        "current": 52, "days_to_peak": -9, "k": 0.20, "seasonal": True,
        "citations": [
            ("Strava's Year in Sport lands", "https://www.strava.com/press/year-in-sport", "Strava", "The annual recap drove a record single-day sharing spike before returning to baseline within two weeks."),
            ("Why recap marketing has a two-week shelf life", "https://digiday.com/marketing/recap-season-shelf-life", "Digiday", "Recap formats concentrate nearly all engagement into a 10-day window, making late entry effectively worthless."),
        ],
    },
    {
        "id": "trend-hybrid-training",
        "name": "Hybrid Training",
        "category": "training_method",
        "description": (
            "Runners lifting and lifters running. The single-discipline identity is "
            "dissolving in favour of combined strength-and-endurance programming."
        ),
        "why_now": "Steady, non-seasonal climb with a long runway and no peak in sight yet.",
        "query_terms": ["hybrid training", "run and lift", "hybrid athlete", "strength for runners"],
        "current": 54, "days_to_peak": 26, "k": 0.060, "seasonal": False,
        "citations": [
            ("The hybrid athlete takes over", "https://www.outsideonline.com/health/training/hybrid-athlete-trend", "Outside", "Combined strength-endurance programming is the fastest growing category in coaching apps."),
            ("Runners are finally lifting", "https://www.womenshealthmag.com/fitness/hybrid-training-runners", "Women's Health", "Search interest in strength work for runners has doubled, led by women under 30."),
        ],
    },
    {
        "id": "trend-zone-2-everything",
        "name": "Zone 2 Everything",
        "category": "training_method",
        "description": (
            "Low-intensity aerobic training as a lifestyle identity, spilling out of "
            "endurance sport into general wellness."
        ),
        "why_now": "Very high momentum but essentially at peak — the window to act is nearly closed.",
        "query_terms": ["zone 2", "zone 2 training", "easy runs", "aerobic base"],
        "current": 81, "days_to_peak": 3, "k": 0.100, "seasonal": False,
        "citations": [
            ("Zone 2 is everywhere", "https://www.nytimes.com/well/move/zone-2-training", "New York Times", "The low-intensity training concept has crossed from endurance sport into mainstream wellness advice."),
        ],
    },
    {
        "id": "trend-marathon-debut",
        "name": "Marathon Debut Culture",
        "category": "community_behaviour",
        "description": (
            "First-time marathon documentation as a content genre — the training "
            "block as a serialised story, not a single race-day post."
        ),
        "why_now": "Strong sustained climb tied to the autumn race calendar, with a long tail.",
        "query_terms": ["first marathon", "marathon training vlog", "marathon debut", "couch to marathon"],
        "current": 61, "days_to_peak": 19, "k": 0.068, "seasonal": False,
        "citations": [
            ("Everyone is running their first marathon", "https://www.vogue.com/article/marathon-debut-culture", "Vogue", "Debut marathon entries from women under 30 have risen sharply for a third consecutive year."),
            ("The marathon training vlog boom", "https://www.tubefilter.com/marathon-vlog-genre", "Tubefilter", "Serialised training-block content is outperforming race-day recaps on watch time."),
        ],
    },
    {
        "id": "trend-run-commuting",
        "name": "Run-Commuting",
        "category": "community_behaviour",
        "description": "Replacing the commute with a run, and the gear problem that creates.",
        "why_now": "Early but real — low current momentum with a long runway, worth watching.",
        "query_terms": ["run commute", "running to work", "run commuting gear"],
        "current": 38, "days_to_peak": 34, "k": 0.065, "seasonal": False,
        "citations": [
            ("The run commute is having a moment", "https://www.fastcompany.com/run-commute-trend", "Fast Company", "Run-commuting mentions are climbing steadily in major metros with improving cycling infrastructure."),
        ],
    },
    {
        "id": "trend-track-club-fashion",
        "name": "Track Club Fashion",
        "category": "style",
        "description": "Retro track-club aesthetics moving from sport into everyday wardrobes.",
        "why_now": "Mid-climb style trend with meaningful crossover into apparel purchase intent.",
        "query_terms": ["track club", "track club fashion", "retro running kit", "athleisure track"],
        "current": 47, "days_to_peak": 16, "k": 0.115, "seasonal": False,
        "citations": [
            ("Track club is the new prep", "https://www.gq.com/story/track-club-style", "GQ", "Retro club kit has become a dominant reference across streetwear and athleisure collections."),
        ],
    },
    {
        "id": "trend-silent-walking",
        "name": "Silent Walking",
        "category": "wellness_fad",
        "description": "Walking without headphones as a mindfulness practice.",
        "why_now": "Already collapsed. Included to show the engine rejecting a dead trend.",
        "query_terms": ["silent walking", "walking without headphones"],
        "current": 22, "days_to_peak": -6, "k": 0.180, "seasonal": False,
        "citations": [
            ("Silent walking, explained", "https://www.theatlantic.com/health/silent-walking", "The Atlantic", "The practice spiked on social video before fading almost as quickly as it arrived."),
        ],
    },
]


def build_trends() -> list[dict]:
    trends = []
    for spec in TREND_SPECS:
        tau = decay_prior(spec["category"])
        params = solve_from_narrative(spec["current"], spec["days_to_peak"], spec["k"], tau)
        peak = peak_value(params["L"])
        if peak > 100.5:
            raise RuntimeError(f"{spec['name']}: implied peak {peak:.1f} exceeds the 0-100 index")
        trends.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "description": spec["description"],
                "why_now": spec["why_now"],
                "niche": "women's running and athletic apparel",
                "category": spec["category"],
                "query_terms": spec["query_terms"],
                "seasonal": spec["seasonal"],
                "source": "seed",
                "citations": [
                    {"title": t, "url": u, "publisher": p, "snippet": s_}
                    for (t, u, p, s_) in spec["citations"]
                ],
                "momentum_series": series(params),
                "_truth": {
                    "days_to_peak": spec["days_to_peak"],
                    "ttl_days": round(derived_ttl(spec["days_to_peak"], tau), 2),
                    "peak_value": round(peak, 2),
                    "params": {k: round(v, 4) for k, v in params.items()},
                },
            }
        )
    return trends


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _brand import build_brand_and_campaigns
    from _creators import build_creators

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    trends = build_trends()
    (SEED_DIR / "trends.json").write_text(json.dumps(trends, indent=1))

    creators = build_creators(trends)
    (SEED_DIR / "creators.json").write_text(json.dumps(creators, indent=1))

    brand, campaigns = build_brand_and_campaigns(creators)
    (SEED_DIR / "brand.json").write_text(json.dumps(brand, indent=1))
    (SEED_DIR / "campaigns.json").write_text(json.dumps(campaigns, indent=1))

    print(f"wrote {len(trends)} trends, {len(creators)} creators, {len(campaigns)} campaigns")
    print(f"brand avg activation lead: {brand['avg_activation_lead_days']} days")
    for t in trends:
        tr = t["_truth"]
        print(
            f"  {t['name']:<26} peak in {tr['days_to_peak']:>4}d  "
            f"ttl {tr['ttl_days']:>5}d  peak={tr['peak_value']:>5}  tau={tr['params']['tau']:.0f}"
        )
