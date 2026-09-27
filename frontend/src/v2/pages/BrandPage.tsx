import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { fmtDate, fmtUsd } from "../../lib/format";
import { Answer, BigNumber, Card, Failed, Loading, NextStep, ShowWorking } from "../ui";

export function BrandPage() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery({ queryKey: ["brand"], queryFn: api.brand });

  if (isLoading) return <Loading label="Opening your account" />;
  if (error || !data) return <Failed error={error} />;

  const { brand, insights, campaigns } = data;
  const lead = insights.activation_lead_days;
  const faster = lead.recent < lead.all_time;
  const recent = [...campaigns].sort((a, b) => b.launched_at.localeCompare(a.launched_at)).slice(0, 4);

  return (
    <>
      <Answer
        eyebrow={brand.name}
        headline={
          <>
            You take{" "}
            <span style={{ color: "var(--brand)" }}>{Math.round(lead.learned)} days</span> to get a
            campaign live.
          </>
        }
        sub="Everything this tool recommends is judged against that number. A trend has to outlast your own process to be worth starting — otherwise the moment passes while the work is still in approvals."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <BigNumber
            value={Math.round(lead.learned)}
            unit="days"
            label="From spotting something to being live"
            tone={faster ? "good" : "neutral"}
          />
          {faster && (
            <p className="mt-2 text-[12px]" style={{ color: "var(--status-good)" }}>
              ▲ Getting faster — your last four averaged {Math.round(lead.recent)}d
            </p>
          )}
        </Card>
        <Card>
          <BigNumber value={insights.campaigns_run} label="Campaigns run through the engine" />
        </Card>
        <Card>
          <BigNumber value={fmtUsd(insights.total_spend_usd)} label="Invested so far" />
        </Card>
      </div>

      <Card className="mt-4" title="Your last four campaigns" sub="Did they beat what we predicted?">
        <ul className="divide-y" style={{ borderColor: "var(--gridline)" }}>
          {recent.map((c) => {
            const delta = c.actual.performance_index - c.predicted.performance_index;
            const beat = delta >= 0;
            return (
              <li key={c.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3">
                <div className="min-w-0 flex-1">
                  <div className="text-[14px] font-medium">{c.name}</div>
                  <div className="text-[12px] text-muted">
                    {c.trend_name} · {fmtDate(c.launched_at)} · {fmtUsd(c.spend_usd)}
                  </div>
                </div>
                <div
                  className="text-[13px] font-medium"
                  style={{ color: beat ? "var(--status-good)" : "var(--text-secondary)" }}
                >
                  {beat ? "▲ Beat forecast" : "▼ Under forecast"} by {Math.abs(delta).toFixed(0)}
                </div>
              </li>
            );
          })}
        </ul>

        <ShowWorking label="What your history tells the engine">
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <h3 className="mb-2 text-[13px] font-medium">Creator types that deliver for you</h3>
              <ul className="space-y-1">
                {insights.best_archetypes.slice(0, 4).map((a) => (
                  <li key={a.archetype} className="flex justify-between gap-3 text-ink-2">
                    <span className="min-w-0 truncate">{a.archetype}</span>
                    <span className="tnum shrink-0 font-medium text-ink">
                      {a.mean_index.toFixed(0)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-2 text-[13px] font-medium">Wasted double-reach</h3>
              <p className="text-ink-2">{insights.overlap_finding}</p>
              <p className="mt-2 text-muted">
                Correlation between how much your creators' audiences overlapped and how the
                campaign performed:{" "}
                <span className="tnum">
                  {insights.overlap_vs_performance_correlation.toFixed(2)}
                </span>
                . Negative means overlap hurt.
              </p>
              <p className="mt-3 text-muted">
                Across all {insights.campaigns_run} campaigns our forecasts were off by an average
                of {insights.mean_prediction_error.toFixed(1)} points. Activation lead has ranged
                from {lead.fastest}d to {lead.all_time.toFixed(0)}d on average.
              </p>
            </div>
          </div>
          <div className="mt-4">
            <h3 className="mb-2 text-[13px] font-medium">Your brand safety rules</h3>
            <ul className="flex flex-wrap gap-2">
              {brand.brand_safety_requirements.map((r) => (
                <li key={r} className="v2-pill bg-surface px-3 py-1 text-[12px] text-ink-2 ring-1 ring-hairline">
                  {r}
                </li>
              ))}
            </ul>
            <p className="mt-2 text-muted">
              Creators whose content breaks these are held back from any recommendation until
              someone clears them.
            </p>
          </div>
        </ShowWorking>
      </Card>

      <NextStep label="See what's emerging" onClick={() => navigate("/scout")} />
    </>
  );
}
