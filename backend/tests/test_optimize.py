"""Portfolio Optimizer."""

from __future__ import annotations

import pytest

from app.engine.optimize import (
    build_audience_space,
    compare_portfolios,
    deduplicated_reach,
    mean_pairwise_overlap,
    overlap_matrix,
)


@pytest.fixture(scope="module")
def comparison(creators, scores, brief):
    return compare_portfolios(creators, scores, brief)


def test_both_portfolios_respect_the_budget(comparison, brief):
    for pf in (comparison.naive, comparison.optimized):
        assert pf.total_cost_usd <= brief.budget_usd
        assert len(pf.members) <= brief.max_creators
        assert len(pf.members) >= 1


def test_optimizer_actually_spends_the_budget(comparison):
    """A portfolio that leaves half the money unspent is not an answer."""
    assert comparison.optimized.budget_used_pct > 85


def test_optimized_mix_reduces_duplicate_reach(comparison):
    """The deck's claim: same budget, less overlap, broader coverage."""
    assert comparison.optimized.overlap_pct < comparison.naive.overlap_pct
    assert comparison.optimized.coverage_pct > comparison.naive.coverage_pct
    assert comparison.incremental_reach > 0


def test_optimizer_trades_individual_score_for_coverage(comparison):
    """The interesting result: it declines the highest-scoring line-up on
    purpose, because that line-up buys the same audience twice."""
    naive_ids = {m.creator_id for m in comparison.naive.members}
    optimized_ids = {m.creator_id for m in comparison.optimized.members}
    assert naive_ids != optimized_ids
    assert comparison.optimized.avg_opportunity_score < comparison.naive.avg_opportunity_score


def test_deduplicated_reach_is_below_gross_reach(comparison):
    for pf in (comparison.naive, comparison.optimized):
        assert 0 < pf.deduplicated_reach < pf.gross_reach


def test_brand_safety_exclusions_are_honoured(creators, scores, brief):
    flagged = {s.creator_id for s in scores if s.brand_safety_flag}
    assert flagged
    result = compare_portfolios(creators, scores, brief, exclude_flagged=True)
    chosen = {m.creator_id for m in result.optimized.members}
    assert not (chosen & flagged)
    assert result.optimized.notes


def test_overlap_metric_is_bounded_and_symmetric(creators, brief):
    space = build_audience_space(creators, brief)
    m = overlap_matrix(space)
    assert m.shape == (len(creators), len(creators))
    assert (m >= 0).all() and (m <= 1).all()
    assert (abs(m - m.T) < 1e-9).all()


def test_identical_audiences_overlap_more_than_different_ones(creators, brief, scores):
    """Sanity check on the duplication model itself."""
    by_id = {c.id: c for c in creators}
    space = build_audience_space(creators, brief)
    m = overlap_matrix(space)
    index = {c.id: i for i, c in enumerate(creators)}

    community = [c.id for c in creators if "Running Community" in c.archetype][:2]
    style = next(c.id for c in creators if "Athleisure" in c.archetype)
    same = m[index[community[0]], index[community[1]]]
    different = m[index[community[0]], index[style]]
    assert same > different
    assert by_id[style].archetype != by_id[community[0]].archetype


def test_smaller_budget_buys_fewer_creators(creators, scores, brief):
    lean = brief.model_copy(update={"budget_usd": 60_000.0})
    result = compare_portfolios(creators, scores, lean)
    assert result.optimized.total_cost_usd <= 60_000.0
    assert len(result.optimized.members) < brief.max_creators


def test_coverage_is_submodular(creators, brief):
    """Adding a creator to a bigger portfolio must add no more unique audience
    than adding them to a smaller one.

    Note this is a property of a *fixed* creator against nested sets — not a
    claim that a score-ordered portfolio shows monotonically falling gains. A
    creator further down the list can easily contribute more if their audience
    sits somewhere nobody above them reaches.
    """
    space = build_audience_space(creators, brief)
    candidate = len(creators) - 1
    small = [0, 1]
    large = [0, 1, 2, 3, 4]

    def gain(base):
        before = deduplicated_reach(space, base, target_only=True)
        after = deduplicated_reach(space, base + [candidate], target_only=True)
        return after - before

    assert gain(large) <= gain(small) + 1e-6


def test_marginal_coverage_is_reported_per_member(comparison):
    gains = [m.marginal_coverage for m in comparison.optimized.members]
    assert len(gains) == len(comparison.optimized.members)
    assert all(g >= 0 for g in gains)
    assert sum(gains) == pytest.approx(comparison.optimized.coverage_pct, abs=0.5)


def test_single_creator_has_no_overlap(creators, brief):
    space = build_audience_space(creators, brief)
    assert mean_pairwise_overlap(space, [0]) == 0.0
