import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type CreatorScore } from "../../lib/api";
import { fmtCompact, fmtUsd } from "../../lib/format";
import { useSelection } from "../../state";
import { ReachRelevanceChart } from "../../components/charts/ReachRelevanceChart";
import {
  Answer,
  Bar,
  Card,
  Chip,
  DataSource,
  Failed,
  Loading,
  NextStep,
  PillButton,
  ShowWorking,
} from "../ui";

const DEFAULT_TREND = "trend-social-running-clubs";

/** The engine's signal names, said the way a marketer would say them. */
const SIGNAL_LABEL: Record<string, string> = {
  content_fit: "Already covers this",
  audience_fit: "Right audience",
  brand_fit: "Suits your brand",
  momentum: "Growing on this topic",
  proven_performance: "Past results with you",
};

function initials(name: string) {
  return name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function CreatorCard({ s, rank }: { s: CreatorScore; rank: number }) {
  const [open, setOpen] = useState(false);
  const lost = (s.reach_relevance_delta ?? 0) <= -6;
  return (
    <div className="rounded-xl bg-surface ring-1 ring-hairline" style={{ borderRadius: "var(--radius-card)" }}>
      <div className="flex items-start gap-3 p-4">
        <span
          aria-hidden="true"
          className="grid h-11 w-11 shrink-0 place-items-center rounded-full text-[14px] font-medium"
          style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}
        >
          {initials(s.creator_name)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[15px] font-medium">{s.creator_name}</span>
            {rank === 1 && <Chip tone="brand">Best fit</Chip>}
            {s.brand_safety_flag && (
              <Chip tone="warning" title={s.brand_safety_note}>
                Needs a safety check
              </Chip>
            )}
          </div>
          <div className="mt-0.5 text-[12px] text-muted">
            {s.archetype} · {fmtCompact(s.subscribers)} subscribers · about{" "}
            {fmtUsd(s.estimated_cost_usd)}
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-[26px] font-bold leading-none">{Math.round(s.composite)}</div>
          <div className="text-[11px] text-muted">out of 100</div>
        </div>
      </div>

      {lost && (
        <div className="px-4 pb-3 text-[12px]" style={{ color: "var(--text-secondary)" }}>
          Huge channel, wrong fit — {Math.abs(s.reach_relevance_delta ?? 0)} places worse on fit
          than on size alone.
        </div>
      )}

      <div className="px-4 pb-4">
        <button
          onClick={() => setOpen((v) => !v)}
          className="text-[13px] font-medium"
          style={{ color: "var(--series-1)" }}
          aria-expanded={open}
        >
          {open ? "Hide the breakdown" : "Why this score?"}
        </button>

        {open && (
          <div className="mt-3 space-y-3">
            {s.signals.map((sig) => (
              <div key={sig.name}>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="flex items-center gap-2 text-[13px]">
                    {SIGNAL_LABEL[sig.name] ?? sig.label}
                    <DataSource provenance={sig.provenance} />
                  </span>
                  <span className="tnum text-[13px] font-medium">{Math.round(sig.score)}</span>
                </div>
                <div className="mt-1">
                  <Bar value={sig.score} />
                </div>
                <p className="mt-1 text-[12px] leading-snug text-ink-2">{sig.rationale}</p>
                {sig.evidence.length > 0 && (
                  <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px] text-muted">
                    {sig.evidence.slice(0, 3).map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
            {s.sentiment_positive_pct != null && (
              <p className="text-[12px] text-ink-2">
                <strong className="font-medium">
                  {Math.round(s.sentiment_positive_pct)}% of their comments read positive.
                </strong>{" "}
                Sampled from their most recent video.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function CreatorsPage() {
  const navigate = useNavigate();
  const { trendId, setTrendId } = useSelection();
  const id = trendId ?? DEFAULT_TREND;
  const [showAll, setShowAll] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["scores", id],
    queryFn: () => api.scores(id),
  });
  const portfolio = useQuery({ queryKey: ["portfolio", id], queryFn: () => api.portfolio(id) });

  if (isLoading) return <Loading label="Scoring creators" />;
  if (error || !data) return <Failed error={error} />;

  const scores = data.scores;
  const top = scores[0];
  const biggest = [...scores].sort((a, b) => b.subscribers - a.subscribers)[0];
  const shown = showAll ? scores : scores.slice(0, 5);
  const chosen = (portfolio.data?.optimized.members ?? []).map((m) => m.creator_id);

  return (
    <>
      <Answer
        eyebrow="Who to back"
        headline={
          <>
            Back <span style={{ color: "var(--brand)" }}>{top.creator_name}</span> — not the one
            with {fmtCompact(biggest.subscribers)} subscribers.
          </>
        }
        sub={`${top.creator_name} has ${fmtCompact(top.subscribers)} subscribers and scores ${Math.round(top.composite)}. The biggest channel in the pool has ${fmtCompact(biggest.subscribers)} and comes ${biggest.rank}th, because size is not the same thing as being the right person to talk about this.`}
      />

      <div className="space-y-3">
        {shown.map((s) => (
          <CreatorCard key={s.creator_id} s={s} rank={s.rank} />
        ))}
      </div>

      {!showAll && (
        <div className="mt-4">
          <PillButton variant="quiet" full onClick={() => setShowAll(true)}>
            See all {scores.length} creators
          </PillButton>
        </div>
      )}

      <Card
        className="mt-6"
        title="Size doesn't buy relevance"
        sub="If bigger channels were better for this trend, these dots would climb to the right. They don't."
      >
        <ReachRelevanceChart scores={scores} selectedIds={chosen} height={260} />

        <ShowWorking label="How the score is built">
          <p>
            Five signals, each scored out of 100 and weighted into one number. Every signal shows
            where it came from: <strong>confirmed by the creator</strong> means it came from that
            channel owner's own YouTube Analytics, <strong>measured</strong> means we counted it
            from public data, and <strong>our estimate</strong> means we inferred it and nobody has
            confirmed it.
          </p>
          <ul className="mt-3 space-y-1.5">
            {Object.entries(data.weights).map(([k, v]) => (
              <li key={k} className="flex justify-between gap-3">
                <span className="text-ink-2">{SIGNAL_LABEL[k] ?? k}</span>
                <span className="tnum font-medium">{(v * 100).toFixed(0)}% of the score</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-muted">
            Those weights are not fixed — they are re-learned from your campaign results. That is
            the last step in this tool.
          </p>
        </ShowWorking>
      </Card>

      <NextStep
        label="See where the money goes"
        onClick={() => {
          setTrendId(id);
          navigate("/portfolio");
        }}
      />
    </>
  );
}
