"""How much each archetype covers each trend, and what that content looks like.

Without this the seeded world was degenerate: every creator posted only their
own archetype's themes, so catalogues either matched a trend almost perfectly
or not at all, and content fit came out bimodal (100 or 12, nothing between).
Real creators overlap — a marathon coach covers hybrid training, a style
creator covers track club, a fitness vlogger dips into run clubs — and the
scoring is only meaningful when that gradient exists.

Trend-linked uploads are also dated *against the trend's own momentum curve*,
so a creator's publishing follows the trend as it rises. That makes creator
momentum and platform topic-velocity real measurements over the seeded world
rather than decoration.
"""

from __future__ import annotations

AFFINITY: dict[str, dict[str, float]] = {
    "run_community": {
        "trend-social-running-clubs": 0.95, "trend-marathon-debut": 0.40,
        "trend-run-commuting": 0.30, "trend-strava-wrapped": 0.20,
        "trend-track-club-fashion": 0.20, "trend-zone-2-everything": 0.10,
    },
    "fitness_lifestyle": {
        "trend-social-running-clubs": 0.50, "trend-hybrid-training": 0.45,
        "trend-zone-2-everything": 0.30, "trend-track-club-fashion": 0.30,
        "trend-marathon-debut": 0.20, "trend-silent-walking": 0.20,
    },
    "celebrity_fitness": {
        "trend-hybrid-training": 0.30, "trend-zone-2-everything": 0.20,
        "trend-marathon-debut": 0.18, "trend-silent-walking": 0.15,
        "trend-social-running-clubs": 0.12, "trend-strava-wrapped": 0.10,
    },
    "wellness_recovery": {
        "trend-zone-2-everything": 0.60, "trend-silent-walking": 0.40,
        "trend-hybrid-training": 0.20, "trend-marathon-debut": 0.15,
    },
    "athleisure_style": {
        "trend-track-club-fashion": 0.80, "trend-social-running-clubs": 0.30,
        "trend-run-commuting": 0.20,
    },
    "marathon_coach": {
        "trend-marathon-debut": 0.80, "trend-hybrid-training": 0.60,
        "trend-zone-2-everything": 0.40, "trend-social-running-clubs": 0.25,
    },
    "run_vlogger": {
        "trend-marathon-debut": 0.60, "trend-social-running-clubs": 0.45,
        "trend-run-commuting": 0.40, "trend-strava-wrapped": 0.30,
        "trend-track-club-fashion": 0.20,
    },
    "sports_science": {
        "trend-zone-2-everything": 0.70, "trend-hybrid-training": 0.60,
        "trend-marathon-debut": 0.20,
    },
    "college_athletics": {
        "trend-track-club-fashion": 0.50, "trend-social-running-clubs": 0.30,
        "trend-marathon-debut": 0.20,
    },
}

TITLES: dict[str, list[str]] = {
    "trend-social-running-clubs": [
        "I joined a social running club and everything changed",
        "Why run club is the best thing in my week",
        "Inside {city}'s fastest growing run club",
        "Run club long run, then coffee",
        "The running community nobody told you about",
        "Starting a run club from zero",
        "Run club pace groups, explained",
        "Social running club etiquette for beginners",
    ],
    "trend-strava-wrapped": [
        "Reacting to my Strava Wrapped",
        "Strava year in sport recap",
        "My Strava wrapped was humbling",
        "Strava recap: the full year of running",
    ],
    "trend-hybrid-training": [
        "Hybrid training week: run and lift",
        "How I became a hybrid athlete",
        "Strength for runners that actually works",
        "Run and lift in the same session",
        "Hybrid athlete training block",
        "Lifting made me a faster runner",
    ],
    "trend-zone-2-everything": [
        "Zone 2 training for a month",
        "Why all my runs are easy runs now",
        "Zone 2 explained properly",
        "Aerobic base building with zone 2",
        "Zone 2 changed my training",
    ],
    "trend-marathon-debut": [
        "My first marathon training block",
        "Marathon debut: week {n}",
        "Couch to marathon, honestly",
        "First marathon mistakes I made",
        "Marathon training vlog: the long run",
        "Training for my marathon debut",
    ],
    "trend-run-commuting": [
        "I run commuted for a month",
        "Run commute gear that survived",
        "Running to work every day",
        "The run commute setup",
    ],
    "trend-track-club-fashion": [
        "Track club fashion haul",
        "Styling retro running kit",
        "Track club aesthetic lookbook",
        "Why track club style is everywhere",
        "Retro running kit try-on",
    ],
    "trend-silent-walking": [
        "I tried silent walking",
        "Silent walking for a week",
        "Walking without headphones, honestly",
    ],
}
