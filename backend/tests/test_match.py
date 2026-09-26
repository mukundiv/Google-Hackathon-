"""Creator Opportunity Score."""

from __future__ import annotations

import pytest

from app.engine.match import BASELINE_WEIGHTS, SIGNAL_LABELS
from app.models.creator import Provenance


def test_every_creator_scored_with_all_five_signals(scores, creators):
    assert len(scores) == len(creators)
    for s in scores:
        assert {sig.name for sig in s.signals} == set(BASELINE_WEIGHTS)
        assert 0 <= s.composite <= 100


def test_composite_is_the_weighted_sum_of_its_signals(scores):
    for s in scores:
        expected = sum(sig.score * sig.weight for sig in s.signals)
        assert s.composite == pytest.approx(expected, abs=0.1)


def test_weights_are_normalised(scores):
    assert sum(sig.weight for sig in scores[0].signals) == pytest.approx(1.0, abs=1e-6)


def test_reach_does_not_equal_relevance(scores, creators):
    """The deck's central claim about creators: the biggest channel should not
    win a trend it has no standing in."""
    by_id = {c.id: c for c in creators}
    biggest = max(scores, key=lambda s: s.subscribers)
    winner = min(scores, key=lambda s: s.rank)

    assert biggest.rank_by_reach == 1
    assert winner.subscribers < biggest.subscribers
    assert biggest.rank > 10, "the largest channel should not be near the top on fit"
    assert "Running Community" in by_id[winner.creator_id].archetype


def test_celebrity_archetype_loses_to_community_archetype(scores, creators):
    by_id = {c.id: c for c in creators}
    community = [s.composite for s in scores if "Running Community" in by_id[s.creator_id].archetype]
    celebrity = [s.composite for s in scores if "Celebrity" in by_id[s.creator_id].archetype]
    assert min(community) > max(celebrity)


def test_audience_provenance_is_labelled(scores):
    """Verified and inferred audience data must never be silently mixed."""
    provenances = set()
    for s in scores:
        sig = next(x for x in s.signals if x.name == "audience_fit")
        provenances.add(sig.provenance)
        if sig.provenance is Provenance.ESTIMATED:
            assert any("not owner-verified" in e for e in sig.evidence)
    assert Provenance.VERIFIED in provenances, "the demo needs a connected channel"
    assert Provenance.ESTIMATED in provenances


def test_verified_audience_carries_higher_confidence(scores):
    conf = {}
    for s in scores:
        sig = next(x for x in s.signals if x.name == "audience_fit")
        conf.setdefault(sig.provenance, []).append(sig.confidence)
    assert min(conf[Provenance.VERIFIED]) > max(conf[Provenance.ESTIMATED])


def test_creators_without_history_are_flagged_as_priors(scores):
    estimated = [
        sig
        for s in scores
        for sig in s.signals
        if sig.name == "proven_performance" and sig.provenance is Provenance.ESTIMATED
    ]
    assert estimated
    for sig in estimated:
        assert any("prior" in e.lower() for e in sig.evidence)


def test_every_signal_carries_evidence(scores):
    for s in scores:
        for sig in s.signals:
            assert sig.rationale, f"{s.creator_name}/{sig.name} has no rationale"
            assert sig.evidence, f"{s.creator_name}/{sig.name} has no evidence"
            assert sig.label == SIGNAL_LABELS[sig.name]


def test_brand_safety_flag_is_raised_and_explained(scores):
    flagged = [s for s in scores if s.brand_safety_flag]
    assert flagged, "the demo needs at least one creator to trip brand safety"
    for s in flagged:
        assert s.brand_safety_note


def test_score_distribution_is_usable(scores):
    """A scorer that clusters every creator together cannot support a decision."""
    values = sorted(s.composite for s in scores)
    assert max(values) - min(values) > 35
    assert len(set(round(v) for v in values)) > len(values) * 0.6


def test_ranks_are_dense_and_unique(scores):
    assert sorted(s.rank for s in scores) == list(range(1, len(scores) + 1))
    assert sorted(s.rank_by_reach for s in scores) == list(range(1, len(scores) + 1))
