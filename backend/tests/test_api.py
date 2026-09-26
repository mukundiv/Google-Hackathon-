"""HTTP surface."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_reports_the_active_provider_for_each_signal(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert set(body["providers"]) == {"gemini", "youtube", "trends", "analytics"}
    for state in body["providers"].values():
        assert state["active"] in {"mock", "live", "bigquery", "oauth"}
        assert isinstance(state["live"], bool)


def test_console_runs_with_no_credentials_configured(client):
    """The whole product has to work before any API integration happens."""
    body = client.get("/api/health").json()
    assert body["any_live"] is False
    assert client.post("/api/run").status_code == 200


def test_scout_returns_ranked_opportunities(client):
    body = client.post("/api/scout", json={"limit": 8}).json()
    ops = body["opportunities"]
    assert len(ops) >= 6
    verdicts = [o["window"]["verdict"] for o in ops]
    assert verdicts.index("PASS") > verdicts.index("ACT"), "actionable trends should rank first"
    for o in ops:
        assert o["trend"]["citations"], "every scouted trend must carry its sources"


def test_full_run_reproduces_the_deck_scenario(client):
    body = client.post("/api/run").json()
    chosen = body["chosen"]
    assert chosen["trend"]["name"] == "Social Running Clubs"
    assert chosen["window"]["verdict"] == "ACT"
    assert 10 <= chosen["window"]["capture_window_days"] <= 16
    assert body["portfolio"]["optimized"]["overlap_pct"] < body["portfolio"]["naive"]["overlap_pct"]
    assert body["recommendation"]


def test_capture_endpoint_returns_the_curve(client):
    body = client.get("/api/capture/trend-social-running-clubs").json()
    assert len(body["momentum"]) > 100
    assert body["window"]["verdict"] == "ACT"


def test_unknown_trend_is_a_404(client):
    assert client.get("/api/capture/trend-does-not-exist").status_code == 404
    assert client.post("/api/creators/score", json={"trend_id": "nope"}).status_code == 404


def test_scores_carry_archetype_and_reach_rank(client):
    body = client.post(
        "/api/creators/score", json={"trend_id": "trend-social-running-clubs"}
    ).json()
    scores = body["scores"]
    assert scores[0]["rank"] == 1
    assert all("archetype" in s for s in scores)
    assert any(s["reach_relevance_delta"] < -5 for s in scores), "expected a big-but-unfit creator"


def test_brand_portal_summarises_history(client):
    body = client.get("/api/brand").json()
    assert body["insights"]["campaigns_run"] == 8
    assert body["insights"]["best_archetypes"]
    assert body["suggested_brief"]["budget_usd"] == 250_000


def test_learning_loop_absorbs_a_new_result(client):
    before = client.get("/api/learning").json()
    payload = {
        "name": "Test Activation",
        "trend_name": "Social Running Clubs",
        "trend_category": "community_behaviour",
        "spend_usd": 120_000,
        "activation_lead_days": 6.0,
        "signal_snapshot": {
            "content_fit": 94, "audience_fit": 90, "brand_fit": 70,
            "momentum": 92, "proven_performance": 50,
        },
        "predicted": {"performance_index": 80.0},
        "actual": {"performance_index": 93.0},
    }
    after = client.post("/api/learning/observe", json=payload).json()
    assert after["ok"]
    assert after["state"]["campaigns_learned_from"] == before["campaigns_learned_from"] + 1

    applied = client.post("/api/learning/apply").json()
    assert applied["state"]["applied_version"] != "baseline"

    reset = client.post("/api/learning/reset").json()
    assert reset["state"]["campaigns_learned_from"] == before["campaigns_learned_from"]
    assert reset["state"]["applied_version"] == "baseline"


def test_applied_weights_are_not_reported_as_pending(client):
    """Adopting the recommended weighting must clear the 'newer weighting
    available' state — the version gains a time suffix on apply, so comparing
    the full string reported a pending change forever."""
    client.post("/api/learning/reset")
    assert client.get("/api/learning").json()["pending_change"] is True

    client.post("/api/learning/apply")
    after = client.get("/api/learning").json()
    assert after["applied_version"].startswith(after["current"]["version"])
    assert after["pending_change"] is False

    client.post("/api/learning/reset")
