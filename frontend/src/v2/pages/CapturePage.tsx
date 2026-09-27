import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { fmtDuration } from "../../lib/format";
import { useSelection } from "../../state";
import { MomentumChart } from "../../components/charts/MomentumChart";
import {
  Answer,
  BigNumber,
  Card,
  Failed,
  Loading,
  NextStep,
  ShowWorking,
  Verdict,
} from "../ui";

const DEFAULT_TREND = "trend-social-running-clubs";

export function CapturePage() {
  const navigate = useNavigate();
  const { trendId, setTrendId } = useSelection();
  const id = trendId ?? DEFAULT_TREND;

  const scout = useQuery({ queryKey: ["scout"], queryFn: () => api.scout(undefined, 8) });
  const { data, isLoading, error } = useQuery({
    queryKey: ["capture", id],
    queryFn: () => api.capture(id),
  });

  if (isLoading) return <Loading label="Checking the timing" />;
  if (error || !data) return <Failed error={error} />;

  const w = data.window;
  const skip = w.verdict === "PASS";
  const days = Math.round(w.capture_window_days);

  return (
    <>
      <Answer
        eyebrow={data.trend.name}
        headline={
          skip ? (
            <>
              Skip this one. It closes{" "}
              <span style={{ color: "var(--verdict-pass)" }}>before you could launch.</span>
            </>
          ) : (
            <>
              Act on this one. You have{" "}
              <span style={{ color: "var(--status-good)" }}>{days} days.</span>
            </>
          )
        }
        sub={
          skip
            ? `This trend stops mattering in about ${Math.round(w.ttl_days)} days, and it takes you ${Math.round(w.activation_lead_days)} days to get live. The moment passes while the work is still in progress.`
            : `This trend stays relevant for about ${Math.round(w.ttl_days)} more days. Getting live takes you ${Math.round(w.activation_lead_days)} days. That leaves ${days} days you can actually use.`
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Verdict verdict={w.verdict} />
        <select
          value={id}
          onChange={(e) => setTrendId(e.target.value)}
          className="v2-pill bg-surface px-3 py-1.5 text-[13px] ring-1 ring-hairline"
          aria-label="Look at a different trend"
        >
          {(scout.data?.opportunities ?? []).map((o) => (
            <option key={o.trend.id} value={o.trend.id}>
              {o.trend.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <BigNumber
            value={skip ? "0" : days}
            unit="days"
            label="Left to act on this"
            tone={skip ? "pass" : "good"}
          />
        </Card>
        <Card>
          <BigNumber
            value={w.launch_within_hours ? fmtDuration(w.launch_within_hours) : "Passed"}
            label="To decide, if you want to land before the peak"
            tone={w.launch_within_hours ? "warning" : "pass"}
          />
        </Card>
      </div>

      <Card
        className="mt-4"
        title="Where this trend is headed"
        sub="Solid line is what has happened. Dashed is our forecast — the shaded band is the time you can actually use."
      >
        <MomentumChart
          observed={data.momentum}
          projection={data.projection}
          window={w}
          height={280}
          labels={{
            observed: "Interest so far",
            forecast: "Where it's going",
            threshold: "Still worth doing above this line",
            lead: "you're still building",
            window: "your window",
            closed: "already gone",
          }}
        />

        <ShowWorking label="How we worked this out">
          <p>{w.rationale}</p>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-muted">Stays relevant for</dt>
              <dd className="tnum font-medium">
                {w.ttl_days} days{" "}
                <span className="font-normal text-muted">
                  (could be {w.ttl_low_days}–{w.ttl_high_days})
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-muted">Your time to get live</dt>
              <dd className="tnum font-medium">{w.activation_lead_days} days</dd>
            </div>
            <div>
              <dt className="text-muted">Where it is in its life</dt>
              <dd className="font-medium capitalize">{w.stage}</dd>
            </div>
            <div>
              <dt className="text-muted">How confident we are</dt>
              <dd className="tnum font-medium">{Math.round(w.confidence * 100)}%</dd>
            </div>
          </dl>
          <p className="mt-4 text-muted">
            The curve is fitted to {data.momentum.length} daily readings of search interest
            (fit quality r² {w.fit_quality.toFixed(3)}).{" "}
            {w.method === "decay_from_prior"
              ? "This trend hasn't peaked yet, so how fast it will fade is an assumption based on similar trends, not something we can measure. We'd rather say so than hand you a confident number we didn't earn."
              : w.method === "decay_observed_shrunk"
                ? "It has started falling, but there isn't much decline to read yet, so the fade rate is part measured and part assumed."
                : w.method === "linear_fallback"
                  ? "The curve fit failed, so this is a rough straight-line estimate. Treat it as indicative."
                  : "It has already peaked, so how fast it is fading is measured directly from the data."}
          </p>
        </ShowWorking>
      </Card>

      <NextStep
        label={skip ? "Look at creators anyway" : "See who qualifies"}
        onClick={() => {
          setTrendId(id);
          navigate("/creators");
        }}
      />
    </>
  );
}
