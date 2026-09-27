import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type Portfolio } from "../../lib/api";
import { fmtCompact, fmtUsd } from "../../lib/format";
import { useSelection } from "../../state";
import { PortfolioCompareChart } from "../../components/charts/PortfolioCompareChart";
import {
  Answer,
  BigNumber,
  Card,
  Chip,
  Failed,
  Loading,
  NextStep,
  ShowWorking,
} from "../ui";

const DEFAULT_TREND = "trend-social-running-clubs";

function Option({
  p,
  recommended,
  caption,
}: {
  p: Portfolio;
  recommended?: boolean;
  caption: string;
}) {
  return (
    <div
      className="rounded-xl bg-surface p-4 ring-1"
      style={{
        borderRadius: "var(--radius-card)",
        boxShadow: recommended ? "inset 0 0 0 2px var(--brand)" : undefined,
      }}
    >
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-[15px] font-medium">
          {recommended ? "What we recommend" : "The obvious pick"}
        </h3>
        {recommended && <Chip tone="brand">Recommended</Chip>}
      </div>
      <p className="mt-1 text-[13px] leading-snug text-ink-2">{caption}</p>

      <div className="mt-4 flex flex-wrap gap-6">
        <BigNumber
          value={fmtCompact(p.deduplicated_reach)}
          label="People reached, counted once"
          tone={recommended ? "good" : "neutral"}
        />
        <BigNumber
          value={`${Math.round(p.overlap_pct)}%`}
          label="Paying twice for the same people"
          tone={recommended ? "good" : "neutral"}
        />
      </div>

      <ul className="mt-4 space-y-1.5 border-t pt-3" style={{ borderColor: "var(--gridline)" }}>
        {p.members.map((m) => (
          <li key={m.creator_id} className="flex items-baseline gap-2 text-[13px]">
            <span className="min-w-0 flex-1 truncate">
              {m.creator_name}
              <span className="ml-1.5 text-[11px] text-muted">
                {fmtCompact(m.subscribers)}
              </span>
            </span>
            <span className="tnum shrink-0 text-[12px] text-ink-2">{fmtUsd(m.cost_usd)}</span>
          </li>
        ))}
      </ul>
      <div className="mt-2 flex justify-between border-t pt-2 text-[13px]" style={{ borderColor: "var(--gridline)" }}>
        <span className="text-ink-2">Total</span>
        <span className="tnum font-medium">{fmtUsd(p.total_cost_usd)}</span>
      </div>
    </div>
  );
}

export function PortfolioPage() {
  const navigate = useNavigate();
  const { trendId } = useSelection();
  const id = trendId ?? DEFAULT_TREND;
  const { data, isLoading, error } = useQuery({
    queryKey: ["portfolio", id],
    queryFn: () => api.portfolio(id),
  });

  if (isLoading) return <Loading label="Working out the best mix" />;
  if (error || !data) return <Failed error={error} />;

  const { naive, optimized } = data;
  const given = naive.avg_opportunity_score - optimized.avg_opportunity_score;

  return (
    <>
      <Answer
        eyebrow="Where the money goes"
        headline={
          <>
            Same {fmtUsd(optimized.budget_usd)}.{" "}
            <span style={{ color: "var(--brand)" }}>
              {fmtCompact(data.incremental_reach)} more people.
            </span>
          </>
        }
        sub="Buying the five highest-scoring creators sells you the same audience five times. Swapping two of them for creators who reach people the others don't is worth more than the score you give up."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Option
          p={naive}
          caption="Take the highest scores until the budget runs out."
        />
        <Option
          p={optimized}
          recommended
          caption="Trade a little individual fit for people nobody else on the list reaches."
        />
      </div>

      <Card
        className="mt-4"
        title="What changes"
        sub="Reaching more of your target is good. Paying twice for the same viewers is not."
      >
        <PortfolioCompareChart
          comparison={data}
          height={220}
          labels={{
            coverage: "Your target reached",
            overlap: "Paying twice for the same people",
            naive: "The obvious pick",
            optimized: "What we recommend",
          }}
        />

        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <BigNumber
            value={`${Math.round(data.overlap_reduction_pts)}`}
            unit="pts"
            label="Less double-paying"
            tone="good"
          />
          <BigNumber
            value={`+${Math.round(data.coverage_gain_pts)}`}
            unit="pts"
            label="More of your target reached"
            tone="good"
          />
          <BigNumber
            value={given.toFixed(1)}
            unit="pts"
            label="Average fit given up — on purpose"
            tone="warning"
          />
        </div>

        <ShowWorking label="How the mix was chosen">
          <p>{data.verdict}</p>
          {optimized.notes.map((n) => (
            <p key={n} className="mt-2 text-muted">
              {n}
            </p>
          ))}
          <p className="mt-3">
            Chosen by solving for the best combination rather than picking down a ranked list: it
            maximises fit and audience reached per dollar, and subtracts a penalty every time two
            creators would reach the same people. Every combination that fits the budget is
            considered.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[560px] text-[12px]">
              <thead>
                <tr className="text-muted">
                  <th className="py-1.5 text-left font-medium">Creator</th>
                  <th className="py-1.5 text-left font-medium">Type</th>
                  <th className="py-1.5 text-right font-medium">Fit</th>
                  <th className="py-1.5 text-right font-medium">New audience added</th>
                  <th className="py-1.5 text-right font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {optimized.members.map((m) => (
                  <tr key={m.creator_id} className="border-t" style={{ borderColor: "var(--gridline)" }}>
                    <td className="py-1.5">{m.creator_name}</td>
                    <td className="py-1.5 text-ink-2">{m.archetype}</td>
                    <td className="tnum py-1.5 text-right">{m.opportunity_score.toFixed(0)}</td>
                    <td className="tnum py-1.5 text-right">+{m.marginal_coverage.toFixed(1)} pts</td>
                    <td className="tnum py-1.5 text-right">{fmtUsd(m.cost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-muted">
            "People reached, counted once" removes the double-counting: two creators who share a
            third of their audience do not reach the sum of their subscriber counts.
          </p>
        </ShowWorking>
      </Card>

      <NextStep label="See what we learned" onClick={() => navigate("/learning")} />
    </>
  );
}
