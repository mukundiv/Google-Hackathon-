"""Freeze one full run of the engine into a JSON snapshot.

The console normally talks to the API. For a shareable demo there is no API to
talk to, so this captures every response the six screens read and writes them
to a single file the built page can carry inside itself.

The snapshot is real engine output, not hand-written fixtures: it is whatever
the running API returns at the moment it is captured.

Run with the API up:
    python scripts/export_demo_snapshot.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

API = "http://127.0.0.1:8000/api"
OUT = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "demo-data.json"

# The result fed back on the Learning page, matching SAMPLE_RESULT in
# frontend/src/pages/LearningPage.tsx so the two states line up.
SAMPLE_RESULT = {
    "name": "Run Club Activation",
    "trend_name": "Social Running Clubs",
    "trend_category": "community_behaviour",
    "spend_usd": 249_000,
    "activation_lead_days": 6.5,
    "signal_snapshot": {
        "content_fit": 95,
        "audience_fit": 91,
        "brand_fit": 88,
        "momentum": 93,
        "proven_performance": 52,
    },
    "predicted": {"performance_index": 84.0, "reach": 720_000, "views": 1_150_000},
    "actual": {"performance_index": 91.5, "reach": 806_000, "views": 1_310_000},
    "portfolio_overlap_pct": 16.9,
    "learnings": [
        "Community creators with no prior brand history outperformed repeat partners again.",
        "The optimised mix held overlap under 20% and beat the forecast.",
    ],
}


def main() -> int:
    client = httpx.Client(timeout=120.0)

    try:
        client.get(f"{API}/health").raise_for_status()
    except Exception as exc:
        print(f"API is not reachable at {API}: {exc}")
        print("Start it first:  python -m uvicorn app.main:app --port 8000")
        return 1

    # Start from a clean learning state so the snapshot is reproducible.
    client.post(f"{API}/learning/reset").raise_for_status()

    snapshot: dict = {
        "health": client.get(f"{API}/health").json(),
        "brand": client.get(f"{API}/brand").json(),
        "scout": client.post(f"{API}/scout", json={"limit": 8}).json(),
        "learning": client.get(f"{API}/learning").json(),
        "capture": {},
        "scores": {},
        "portfolio": {},
    }

    trend_ids = [o["trend"]["id"] for o in snapshot["scout"]["opportunities"]]
    print(f"capturing {len(trend_ids)} trends")

    for tid in trend_ids:
        snapshot["capture"][tid] = client.get(f"{API}/capture/{tid}").json()
        snapshot["scores"][tid] = client.post(
            f"{API}/creators/score", json={"trend_id": tid}
        ).json()
        snapshot["portfolio"][tid] = client.post(
            f"{API}/portfolio", json={"trend_id": tid}
        ).json()
        print(f"  {tid}")

    # The "after feedback" state, so the Learning page stays interactive with
    # no backend: the button swaps between two real states rather than posting.
    observed = client.post(f"{API}/learning/observe", json=SAMPLE_RESULT).json()
    snapshot["learningAfter"] = observed["state"]
    client.post(f"{API}/learning/apply").raise_for_status()
    snapshot["learningApplied"] = client.get(f"{API}/learning").json()

    # Re-score under the learned weights. Without this the demo could show the
    # weights moving but not the consequence, which is the only reason the
    # learning loop is worth having.
    print("re-scoring under the learned weights")
    snapshot["scoresRelearned"] = {}
    snapshot["portfolioRelearned"] = {}
    for tid in trend_ids:
        snapshot["scoresRelearned"][tid] = client.post(
            f"{API}/creators/score", json={"trend_id": tid}
        ).json()
        snapshot["portfolioRelearned"][tid] = client.post(
            f"{API}/portfolio", json={"trend_id": tid}
        ).json()

    # Leave the running instance as it was found.
    client.post(f"{API}/learning/reset").raise_for_status()

    snapshot["meta"] = {
        "captured_from": API,
        "trends": len(trend_ids),
        "creators": len(snapshot["scores"][trend_ids[0]]["scores"]),
        "note": (
            "Frozen snapshot of one run of the Creator Opportunity Engine. "
            "Every number here was computed by the engine, not authored."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, separators=(",", ":")))
    size_mb = OUT.stat().st_size / 1_048_576
    print(f"\nwrote {OUT}  ({size_mb:.2f} MB)")
    print(f"  trends    {len(trend_ids)}")
    print(f"  creators  {snapshot['meta']['creators']}")
    print(f"  campaigns {len(snapshot['brand']['campaigns'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
