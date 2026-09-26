import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { PredictionTrendChart, WeightDeltaChart } from "../components/charts/LearningCharts";
import { Card, ErrorNote, SectionLabel, Spinner, StatTile } from "../components/ui";

/** A plausible result for the campaign the console just recommended, so the
 *  loop can be closed live in a demo without waiting weeks for real data. */
const SAMPLE_RESULT = {
  name: "Run Club Activation",
  trend_name: "Social Running Clubs",
  trend_category: "community_behaviour",
  spend_usd: 249_000,
  activation_lead_days: 6.5,
  signal_snapshot: {
    content_fit: 95,
    audience_fit: 91,
    brand_fit: 88,
    momentum: 93,
    proven_performance: 52,
  },
  predicted: { performance_index: 84.0, reach: 720_000, views: 1_150_000 },
  actual: { performance_index: 91.5, reach: 806_000, views: 1_310_000 },
  portfolio_overlap_pct: 16.9,
  learnings: [
    "Community creators with no prior brand history outperformed repeat partners again.",
    "The optimised mix held overlap under 20% and beat the forecast.",
  ],
};

/** Stage 05 — results come back and the model changes. */
export function LearningPage() {
  const qc = useQueryClient();
  const [busy, setBusy] = useState<string | null>(null);
  const { data, isLoading, error } = useQuery({ queryKey: ["learning"], queryFn: api.learning });

  const invalidate = () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: ["learning"] }),
      qc.invalidateQueries({ queryKey: ["scores"] }),
      qc.invalidateQueries({ queryKey: ["portfolio"] }),
      qc.invalidateQueries({ queryKey: ["scout"] }),
      qc.invalidateQueries({ queryKey: ["brand"] }),
      qc.invalidateQueries({ queryKey: ["health"] }),
    ]);

  const observe = useMutation({
    mutationFn: () => api.observe(SAMPLE_RESULT),
    onMutate: () => setBusy("observe"),
    onSettled: async () => {
      await invalidate();
      setBusy(null);
    },
  });
  const apply = useMutation({
    mutationFn: api.applyLearning,
    onMutate: () => setBusy("apply"),
    onSettled: async () => {
      await invalidate();
      setBusy(null);
    },
  });
  const reset = useMutation({
    mutationFn: api.resetLearning,
    onMutate: () => setBusy("reset"),
    onSettled: async () => {
      await invalidate();
      setBusy(null);
    },
  });

  if (isLoading) return <Spinner label="Reading the ledger" />;
  if (error || !data) return <ErrorNote error={error} />;

  const up = data.calibration.filter((c) => c.weight_after > c.weight_before);
  const down = data.calibration.filter((c) => c.weight_after < c.weight_before);

  return (
    <div className="space-y-5">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-widest text-muted">
          05 · Learn
        </div>
        <h1 className="mt-1 text-2xl font-semibold">Learning Loop</h1>
        <p className="mt-1 max-w-3xl text-[14px] leading-snug text-ink-2">
          Predict → activate → observe → learn. Campaign results are regressed against the signal
          profile that produced them, and the Creator Opportunity Score is re-weighted. With a short
          ledger the fit is deliberately blended with the prior — {data.campaigns_learned_from}{" "}
          campaigns should move the model, not rewrite it.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Campaigns learned from" value={data.campaigns_learned_from} />
        <StatTile
          label="Weights in use"
          value={data.applied_version}
          tone={data.pending_change ? "warning" : "neutral"}
          note={data.pending_change ? "A newer weighting is available" : "Current"}
        />
        <StatTile
          label="Learned activation lead"
          value={data.activation_lead_days}
          unit="days"
          note="Feeds straight back into every capture window"
        />
        <StatTile
          label="Mean prediction error"
          value={
            data.prediction_error_trend.length
              ? (
                  data.prediction_error_trend.reduce((s, r) => s + r.abs_error, 0) /
                  data.prediction_error_trend.length
                ).toFixed(1)
              : "—"
          }
          unit="pts"
        />
      </div>

      <Card
        title="What the engine learned"
        subtitle={data.summary}
        actions={
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => observe.mutate()}
              disabled={busy !== null}
              className="rounded-md px-3 py-1.5 text-[12px] font-medium text-white disabled:opacity-50"
              style={{ background: "var(--series-1)" }}
            >
              {busy === "observe" ? "Feeding back…" : "Feed back a campaign result"}
            </button>
            <button
              onClick={() => apply.mutate()}
              disabled={busy !== null || !data.pending_change}
              className="rounded-md px-3 py-1.5 text-[12px] font-medium ring-1 ring-hairline disabled:opacity-40"
            >
              {busy === "apply" ? "Applying…" : "Apply new weights"}
            </button>
            <button
              onClick={() => reset.mutate()}
              disabled={busy !== null}
              className="rounded-md px-3 py-1.5 text-[12px] font-medium text-ink-2 ring-1 ring-hairline disabled:opacity-40"
            >
              Reset
            </button>
          </div>
        }
      >
        <div className="grid gap-5 lg:grid-cols-2">
          <div>
            <SectionLabel>Weight change per signal</SectionLabel>
            <WeightDeltaChart calibration={data.calibration} />
          </div>
          <div>
            <SectionLabel>Predicted against delivered</SectionLabel>
            <PredictionTrendChart state={data} />
          </div>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Signals that earned more weight">
          {up.length === 0 ? (
            <p className="text-[13px] text-ink-2">No signal gained weight yet.</p>
          ) : (
            <ul className="space-y-2.5">
              {up.map((c) => (
                <li key={c.signal}>
                  <div className="flex items-baseline justify-between text-[13px]">
                    <span className="font-medium">{c.label}</span>
                    <span className="tnum font-semibold" style={{ color: "var(--series-1)" }}>
                      +{((c.weight_after - c.weight_before) * 100).toFixed(1)} pts
                    </span>
                  </div>
                  <p className="mt-0.5 text-[12px] leading-snug text-ink-2">
                    Correlated {c.correlation_with_outcome.toFixed(2)} with what campaigns actually
                    delivered, across {c.samples} campaigns.
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Signals that lost weight">
          {down.length === 0 ? (
            <p className="text-[13px] text-ink-2">No signal lost weight yet.</p>
          ) : (
            <ul className="space-y-2.5">
              {down.map((c) => (
                <li key={c.signal}>
                  <div className="flex items-baseline justify-between text-[13px]">
                    <span className="font-medium">{c.label}</span>
                    <span className="tnum font-semibold" style={{ color: "var(--status-critical)" }}>
                      {((c.weight_after - c.weight_before) * 100).toFixed(1)} pts
                    </span>
                  </div>
                  <p className="mt-0.5 text-[12px] leading-snug text-ink-2">
                    Correlated {c.correlation_with_outcome.toFixed(2)} with delivered performance —
                    it was carrying more weight than it earned.
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card
        title="Current weighting"
        subtitle={data.current.note}
      >
        <div className="grid gap-2 sm:grid-cols-5">
          {Object.entries(data.current.weights).map(([k, v]) => (
            <div key={k} className="rounded-lg bg-raised px-3 py-2">
              <div className="text-[11px] capitalize text-muted">{k.replace(/_/g, " ")}</div>
              <div className="tnum mt-0.5 text-[17px] font-semibold">{(v * 100).toFixed(1)}%</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
