"""Creator seed generation — imported by generate_seed.py."""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

from _trend_content import AFFINITY, TITLES

TODAY = date(2026, 9, 26)

# Audience segment vocabulary: "<gender>:<age bucket>:<geo>:<interest>"
# Weights per archetype are hand-set so that the portfolio optimiser faces a
# genuine trade-off: the highest-scoring creators share an audience, and
# broadening coverage means accepting slightly lower individual scores.
ARCHETYPES: list[dict] = [
    {
        "key": "run_community",
        "label": "Running Community Creator",
        "n": 5,
        "subs": (180_000, 520_000),
        "vtr": 0.42,
        "cpm": 46.0,
        "positioning": (
            "Documents city run club culture week to week — the people, the routes, "
            "the post-run coffee. Community first, built around showing up rather than "
            "hero worship, and deliberately inclusive of every pace. Kit gets used, "
            "not displayed."
        ),
        "themes": [
            "I joined {city}'s biggest run club",
            "Run club changed how I train",
            "Inside a {city} social running club",
            "Why everyone is joining a run club right now",
            "Run club long run + coffee",
            "Running community meetup in {city}",
            "Tempo session with the run club",
            "First time at a social running club",
            "Run club pace groups explained",
            "Building a running community from scratch",
        ],
        "audience": {
            "female:18-24:US:running": 0.30, "female:25-34:US:running": 0.24,
            "female:18-24:US:fitness": 0.13, "female:25-34:US:fitness": 0.08,
            "male:25-34:US:running": 0.09, "female:18-24:CA:running": 0.05,
            "female:25-34:UK:running": 0.05, "female:18-24:US:lifestyle": 0.06,
        },
        "sentiment": 0.88,
    },
    {
        "key": "fitness_lifestyle",
        "label": "Fitness & Lifestyle Creator",
        "n": 5,
        "subs": (450_000, 950_000),
        "vtr": 0.28,
        "cpm": 52.0,
        "positioning": (
            "Blends training content with daily-life vlogging and product hauls. "
            "Polished and aspirational, broad fitness rather than specialist running, "
            "with a consistent line that performance should be inclusive rather than "
            "intimidating."
        ),
        "themes": [
            "My full week of workouts",
            "Realistic fitness routine as a busy {job}",
            "What I eat in a day + training",
            "Gym haul and activewear try-on",
            "Morning routine before the gym",
            "How I stay consistent with fitness",
            "Trying a running week for the first time",
            "Full body strength session",
            "Fitness reset after a rough month",
            "Activewear that actually holds up",
        ],
        "audience": {
            "female:18-24:US:fitness": 0.28, "female:25-34:US:fitness": 0.19,
            "female:18-24:US:running": 0.16, "female:25-34:US:running": 0.09,
            "female:18-24:US:lifestyle": 0.11, "male:18-24:US:fitness": 0.07,
            "female:18-24:CA:fitness": 0.06, "female:25-34:UK:fitness": 0.04,
        },
        "sentiment": 0.79,
    },
    {
        "key": "celebrity_fitness",
        "label": "Celebrity Fitness Creator",
        "n": 3,
        "subs": (1_500_000, 2_600_000),
        "vtr": 0.34,
        "cpm": 58.0,
        "positioning": (
            "Mass-reach fitness entertainment — challenges, stunts and celebrity "
            "collaborations. Built on spectacle and elite feats; enormous "
            "audience, weak topical ownership, and a tone that trades on being "
            "exceptional rather than accessible."
        ),
        "themes": [
            "I trained like a pro athlete for 30 days",
            "Extreme fitness challenge",
            "{celeb} tries my workout",
            "Marathon in 12 weeks: can I do it",
            "Testing viral fitness trends",
            "The hardest workout on the internet",
            "I tried the {celeb} training plan",
            "Fitness myths debunked",
            "24 hours in the gym",
            "Reacting to fitness fails",
            "Before and after: my 90 day transformation",
        ],
        # Broad and male-leaning, but not a strawman: a brand would not
        # shortlist a creator with no overlap at all, and the interesting
        # result is a plausible candidate losing on fit rather than an
        # obviously wrong one.
        "audience": {
            "male:25-34:US:fitness": 0.16, "male:35-44:US:fitness": 0.11,
            "female:25-34:US:fitness": 0.17, "female:18-24:US:fitness": 0.13,
            "female:25-34:US:running": 0.07, "female:35-44:US:fitness": 0.09,
            "male:18-24:US:sports": 0.08, "male:25-34:CA:fitness": 0.07,
            "female:25-34:UK:fitness": 0.07, "male:35-44:UK:sports": 0.05,
        },
        "sentiment": 0.62,
    },
    {
        "key": "wellness_recovery",
        "label": "Wellness & Recovery Creator",
        "n": 5,
        "subs": (120_000, 480_000),
        "vtr": 0.31,
        "cpm": 42.0,
        "positioning": (
            "Sleep, mobility, stress and recovery for people who train. Calm and "
            "evidence-leaning, inclusive of every level, focused on training being "
            "sustainable rather than performative."
        ),
        "themes": [
            "Recovery routine that actually works",
            "Mobility for runners",
            "How I fixed my sleep",
            "Zone 2 and why easy days matter",
            "Stretching routine after long runs",
            "Rest days without guilt",
            "Breathwork for training stress",
            "Why your recovery is failing",
            "Sunday reset: mobility and mindset",
            "Recovery tools I actually use",
        ],
        "audience": {
            "female:25-34:US:wellness": 0.27, "female:35-44:US:wellness": 0.17,
            "female:25-34:US:fitness": 0.12, "female:25-34:US:running": 0.10,
            "female:18-24:US:wellness": 0.11, "male:25-34:US:wellness": 0.08,
            "female:25-34:CA:wellness": 0.08, "female:35-44:UK:wellness": 0.07,
        },
        "sentiment": 0.86,
    },
    {
        "key": "athleisure_style",
        "label": "Athleisure & Style Creator",
        "n": 5,
        "subs": (150_000, 600_000),
        "vtr": 0.26,
        "cpm": 50.0,
        "positioning": (
            "Sport-adjacent fashion — track club aesthetics, kit styling and "
            "run-to-brunch outfitting. Purchase-intent heavy, training-light."
        ),
        "themes": [
            "Track club fashion is taking over",
            "Styling running kit off the track",
            "Athleisure haul: what's worth it",
            "Retro running kit lookbook",
            "Run to brunch outfit ideas",
            "The best running shoes for style",
            "Sportswear trends this season",
            "How to style shorts and a singlet",
            "Kit that works for running and life",
            "Building an athleisure capsule",
        ],
        "audience": {
            "female:18-24:US:fashion": 0.26, "female:25-34:US:fashion": 0.18,
            "female:18-24:US:lifestyle": 0.16, "female:25-34:US:lifestyle": 0.11,
            "female:18-24:US:running": 0.08, "female:18-24:UK:fashion": 0.09,
            "female:25-34:CA:fashion": 0.07, "male:18-24:US:fashion": 0.05,
        },
        "sentiment": 0.81,
    },
    {
        "key": "marathon_coach",
        "label": "Marathon Coach",
        "n": 5,
        "subs": (90_000, 380_000),
        "vtr": 0.38,
        "cpm": 40.0,
        "positioning": (
            "Structured training guidance for first-time and improving marathoners. "
            "Technical and plan-driven, high trust with committed runners, explicitly "
            "inclusive of back-of-pack athletes and built around gear that gets used."
        ),
        "themes": [
            "Your first marathon training plan",
            "Marathon debut mistakes to avoid",
            "Hybrid training for runners",
            "Strength work for marathon training",
            "How to pace your first marathon",
            "16 week marathon block explained",
            "Long run progression",
            "Fuelling for the marathon",
            "Taper week done right",
            "Run and lift in the same week",
        ],
        "audience": {
            "female:25-34:US:running": 0.20, "male:25-34:US:running": 0.18,
            "female:18-24:US:running": 0.13, "male:35-44:US:running": 0.12,
            "female:35-44:US:running": 0.10, "male:25-34:UK:running": 0.09,
            "female:25-34:CA:running": 0.09, "male:18-24:US:running": 0.09,
        },
        "sentiment": 0.84,
    },
    {
        "key": "run_vlogger",
        "label": "Run Vlogger",
        "n": 5,
        "subs": (60_000, 300_000),
        "vtr": 0.44,
        "cpm": 36.0,
        "positioning": (
            "Personal running diary — training blocks, races and the emotional arc of "
            "a season. Young, female-skewing, very high engagement, and openly about "
            "community over individual performance."
        ),
        "themes": [
            "Marathon training vlog week {n}",
            "Running my first marathon",
            "Race day vlog",
            "Run commute to work",
            "A week of runs with me",
            "Training block diary",
            "Running through a bad week",
            "5am runs for a month",
            "My first sub-2 half",
            "Run club and long run vlog",
        ],
        "audience": {
            "female:18-24:US:running": 0.27, "female:25-34:US:running": 0.19,
            "female:18-24:US:lifestyle": 0.14, "female:18-24:UK:running": 0.10,
            "female:18-24:CA:running": 0.09, "female:25-34:US:wellness": 0.08,
            "male:18-24:US:running": 0.07, "female:18-24:US:fitness": 0.06,
        },
        "sentiment": 0.90,
    },
    {
        "key": "sports_science",
        "label": "Sports Science Creator",
        "n": 4,
        "subs": (200_000, 700_000),
        "vtr": 0.30,
        "cpm": 38.0,
        "positioning": (
            "Research-led breakdowns of training methods and gear. Analytical, "
            "male-skewing, older, high credibility and low trend-chasing."
        ),
        "themes": [
            "What the research says about zone 2",
            "Do super shoes actually work",
            "Hybrid training: the evidence",
            "VO2 max explained properly",
            "Recovery science breakdown",
            "Running economy deep dive",
            "Strength training and endurance",
            "Testing training myths",
            "Heart rate training explained",
            "Lactate threshold in plain English",
        ],
        "audience": {
            "male:25-34:US:sports": 0.21, "male:35-44:US:sports": 0.18,
            "male:25-34:US:running": 0.15, "female:25-34:US:running": 0.11,
            "male:35-44:UK:sports": 0.10, "male:25-34:CA:sports": 0.09,
            "female:35-44:US:sports": 0.08, "male:18-24:US:sports": 0.08,
        },
        "sentiment": 0.77,
    },
    {
        "key": "college_athletics",
        "label": "College Athletics Creator",
        "n": 3,
        "subs": (110_000, 420_000),
        "vtr": 0.36,
        "cpm": 34.0,
        "positioning": (
            "NCAA track and cross-country life. Very young audience, strong team "
            "and track-club culture, limited purchasing power."
        ),
        "themes": [
            "Day in the life of a D1 runner",
            "Track season training week",
            "Cross country camp vlog",
            "College track meet recap",
            "Training with my team",
            "Track club kit reveal",
            "Balancing school and track",
            "Conference championships vlog",
            "Off season base building",
            "What D1 running is really like",
        ],
        "audience": {
            "female:18-24:US:sports": 0.24, "male:18-24:US:sports": 0.20,
            "female:18-24:US:running": 0.18, "male:18-24:US:running": 0.14,
            "female:18-24:US:fashion": 0.08, "female:18-24:CA:sports": 0.06,
            "male:18-24:CA:running": 0.05, "female:25-34:US:running": 0.05,
        },
        "sentiment": 0.85,
    },
]

FIRST = ["Maya", "Lena", "Tasha", "Priya", "Nina", "Adaeze", "Joss", "Rue", "Imani", "Sofia",
         "Kira", "Noor", "Elise", "Talia", "Bex", "Camille", "Dani", "Frankie", "Greta", "Hana",
         "Ines", "Jade", "Kofi", "Liam", "Mateo", "Niko", "Omar", "Pablo", "Quinn", "Rafa",
         "Sami", "Theo", "Uma", "Vera", "Wes", "Xan", "Yara", "Zeke", "Amara", "Beau"]
LAST = ["Okonkwo", "Brooks", "Vance", "Raman", "Holt", "Mensah", "Pike", "Calder", "Osei", "Reyes",
        "Dunn", "Haddad", "Moreau", "Ward", "Nolan", "Fontaine", "Price", "Ellis", "Lund", "Sato",
        "Costa", "Idris", "Boateng", "Shaw", "Alvarez", "Petrov", "Nassar", "Silva", "Marsh", "Ito",
        "Farah", "Bergman", "Clark", "Novak", "Reed", "Kaur", "Diallo", "Lang", "Moss", "Frye"]

CITIES = ["Brooklyn", "Chicago", "Austin", "Seattle", "Denver", "London", "Toronto", "Atlanta"]
JOBS = ["nurse", "teacher", "designer", "analyst", "student"]
CELEBS = ["an Olympian", "a pro sprinter", "an NFL safety", "a UFC fighter"]


def _fill(template: str, r: random.Random, i: int) -> str:
    return (
        template.replace("{city}", r.choice(CITIES))
        .replace("{job}", r.choice(JOBS))
        .replace("{celeb}", r.choice(CELEBS))
        .replace("{n}", str(i % 16 + 1))
    )


def _trend_curves(trends: list[dict]) -> dict[str, list[tuple[date, float]]]:
    """Momentum by day per trend, used to date trend-linked uploads."""
    out = {}
    for t in trends:
        pts = [
            (date.fromisoformat(p["day"]), float(p["value"]))
            for p in t["momentum_series"]
        ]
        out[t["id"]] = pts
    return out


def _sample_trend_date(
    curve: list[tuple[date, float]], r: random.Random
) -> tuple[date, float] | None:
    """Pick an upload date with probability proportional to momentum.

    Creators publish into a trend as it rises, so upload timing has to follow
    the curve rather than be spread evenly. This is what makes platform
    topic-velocity a real measurement over the seeded world.
    """
    live = [(d, v) for d, v in curve if v >= 8.0]
    if not live:
        return None
    total = sum(v for _, v in live)
    pick = r.uniform(0, total)
    acc = 0.0
    for d, v in live:
        acc += v
        if acc >= pick:
            return d, v
    return live[-1]


def _build_videos(
    arch: dict,
    n: int,
    pos: float,
    avg_views: int,
    r: random.Random,
    trend_curves: dict[str, list[tuple[date, float]]],
) -> list[dict]:
    affinity = AFFINITY.get(arch["key"], {})
    videos: list[dict] = []
    total_videos = 18
    n_trend = int(total_videos * 0.45)

    # --- trend-linked uploads -----------------------------------------
    if affinity:
        trend_ids = list(affinity)
        weights = [affinity[t] for t in trend_ids]
        for i in range(n_trend):
            tid = r.choices(trend_ids, weights=weights, k=1)[0]
            curve = trend_curves.get(tid)
            if not curve:
                continue
            sampled = _sample_trend_date(curve, r)
            if sampled is None:
                continue
            day, momentum_now = sampled
            template = r.choice(TITLES.get(tid, ["Talking about {n}"]))
            title = _fill(template, r, i)
            # Content riding a live trend outperforms the creator's baseline.
            momentum_lift = 0.70 + 0.95 * (momentum_now / 100.0)
            views = int(avg_views * momentum_lift * (0.7 + 0.5 * affinity[tid]) * r.uniform(0.7, 1.35))
            videos.append(
                _video(f"{arch['key']}-{n}-t{i}", title, arch, day, views, r, extra_tags=tid)
            )

    # --- evergreen archetype content ----------------------------------
    # Each creator covers a subset of their archetype's themes rather than all
    # of them, so creators of the same type have genuinely different
    # catalogues. Without this, every creator in an archetype was a near-copy
    # and content fit could not separate them.
    themes = r.sample(arch["themes"], k=min(len(arch["themes"]), 7))
    for v in range(total_videos - len(videos)):
        days_ago = int(180 * (v / max(1, total_videos - len(videos))) + r.uniform(0, 8))
        title = _fill(themes[v % len(themes)], r, v)
        recency = 1.0 + 0.35 * math.exp(-days_ago / 70.0) * pos
        views = int(avg_views * recency * r.uniform(0.62, 1.42))
        videos.append(
            _video(f"{arch['key']}-{n}-e{v}", title, arch, TODAY - timedelta(days=days_ago), views, r)
        )
    return videos


def _video(
    vid: str, title: str, arch: dict, day: date, views: int, r: random.Random, extra_tags: str = ""
) -> dict:
    tags = _tags_for(arch["key"], title)
    if extra_tags:
        tags = list(dict.fromkeys(tags + extra_tags.replace("trend-", "").split("-")))[:12]
    return {
        "id": f"vid-{vid}",
        "title": title,
        "description": f"{title}. {arch['positioning'][:110]}",
        "tags": tags,
        "published_at": day.isoformat(),
        "views": max(500, views),
        "likes": int(views * r.uniform(0.035, 0.085)),
        "comments": int(views * r.uniform(0.0025, 0.0075)),
        "duration_seconds": r.choice([420, 610, 780, 940, 1180]),
    }


def build_creators(trends: list[dict]) -> list[dict]:
    """Build the creator pool.

    Trend affinity is expressed through the *content* a creator actually makes:
    creators whose recent uploads use a trend's query terms score highly on
    content fit and, if those uploads are also outperforming their baseline, on
    momentum too. Nothing is scored directly here — this only produces facts.
    """
    r = random.Random(4242)
    trend_curves = _trend_curves(trends)
    creators: list[dict] = []
    name_pool = [(f, l) for f in FIRST for l in LAST]
    r.shuffle(name_pool)
    idx = 0

    for arch in ARCHETYPES:
        for n in range(arch["n"]):
            first, last = name_pool[idx]
            idx += 1
            # The first creator of each archetype sits at the top of its
            # subscriber band, so the hero examples are the strongest of their kind.
            pos = 1.0 - (n / max(1, arch["n"]))
            subs = int(arch["subs"][0] + (arch["subs"][1] - arch["subs"][0]) * pos)
            subs = int(subs * r.uniform(0.94, 1.06))
            vtr = arch["vtr"] * r.uniform(0.9, 1.1)
            avg_views = int(subs * vtr)

            # audience distribution with per-creator jitter, renormalised
            aud = {k: v * r.uniform(0.82, 1.18) for k, v in arch["audience"].items()}
            total = sum(aud.values())
            aud = {k: round(v / total, 4) for k, v in aud.items()}

            videos = _build_videos(arch, n, pos, avg_views, r, trend_curves)
            videos.sort(key=lambda v: v["published_at"], reverse=True)

            pos_rate = min(0.97, arch["sentiment"] * r.uniform(0.96, 1.05))
            creators.append(
                {
                    "id": f"creator-{arch['key']}-{n+1}",
                    "channel_id": f"UC{arch['key'][:6]}{n}{r.randint(10000, 99999)}",
                    "name": f"{first} {last}",
                    "handle": f"@{first.lower()}{last.lower()[:4]}",
                    "archetype": arch["label"],
                    "subscribers": subs,
                    "avg_views": avg_views,
                    "country": "US",
                    "topics": _topics_for(arch["key"]),
                    "positioning": arch["positioning"],
                    "videos": videos,
                    "audience_segments": [{"key": k, "weight": w} for k, w in aud.items()],
                    "audience_provenance": "estimated",
                    "sample_comments": _comments(pos_rate, r),
                    "base_cpm_usd": round(arch["cpm"] * r.uniform(0.92, 1.08), 2),
                    "analytics_connected": False,
                }
            )
    return creators


def _topics_for(key: str) -> list[str]:
    return {
        "run_community": ["running", "run club", "running community", "social running"],
        "fitness_lifestyle": ["fitness", "lifestyle", "activewear", "gym"],
        "celebrity_fitness": ["fitness", "challenges", "entertainment", "transformation"],
        "wellness_recovery": ["wellness", "recovery", "mobility", "sleep", "zone 2"],
        "athleisure_style": ["fashion", "athleisure", "style", "track club"],
        "marathon_coach": ["running", "marathon", "coaching", "hybrid training"],
        "run_vlogger": ["running", "vlog", "marathon training", "run commute"],
        "sports_science": ["sports science", "training", "research", "zone 2"],
        "college_athletics": ["track", "cross country", "college sports", "track club"],
    }[key]


def _tags_for(key: str, title: str) -> list[str]:
    base = _topics_for(key)
    words = [w.strip(",.:").lower() for w in title.split() if len(w) > 4]
    return list(dict.fromkeys(base + words))[:10]


POSITIVE = [
    "this is exactly why I started running",
    "the run club episode got me to finally show up",
    "genuinely the most useful running channel",
    "love how real this feels",
    "bought the shoes you recommended and no regrets",
    "your training block series changed my season",
]
NEUTRAL = ["what shoes are those", "where is this filmed", "what's your weekly mileage"]
NEGATIVE = ["too many ads lately", "this felt like a commercial", "not for beginners at all"]


def _comments(pos_rate: float, r: random.Random) -> list[str]:
    out = []
    for _ in range(12):
        roll = r.random()
        if roll < pos_rate:
            out.append(r.choice(POSITIVE))
        elif roll < pos_rate + (1 - pos_rate) * 0.55:
            out.append(r.choice(NEUTRAL))
        else:
            out.append(r.choice(NEGATIVE))
    return out
