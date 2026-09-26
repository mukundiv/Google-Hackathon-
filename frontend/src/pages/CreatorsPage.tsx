import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type CreatorScore } from "../lib/api";
import { fmtCompact, fmtUsd } from "../lib/format";
import { useSelection } from "../state";
import { ReachRelevanceChart } from "../components/charts/ReachRelevanceChart";
import { SignalBars } from "../components/charts/SignalBars";
import { Badge, Card, ErrorNote, SectionLabel, Spinner, StatTile } from "../components/ui";

const DEFAULT_TREND = "trend-social-running-clubs";

function CreatorRow({
  s,
  open,
  onToggle,
}: {
  s: CreatorScore;
  open: boolean;
  onToggle: () => void;
}) {
  const delta = s.reach_relevance_delta ?? 0;
  return (
    <div className="rounded-xl bg-surface ring-1 ring-hairline">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-4 px-4 py-3 text-left hover:bg-raised/60"
        aria-expanded={open}
      >
        <span className="tnum w-6 shrink-0 text-[13px] font-semibold text-muted">{s.rank}</span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <span className="text-[14px] font-semibold">{s.creator_name}</span>
            <span className="text-[12px] text-muted">{s.handle}</span>
            {s.brand_safety_flag && (
              <Badge tone="critical" title={s.brand_safety_note}>
                ⚠ Safety review
              </Badge>
            )}
          </span>
          <span className="mt-0.5 block text-[12px] text-ink-2">
            {s.archetype} · {fmtCompact(s.subscribers)} subscribers ·{" "}
            {fmtUsd(s.estimated_cost_usd)} est.
          </span>
        </span>
        <span className="hidden w-44 shrink-0 text-right text-[12px] text-ink-2 sm:block">
          {delta <= -6 && (
            <span style={{ color: "var(--status-critical)" }}>
              ▼ {Math.abs(delta)} places worse on fit than reach
            </span>
          )}
          {delta >= 6 && (
            <span style={{ color: "var(--status-good)" }}>
              ▲ {delta} places better on fit than reach
            </span>
          )}
          {delta > -6 && delta < 6 && <span className="text-muted">{s.tier}</span>}
        </span>
        <span className="tnum w-14 shrink-0 text-right text-[20px] font-semibold">
          {s.composite.toFixed(0)}
        </span>
      </button>
      {open && (
        <div className="border-t px-4 py-4" style={{ borderColor: "var(--gridline)" }}>
          <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
            <div>
              <SectionLabel>Signal breakdown</SectionLabel>
              <SignalBars signals={s.signals} expanded />
            </div>
            <div className="space-y-3">
              <StatTile
                label="Audience sentiment"
                value={s.sentiment_positive_pct?.toFixed(0) ?? "—"}
                unit="% positive"
                note="Share of sampled comments reading positive"
              />
              <StatTile label="Rank by opportunity" value={`#${s.rank}`} note={s.headline} />
              <StatTile label="Rank by reach alone" value={`#${s.rank_by_reach}`} />
              {s.brand_safety_flag && (
                <div
                  className="rounded-lg px-3 py-2 text-[12px]"
                  style={{
                    background: "color-mix(in srgb, var(--status-critical) 10%, transparent)",
                    color: "var(--status-critical)",
                  }}
                >
                  <strong>Flagged:</strong> {s.brand_safety_note}. Excluded from the optimised
                  portfolio until a human clears it.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** Stage 03 — who can credibly own this opportunity? */
export function CreatorsPage() {
  const navigate = useNavigate();
  const { trendId, setTrendId } = useSelection();
  const id = trendId ?? DEFAULT_TREND;
  const [openId, setOpenId] = useState<string | null>(null);
  const [limit, setLimit] = useState(12);

  const { data, isLoading, error } = useQuery({
    queryKey: ["scores", id],
    queryFn: () => api.scores(id),
  });
  const portfolio = useQuery({
    queryKey: ["portfolio", id],
    queryFn: () => api.portfolio(id),
  });

  if (isLoading) return <Spinner label="Scoring creators against the trend" />;
  if (error || !data) return <ErrorNote error={error} />;

  const scores = data.scores;
  const top = scores[0];
  const biggest = [...scores].sort((a, b) => b.subscribers - a.subscribers)[0];
  const selectedIds = (portfolio.data?.optimized.members ?? []).map((m) => m.creator_id);

  return (
    <div className="space-y-5">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-widest text-muted">
          03 · Match
        </div>
        <h1 className="mt-1 text-2xl font-semibold">Creator Opportunity Score</h1>
        <p className="mt-1 max-w-3xl text-[14px] leading-snug text-ink-2">
          Every creator in the pool scored against{" "}
          <strong className="text-ink">{data.trend.name}</strong> on the five signals, weighted by
          the <code className="text-[12px]">{data.weights_version}</code> model. Each number carries
          its provenance and its evidence — expand a creator to interrogate it.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <StatTile
          label="Best positioned"
          value={top.creator_name}
          note={`${top.composite.toFixed(0)} · ${fmtCompact(top.subscribers)} subscribers`}
          tone="good"
        />
        <StatTile
          label="Largest channel"
          value={biggest.creator_name}
          note={`${fmtCompact(biggest.subscribers)} subscribers, but ranks #${biggest.rank} on fit`}
          tone="warning"
        />
        <StatTile
          label="Reach ≠ relevance"
          value={`${biggest.rank - 1} places`}
          note="Between the biggest channel and the best-positioned one"
        />
      </div>

      <Card
        title="Reach against relevance"
        subtitle="If audience size bought relevance this would slope upward. It does not — which is the whole argument."
      >
        <ReachRelevanceChart scores={scores} selectedIds={selectedIds} />
      </Card>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <SectionLabel>Ranked creators</SectionLabel>
          <span className="text-[12px] text-muted">
            showing {Math.min(limit, scores.length)} of {scores.length}
          </span>
        </div>
        <div className="space-y-2">
          {scores.slice(0, limit).map((s) => (
            <CreatorRow
              key={s.creator_id}
              s={s}
              open={openId === s.creator_id}
              onToggle={() => setOpenId(openId === s.creator_id ? null : s.creator_id)}
            />
          ))}
        </div>
        {limit < scores.length && (
          <button
            onClick={() => setLimit(scores.length)}
            className="mt-3 w-full rounded-md py-2 text-[13px] font-medium ring-1 ring-hairline hover:bg-raised"
          >
            Show all {scores.length} creators
          </button>
        )}
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => {
            setTrendId(id);
            navigate("/portfolio");
          }}
          className="rounded-md px-4 py-2 text-[13px] font-medium text-white"
          style={{ background: "var(--series-1)" }}
        >
          Build the portfolio →
        </button>
      </div>
    </div>
  );
}
