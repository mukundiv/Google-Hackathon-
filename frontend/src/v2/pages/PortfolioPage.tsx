import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type ExcludedTopPick, type Portfolio } from "../../lib/api";
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

function Rank({ rank }: { rank?: number }) {
  if (!rank) return null;
  return (
    <span
      className="tnum shrink-0 text-[12px] font-medium"
      style={{ color: rank === 1 ? "var(--brand)" : "var(--text-muted)" }}
    >
      #{rank}
    </span>
  );
}

function Option({
  p,
  ranks,
  recommended,
  caption,
}: {
  p: Portfolio;
  ranks?: Record<string, number>;
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
            {/* The rank the last step gave them, so the two screens read as
                one list rather than two unrelated sets of names. */}
            <Rank rank={ranks?.[m.creator_id]} />
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
  const ranks = data.ranks;
  const excluded: ExcludedTopPick[] = data.excluded_top_picks ?? [];
  // The top five by fit, each one accounted for: kept, or dropped with the
  // reason. Without this the best-fit creator just vanishes between steps.
  const topPicks = [1, 2, 3, 4, 5].map((rank) => {
    const dropped = excluded.find((e) => e.rank === rank);
    if (dropped) return { rank, name: dropped.creator_name, dropped };
    const member = optimized.members.find((m) => ranks?.[m.creator_id] === rank);
    return { rank, name: member?.creator_name, dropped: undefined };
  });
  const keptTop = topPicks.filter((t) => t.name && !t.dropped).length;

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
        sub="The mix is built from the same ranking as the last step — but it does not just buy the top of it. Taking the five highest-scoring creators sells you the same audience five times; swapping some of them for creators who reach people the others don't is worth more than the score you give up."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Option
          p={naive}
          ranks={ranks}
          caption="Take the highest scores until the budget runs out."
        />
        <Option
          p={optimized}
          ranks={ranks}
          recommended
          caption="Trade a little individual fit for people nobody else on the list reaches."
        />
      </div>

      {excluded.length > 0 && (
        <Card
          className="mt-4"
          title="What happened to the top picks"
          sub={`${keptTop} of the five best-fit creators are in the mix. Here is where the others went.`}
        >
          <ul className="space-y-2.5">
            {topPicks
              .filter((t) => t.name)
              .map((t) => (
                <li key={t.rank} className="flex items-start gap-2.5 text-[13px]">
                  <Rank rank={t.rank} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{t.name}</span>
                      {t.dropped ? (
                        <Chip tone="warning">Not bought</Chip>
                      ) : (
                        <Chip tone="good">In the mix</Chip>
                      )}
                    </div>
                    <p className="mt-0.5 leading-snug text-ink-2">
                      {t.dropped
                        ? t.dropped.reason.charAt(0).toUpperCase() + t.dropped.reason.slice(1) + "."
                        : "Kept — strong fit and an audience the rest of the mix does not already reach."}
                    </p>
                  </div>
                  {t.dropped && (
                    <span className="tnum shrink-0 text-[12px] text-muted">
                      {fmtUsd(t.dropped.cost_usd)}
                    </span>
                  )}
                </li>
              ))}
          </ul>
          <ShowWorking label="The two numbers that decided it">
            <p>
              A highly ranked creator is dropped for one of two reasons: their fee takes a share of
              the budget large enough that the same money buys more new people spread across others,
              or the mix already reaches much of their audience, so what you are paying for is a
              second impression rather than a new person.
            </p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[480px] text-[12px]">
                <thead>
                  <tr className="text-muted">
                    <th className="py-1.5 text-left font-medium">Creator</th>
                    <th className="py-1.5 text-right font-medium">Fit</th>
                    <th className="py-1.5 text-right font-medium">Share of budget</th>
                    <th className="py-1.5 text-right font-medium">Audience already reached</th>
                  </tr>
                </thead>
                <tbody>
                  {excluded.map((e) => (
                    <tr key={e.creator_id} className="border-t" style={{ borderColor: "var(--gridline)" }}>
                      <td className="py-1.5">
                        #{e.rank} {e.creator_name}
                      </td>
                      <td className="tnum py-1.5 text-right">{e.composite.toFixed(0)}</td>
                      <td className="tnum py-1.5 text-right">{e.budget_share_pct.toFixed(0)}%</td>
                      <td className="tnum py-1.5 text-right">{e.overlap_with_mix_pct.toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ShowWorking>
        </Card>
      )}

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
            <table className="w-full min-w-[620px] text-[12px]">
              <thead>
                <tr className="text-muted">
                  <th className="py-1.5 text-left font-medium">Fit rank</th>
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
                    <td className="tnum py-1.5">#{ranks?.[m.creator_id] ?? "—"}</td>
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
