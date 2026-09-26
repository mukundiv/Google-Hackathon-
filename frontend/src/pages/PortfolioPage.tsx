import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type Portfolio } from "../lib/api";
import { fmtCompact, fmtInt, fmtPct, fmtUsd } from "../lib/format";
import { useSelection } from "../state";
import { PortfolioCompareChart } from "../components/charts/PortfolioCompareChart";
import { Card, ErrorNote, SectionLabel, Spinner, StatTile } from "../components/ui";

const DEFAULT_TREND = "trend-social-running-clubs";

function PortfolioColumn({
  p,
  accent,
  highlight,
}: {
  p: Portfolio;
  accent: string;
  highlight?: boolean;
}) {
  return (
    <div
      className="rounded-xl bg-surface p-4 ring-1"
      style={{
        boxShadow: highlight ? `inset 0 0 0 2px ${accent}` : undefined,
        borderColor: "var(--border)",
      }}
    >
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-[14px] font-semibold" style={{ color: accent }}>
          {p.label}
        </h3>
        <span className="tnum text-[12px] text-muted">{p.members.length} creators</span>
      </div>
      <p className="mt-0.5 text-[12px] leading-snug text-ink-2">{p.strategy}</p>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-raised py-2">
          <div className="tnum text-[15px] font-semibold">{fmtPct(p.coverage_pct)}</div>
          <div className="text-[10px] uppercase tracking-wide text-muted">coverage</div>
        </div>
        <div className="rounded-lg bg-raised py-2">
          <div className="tnum text-[15px] font-semibold">{fmtPct(p.overlap_pct)}</div>
          <div className="text-[10px] uppercase tracking-wide text-muted">overlap</div>
        </div>
        <div className="rounded-lg bg-raised py-2">
          <div className="tnum text-[15px] font-semibold">{fmtCompact(p.deduplicated_reach)}</div>
          <div className="text-[10px] uppercase tracking-wide text-muted">net reach</div>
        </div>
      </div>

      <ul className="mt-3 space-y-1.5">
        {p.members.map((m) => (
          <li key={m.creator_id} className="flex items-baseline gap-2 text-[13px]">
            <span className="min-w-0 flex-1">
              <span className="font-medium">{m.creator_name}</span>
              <span className="ml-1.5 text-[11px] text-muted">
                {m.archetype} · {fmtCompact(m.subscribers)}
              </span>
            </span>
            <span className="tnum shrink-0 text-[12px] text-ink-2">{fmtUsd(m.cost_usd)}</span>
            <span className="tnum w-8 shrink-0 text-right font-semibold">
              {m.opportunity_score.toFixed(0)}
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-3 border-t pt-2 text-[12px]" style={{ borderColor: "var(--gridline)" }}>
        <div className="flex justify-between">
          <span className="text-ink-2">Spend</span>
          <span className="tnum font-semibold">
            {fmtUsd(p.total_cost_usd)}{" "}
            <span className="font-normal text-muted">
              ({((p.total_cost_usd / p.budget_usd) * 100).toFixed(0)}% of budget)
            </span>
          </span>
        </div>
        <div className="mt-0.5 flex justify-between">
          <span className="text-ink-2">Average opportunity score</span>
          <span className="tnum font-semibold">{p.avg_opportunity_score.toFixed(1)}</span>
        </div>
      </div>
    </div>
  );
}

/** Stage 04 — the best creators and the best mix are different things. */
export function PortfolioPage() {
  const navigate = useNavigate();
  const { trendId } = useSelection();
  const id = trendId ?? DEFAULT_TREND;

  const { data, isLoading, error } = useQuery({
    queryKey: ["portfolio", id],
    queryFn: () => api.portfolio(id),
  });

  if (isLoading) return <Spinner label="Solving the portfolio" />;
  if (error || !data) return <ErrorNote error={error} />;

  const { naive, optimized } = data;
  const scoreGiveUp = naive.avg_opportunity_score - optimized.avg_opportunity_score;

  return (
    <div className="space-y-5">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-widest text-muted">
          04 · Optimize
        </div>
        <h1 className="mt-1 text-2xl font-semibold">Portfolio Optimizer</h1>
        <p className="mt-1 max-w-3xl text-[14px] leading-snug text-ink-2">
          Buying the highest-scoring creators buys the same audience several times. The optimiser
          maximises fit and coverage per dollar while penalising duplicate reach, solved as a
          mixed-integer program over the whole pool.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Overlap removed"
          value={data.overlap_reduction_pts.toFixed(1)}
          unit="pts"
          tone="good"
          size="lg"
          note={`${fmtPct(naive.overlap_pct)} → ${fmtPct(optimized.overlap_pct)} duplicate audience`}
        />
        <StatTile
          label="Coverage gained"
          value={`+${data.coverage_gain_pts.toFixed(1)}`}
          unit="pts"
          tone="good"
          note={`${fmtPct(naive.coverage_pct)} → ${fmtPct(optimized.coverage_pct)} of the target`}
        />
        <StatTile
          label="Extra people reached"
          value={fmtCompact(data.incremental_reach)}
          tone="good"
          note="Same budget, distinct humans"
        />
        <StatTile
          label="Average score given up"
          value={scoreGiveUp.toFixed(1)}
          unit="pts"
          tone={scoreGiveUp > 0 ? "warning" : "neutral"}
          note="The trade the optimiser makes on purpose"
        />
      </div>

      <Card
        title="Same budget, two answers"
        subtitle="Coverage should be high and overlap should be low — the optimised mix moves both the right way."
      >
        <PortfolioCompareChart comparison={data} />
        <p className="mt-3 text-[14px] leading-relaxed">{data.verdict}</p>
        {optimized.notes.map((n) => (
          <p key={n} className="mt-1.5 text-[12px] text-muted">
            {n}
          </p>
        ))}
      </Card>

      <div>
        <SectionLabel>Side by side</SectionLabel>
        <div className="grid gap-4 lg:grid-cols-2">
          <PortfolioColumn p={naive} accent="var(--series-1)" />
          <PortfolioColumn p={optimized} accent="var(--series-2)" highlight />
        </div>
      </div>

      <Card title="Recommended allocation" subtitle={`Solved with ${optimized.solver}.`}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-[13px]">
            <thead>
              <tr className="text-[11px] uppercase tracking-wide text-muted">
                <th className="px-2 py-2 text-left font-semibold">Creator</th>
                <th className="px-2 py-2 text-left font-semibold">Role in the mix</th>
                <th className="px-2 py-2 text-right font-semibold">Score</th>
                <th className="px-2 py-2 text-right font-semibold">Unique coverage added</th>
                <th className="px-2 py-2 text-right font-semibold">Budget</th>
              </tr>
            </thead>
            <tbody>
              {optimized.members.map((m) => (
                <tr key={m.creator_id} className="border-t" style={{ borderColor: "var(--gridline)" }}>
                  <td className="px-2 py-2.5">
                    <div className="font-medium">{m.creator_name}</div>
                    <div className="text-[11px] text-muted">{fmtInt(m.subscribers)} subscribers</div>
                  </td>
                  <td className="px-2 py-2.5 text-ink-2">{m.archetype}</td>
                  <td className="tnum px-2 py-2.5 text-right">{m.opportunity_score.toFixed(1)}</td>
                  <td className="tnum px-2 py-2.5 text-right">+{m.marginal_coverage.toFixed(1)} pts</td>
                  <td className="tnum px-2 py-2.5 text-right font-semibold">{fmtUsd(m.cost_usd)}</td>
                </tr>
              ))}
              <tr className="border-t font-semibold" style={{ borderColor: "var(--baseline)" }}>
                <td className="px-2 py-2.5" colSpan={4}>
                  Total
                </td>
                <td className="tnum px-2 py-2.5 text-right">{fmtUsd(optimized.total_cost_usd)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex justify-end">
        <button
          onClick={() => navigate("/learning")}
          className="rounded-md px-4 py-2 text-[13px] font-medium text-white"
          style={{ background: "var(--series-1)" }}
        >
          Close the loop with results →
        </button>
      </div>
    </div>
  );
}
