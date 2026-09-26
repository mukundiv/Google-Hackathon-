"""Stage 04 — Optimize: the Portfolio Optimizer.

The deck's point is that the best creators and the best *mix* of creators are
different things. Picking the top-ranked names buys the same audience several
times; the optimiser trades a little individual fit for coverage the brand is
not already paying for.

Maximise, subject to budget and portfolio size:

    sum(opportunity score)  +  audience coverage  -  audience overlap

Coverage is submodular — the second creator in a segment adds less than the
first — so it is linearised for the solver as a per-segment saturation
variable. Overlap needs the pairwise product of two selection variables, which
is linearised the standard way. The solver optimises that surrogate; the
numbers reported back to the brand are computed exactly, including a
Sainsbury-style deduplicated reach that the MILP cannot express.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pulp

from app.models.brief import CampaignBrief
from app.models.creator import Creator, CreatorOpportunityScore
from app.models.portfolio import Portfolio, PortfolioComparison, PortfolioMember

# Objective weights. Score dominates; coverage is worth real money; overlap is
# a penalty rather than a hard constraint so the solver can still buy a
# redundant creator when they are simply much better.
W_SCORE = 1.0
W_COVERAGE = 1.6
W_OVERLAP = 0.9

# Segment populations are anchored to what a single large creator can reach:
# the biggest creator in a segment is assumed to touch this share of it.
# Deriving the population by summing every creator's reach instead badly
# overstates it, because those audiences overlap each other heavily.
SINGLE_CREATOR_MAX_PENETRATION = 0.55


@dataclass
class AudienceSpace:
    """Segment-level reach for every creator, plus segment populations."""

    segments: list[str]
    target_mask: np.ndarray  # 1.0 where the segment is in the brief's target
    reach: np.ndarray  # creators x segments, in viewers
    population: np.ndarray  # notional addressable people per segment

    def totals(self) -> np.ndarray:
        return self.reach.sum(axis=1)


def build_audience_space(creators: list[Creator], brief: CampaignBrief) -> AudienceSpace:
    segments = sorted({s.key for c in creators for s in c.audience_segments})
    index = {s: i for i, s in enumerate(segments)}
    target = set(brief.audience.segment_keys())

    reach = np.zeros((len(creators), len(segments)))
    for i, c in enumerate(creators):
        for seg in c.audience_segments:
            reach[i, index[seg.key]] = seg.weight * c.avg_views

    population = reach.max(axis=0) / SINGLE_CREATOR_MAX_PENETRATION
    population[population == 0] = 1.0
    mask = np.array([1.0 if s in target else 0.0 for s in segments])
    return AudienceSpace(segments=segments, target_mask=mask, reach=reach, population=population)


def overlap_matrix(space: AudienceSpace) -> np.ndarray:
    """Pairwise audience duplication rate.

    Cosine similarity was the wrong tool here: it compares the *shape* of two
    audiences, and since nearly every creator in a running niche skews the
    same way it reported ~90% overlap for every possible pair, which made the
    penalty uninformative. What a media planner actually wants is the share of
    the smaller audience that the larger one already reaches. Assuming
    independence within each segment, the expected duplicated audience is
    sum_s (r_is * r_ks / P_s).
    """
    reach, pop = space.reach, space.population
    duplicated = (reach / pop) @ reach.T  # [i,k] = sum_s r_is * r_ks / P_s
    totals = space.totals()
    smaller = np.minimum.outer(totals, totals)
    smaller[smaller == 0] = 1.0
    m = np.clip(duplicated / smaller, 0.0, 1.0)
    np.fill_diagonal(m, 1.0)
    return m


# --------------------------------------------------------------------------
# exact metrics (reported to the brand)
# --------------------------------------------------------------------------
def deduplicated_reach(space: AudienceSpace, selected: list[int], target_only: bool) -> float:
    """Sainsbury-style combined reach: within each segment, treat creators'
    audiences as independently overlapping rather than additive."""
    if not selected:
        return 0.0
    pop = space.population
    frac = np.clip(space.reach[selected] / pop, 0.0, 1.0)
    combined = pop * (1.0 - np.prod(1.0 - frac, axis=0))
    if target_only:
        combined = combined * space.target_mask
    return float(combined.sum())


def coverage_pct(space: AudienceSpace, selected: list[int]) -> float:
    """Share of the addressable *target* audience the portfolio reaches."""
    addressable = float((space.population * space.target_mask).sum())
    if addressable <= 0:
        return 0.0
    return deduplicated_reach(space, selected, target_only=True) / addressable * 100.0


def mean_pairwise_overlap(space: AudienceSpace, selected: list[int]) -> float:
    if len(selected) < 2:
        return 0.0
    m = overlap_matrix(space)
    vals = [m[i, j] for a, i in enumerate(selected) for j in selected[a + 1:]]
    return float(np.mean(vals)) * 100.0


def _portfolio(
    label: str,
    strategy: str,
    selected: list[int],
    creators: list[Creator],
    scores: dict[str, CreatorOpportunityScore],
    space: AudienceSpace,
    brief: CampaignBrief,
    solver: str,
    objective: float = 0.0,
) -> Portfolio:
    members: list[PortfolioMember] = []
    running: list[int] = []
    for i in sorted(selected, key=lambda i: -scores[creators[i].id].composite):
        before = deduplicated_reach(space, running, target_only=True)
        running.append(i)
        after = deduplicated_reach(space, running, target_only=True)
        addressable = float((space.population * space.target_mask).sum()) or 1.0
        members.append(
            PortfolioMember(
                creator_id=creators[i].id,
                creator_name=creators[i].name,
                archetype=creators[i].archetype,
                subscribers=creators[i].subscribers,
                opportunity_score=scores[creators[i].id].composite,
                cost_usd=scores[creators[i].id].estimated_cost_usd,
                marginal_coverage=round((after - before) / addressable * 100.0, 2),
            )
        )

    total_cost = sum(m.cost_usd for m in members)
    avg_score = float(np.mean([m.opportunity_score for m in members])) if members else 0.0
    gross = int(sum(creators[i].avg_views for i in selected))
    dedup = int(deduplicated_reach(space, selected, target_only=False))

    return Portfolio(
        label=label,
        strategy=strategy,
        members=members,
        total_cost_usd=round(total_cost, 2),
        budget_usd=brief.budget_usd,
        avg_opportunity_score=round(avg_score, 1),
        coverage_pct=round(coverage_pct(space, selected), 1),
        overlap_pct=round(mean_pairwise_overlap(space, selected), 1),
        gross_reach=gross,
        deduplicated_reach=dedup,
        objective_value=round(objective, 3),
        solver=solver,
    )


# --------------------------------------------------------------------------
# strategies
# --------------------------------------------------------------------------
def naive_top_ranked(
    creators: list[Creator],
    scores: dict[str, CreatorOpportunityScore],
    brief: CampaignBrief,
    space: AudienceSpace,
    eligible: list[int],
) -> Portfolio:
    """The obvious approach: buy the highest-scoring creators you can afford.

    This is the baseline the deck argues against, and it is a fair one — it
    spends the same budget and respects the same size cap.
    """
    ordered = sorted(eligible, key=lambda i: -scores[creators[i].id].composite)
    selected: list[int] = []
    spend = 0.0
    for i in ordered:
        cost = scores[creators[i].id].estimated_cost_usd
        if len(selected) >= brief.max_creators or spend + cost > brief.budget_usd:
            continue
        selected.append(i)
        spend += cost
    return _portfolio(
        "Top-ranked selection", "Highest opportunity scores that fit the budget",
        selected, creators, scores, space, brief, "greedy_by_score",
    )


def optimize_portfolio(
    creators: list[Creator],
    scores: dict[str, CreatorOpportunityScore],
    brief: CampaignBrief,
    space: AudienceSpace,
    eligible: list[int],
) -> Portfolio:
    n = len(creators)
    m = overlap_matrix(space)
    target_idx = [j for j, v in enumerate(space.target_mask) if v > 0]

    problem = pulp.LpProblem("creator_portfolio", pulp.LpMaximize)
    x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in eligible}
    # Per-segment saturation variable: the diminishing-returns part.
    y = {j: pulp.LpVariable(f"y_{j}", lowBound=0.0, upBound=1.0) for j in target_idx}
    # Pairwise co-selection, for the overlap penalty.
    pairs = [(i, k) for a, i in enumerate(eligible) for k in eligible[a + 1:]]
    z = {(i, k): pulp.LpVariable(f"z_{i}_{k}", lowBound=0.0, upBound=1.0) for i, k in pairs}

    score_term = pulp.lpSum(
        (scores[creators[i].id].composite / 100.0) * x[i] for i in eligible
    )
    seg_weight = {j: float(space.population[j]) for j in target_idx}
    total_seg = sum(seg_weight.values()) or 1.0
    coverage_term = pulp.lpSum((seg_weight[j] / total_seg) * y[j] for j in target_idx)
    overlap_term = pulp.lpSum(float(m[i, k]) * z[(i, k)] for i, k in pairs)
    pair_norm = max(1.0, len(pairs) / max(1, brief.max_creators))

    problem += (
        W_SCORE * score_term
        + W_COVERAGE * coverage_term * brief.max_creators
        - W_OVERLAP * overlap_term / pair_norm
    )

    # y_j can only be as large as the share of segment j the portfolio reaches.
    for j in target_idx:
        problem += y[j] <= pulp.lpSum(
            float(space.reach[i, j] / space.population[j]) * x[i] for i in eligible
        )

    for i, k in pairs:
        problem += z[(i, k)] >= x[i] + x[k] - 1
        problem += z[(i, k)] <= x[i]
        problem += z[(i, k)] <= x[k]

    problem += pulp.lpSum(
        scores[creators[i].id].estimated_cost_usd * x[i] for i in eligible
    ) <= brief.budget_usd
    problem += pulp.lpSum(x[i] for i in eligible) <= brief.max_creators
    problem += pulp.lpSum(x[i] for i in eligible) >= min(brief.min_creators, len(eligible))

    try:
        status = problem.solve(_solver())
    except Exception:
        return greedy_marginal(creators, scores, brief, space, eligible)
    if pulp.LpStatus[status] != "Optimal":
        return greedy_marginal(creators, scores, brief, space, eligible)

    selected = [i for i in eligible if x[i].value() and x[i].value() > 0.5]
    return _portfolio(
        "Optimized portfolio",
        "Maximises fit and audience coverage per dollar while penalising overlap",
        selected, creators, scores, space, brief, "milp_cbc",
        objective=float(pulp.value(problem.objective) or 0.0),
    )


def _solver():
    """Prefer the current CBC entry point, fall back to the legacy one."""
    for factory in ("COIN_CMD", "PULP_CBC_CMD"):
        cmd = getattr(pulp, factory, None)
        if cmd is None:
            continue
        try:
            solver = cmd(msg=False)
            if solver.available():
                return solver
        except Exception:
            continue
    raise RuntimeError("no CBC solver available")


def greedy_marginal(
    creators: list[Creator],
    scores: dict[str, CreatorOpportunityScore],
    brief: CampaignBrief,
    space: AudienceSpace,
    eligible: list[int],
) -> Portfolio:
    """Submodular greedy fallback: repeatedly add the creator with the best
    marginal value per dollar. Used if the MILP solver is unavailable."""
    selected: list[int] = []
    spend = 0.0
    remaining = list(eligible)

    while remaining and len(selected) < brief.max_creators:
        best, best_gain = None, -1e18
        base_cov = deduplicated_reach(space, selected, target_only=True)
        for i in remaining:
            cost = scores[creators[i].id].estimated_cost_usd
            if spend + cost > brief.budget_usd:
                continue
            gain_cov = deduplicated_reach(space, selected + [i], target_only=True) - base_cov
            gain = (
                W_SCORE * scores[creators[i].id].composite / 100.0
                + W_COVERAGE * gain_cov / max(1.0, float(space.population.sum()))
            ) / max(cost, 1.0) * 1e5
            if gain > best_gain:
                best, best_gain = i, gain
        if best is None:
            break
        selected.append(best)
        spend += scores[creators[best].id].estimated_cost_usd
        remaining.remove(best)

    return _portfolio(
        "Optimized portfolio", "Greedy marginal-value fallback",
        selected, creators, scores, space, brief, "greedy_submodular",
    )


def compare_portfolios(
    creators: list[Creator],
    scores: list[CreatorOpportunityScore],
    brief: CampaignBrief,
    exclude_flagged: bool = True,
) -> PortfolioComparison:
    by_id = {s.creator_id: s for s in scores}
    space = build_audience_space(creators, brief)

    eligible = [
        i for i, c in enumerate(creators)
        if c.id in by_id and not (exclude_flagged and by_id[c.id].brand_safety_flag)
    ]

    naive = naive_top_ranked(creators, by_id, brief, space, eligible)
    optimized = optimize_portfolio(creators, by_id, brief, space, eligible)

    if exclude_flagged and len(eligible) < len(creators):
        dropped = len(creators) - len(eligible)
        optimized.notes.append(
            f"{dropped} creator(s) excluded for brand-safety review before optimisation."
        )

    return PortfolioComparison(
        naive=naive,
        optimized=optimized,
        overlap_reduction_pts=round(naive.overlap_pct - optimized.overlap_pct, 1),
        coverage_gain_pts=round(optimized.coverage_pct - naive.coverage_pct, 1),
        incremental_reach=optimized.deduplicated_reach - naive.deduplicated_reach,
        verdict=_verdict(naive, optimized),
    )


def _verdict(naive: Portfolio, optimized: Portfolio) -> str:
    d_overlap = naive.overlap_pct - optimized.overlap_pct
    d_cover = optimized.coverage_pct - naive.coverage_pct
    if d_overlap <= 0 and d_cover <= 0:
        return (
            "The top-ranked selection is already efficient for this brief — the "
            "highest-scoring creators do not duplicate each other."
        )
    return (
        f"Same budget, {d_overlap:.0f} points less audience overlap and "
        f"{d_cover:.0f} points more coverage of the target audience. The "
        f"optimised mix reaches {optimized.deduplicated_reach - naive.deduplicated_reach:,} "
        "more distinct people."
    )
