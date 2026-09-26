import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { fmtDuration } from "../lib/format";
import { useSelection } from "../state";
import { CaptureWindowBar } from "../components/charts/CaptureWindowBar";
import { MomentumChart } from "../components/charts/MomentumChart";
import { Card, ErrorNote, Spinner, StatTile, VerdictPill } from "../components/ui";

const DEFAULT_TREND = "trend-social-running-clubs";

/** Stage 02 — is there still time? */
export function CapturePage() {
  const navigate = useNavigate();
  const { trendId, setTrendId } = useSelection();
  const id = trendId ?? DEFAULT_TREND;

  const scout = useQuery({ queryKey: ["scout"], queryFn: () => api.scout(undefined, 8) });
  const { data, isLoading, error } = useQuery({
    queryKey: ["capture", id],
    queryFn: () => api.capture(id),
  });

  if (isLoading) return <Spinner label="Fitting the momentum curve" />;
  if (error || !data) return <ErrorNote error={error} />;

  const w = data.window;
  const closed = w.verdict === "PASS";
  const supply = scout.data?.opportunities.find((o) => o.trend.id === id);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-widest text-muted">
            02 · Predict
          </div>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-semibold">
            {data.trend.name}
            <VerdictPill verdict={w.verdict} />
          </h1>
          <p className="mt-1 max-w-3xl text-[14px] leading-snug text-ink-2">{data.trend.why_now}</p>
        </div>
        <select
          value={id}
          onChange={(e) => setTrendId(e.target.value)}
          className="rounded-md bg-surface px-3 py-2 text-[13px] ring-1 ring-hairline"
          aria-label="Choose a trend"
        >
          {(scout.data?.opportunities ?? []).map((o) => (
            <option key={o.trend.id} value={o.trend.id}>
              {o.trend.name} — {o.window.verdict}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Capture window"
          value={w.capture_window_days}
          unit="days"
          size="lg"
          tone={closed ? "critical" : w.verdict === "MARGINAL" ? "warning" : "good"}
          note={closed ? "Closes before anything could ship" : "Usable time after activation lead"}
        />
        <StatTile
          label="Time to live"
          value={w.ttl_days}
          unit="days"
          note={`Confidence band ${w.ttl_low_days}–${w.ttl_high_days}d`}
        />
        <StatTile
          label={w.launch_within_hours ? "Commit within" : "Decision deadline"}
          value={w.launch_within_hours ? fmtDuration(w.launch_within_hours) : "passed"}
          tone={w.launch_within_hours ? "warning" : "critical"}
          note="To land content before the peak"
        />
        <StatTile
          label="Creator supply"
          value={supply ? supply.creator_supply_index.toFixed(0) : "—"}
          note={supply?.creator_supply_note}
        />
      </div>

      <Card
        title="Capture window = time-to-live − activation lead time"
        subtitle="A trend is only an opportunity if it outlives the brand's own process."
      >
        <CaptureWindowBar window={w} />
      </Card>

      <Card
        title="Momentum and forecast"
        subtitle={`Fitted from ${data.momentum.length} daily observations. The dashed line is the forecast, not a measurement.`}
      >
        <MomentumChart observed={data.momentum} projection={data.projection} window={w} />
      </Card>

      <Card title="How the engine reached this" subtitle="Method and its limits, stated.">
        <p className="text-[14px] leading-relaxed">{w.rationale}</p>
        <div className="mt-4 grid gap-3 text-[12px] sm:grid-cols-4">
          <div className="rounded-lg bg-raised px-3 py-2">
            <div className="text-muted">Lifecycle stage</div>
            <div className="mt-0.5 font-semibold capitalize">{w.stage}</div>
          </div>
          <div className="rounded-lg bg-raised px-3 py-2">
            <div className="text-muted">Curve fit quality</div>
            <div className="tnum mt-0.5 font-semibold">r² {w.fit_quality.toFixed(3)}</div>
          </div>
          <div className="rounded-lg bg-raised px-3 py-2">
            <div className="text-muted">Decay rate</div>
            <div className="mt-0.5 font-semibold">
              {w.method === "decay_observed"
                ? "measured"
                : w.method === "decay_observed_shrunk"
                  ? "part-measured"
                  : w.method === "linear_fallback"
                    ? "fallback"
                    : "assumed from prior"}
            </div>
          </div>
          <div className="rounded-lg bg-raised px-3 py-2">
            <div className="text-muted">Overall confidence</div>
            <div className="tnum mt-0.5 font-semibold">{(w.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      </Card>

      <div className="flex justify-end">
        <button
          onClick={() => {
            setTrendId(id);
            navigate("/creators");
          }}
          className="rounded-md px-4 py-2 text-[13px] font-medium text-white"
          style={{ background: closed ? "var(--text-muted)" : "var(--series-1)" }}
        >
          {closed ? "Score creators anyway →" : "Find creators who can own this →"}
        </button>
      </div>
    </div>
  );
}
