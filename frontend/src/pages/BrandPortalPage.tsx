import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { fmtDate, fmtInt, fmtPct, fmtUsd } from "../lib/format";
import { Card, ErrorNote, SectionLabel, Spinner, StatTile } from "../components/ui";

/** Stage 00 — the returning brand's own history, and what it implies for the
 *  campaign they are about to plan. */
export function BrandPortalPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["brand"], queryFn: api.brand });

  if (isLoading) return <Spinner label="Loading brand portal" />;
  if (error || !data) return <ErrorNote error={error} />;

  const { brand, insights, campaigns } = data;
  const lead = insights.activation_lead_days;
  const gettingFaster = lead.recent < lead.all_time;

  return (
    <div className="space-y-5">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-widest text-muted">
          Brand Portal
        </div>
        <h1 className="mt-1 text-2xl font-semibold">{brand.name}</h1>
        <p className="mt-1 max-w-2xl text-[14px] leading-snug text-ink-2">{brand.positioning}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Campaigns run" value={insights.campaigns_run} />
        <StatTile label="Total invested" value={fmtUsd(insights.total_spend_usd)} />
        <StatTile
          label="Mean performance"
          value={insights.mean_performance_index.toFixed(1)}
          note={`Average miss of ${insights.mean_prediction_error.toFixed(1)} points against forecast`}
        />
        <StatTile
          label="Activation lead time"
          value={lead.learned}
          unit="days"
          tone={gettingFaster ? "good" : "neutral"}
          note={
            gettingFaster
              ? `Down from ${lead.all_time}d all-time — fastest run was ${lead.fastest}d`
              : `All-time ${lead.all_time}d, fastest ${lead.fastest}d`
          }
        />
      </div>

      <Card
        title="What this brand's history implies"
        subtitle="These are the numbers the engine carries into the next campaign, not decoration."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          <div>
            <SectionLabel>Activation gap</SectionLabel>
            <p className="text-[13px] leading-snug text-ink-2">
              It takes <strong className="text-ink">{lead.learned} days</strong> to get live. Every
              opportunity is judged against that: a trend has to outlive the process before it is
              worth starting.
            </p>
            <Link
              to="/scout"
              className="mt-3 inline-block rounded-md px-3 py-1.5 text-[13px] font-medium text-white"
              style={{ background: "var(--series-1)" }}
            >
              Start a new campaign →
            </Link>
          </div>
          <div>
            <SectionLabel>Creator types that deliver</SectionLabel>
            <ul className="space-y-1.5">
              {insights.best_archetypes.slice(0, 4).map((a) => (
                <li key={a.archetype} className="flex items-baseline justify-between gap-3 text-[13px]">
                  <span className="min-w-0 truncate text-ink-2">{a.archetype}</span>
                  <span className="tnum shrink-0 font-semibold">{a.mean_index.toFixed(0)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <SectionLabel>Audience overlap</SectionLabel>
            <p className="text-[13px] leading-snug text-ink-2">{insights.overlap_finding}</p>
            <p className="mt-1.5 text-[12px] text-muted">
              Correlation between portfolio overlap and outcome:{" "}
              <span className="tnum">{insights.overlap_vs_performance_correlation.toFixed(2)}</span>
            </p>
          </div>
        </div>
      </Card>

      <Card
        title="Campaign history"
        subtitle="Predicted against delivered, for every campaign this brand has run through the engine."
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-[13px]">
            <thead>
              <tr className="text-[11px] uppercase tracking-wide text-muted">
                <th className="px-2 py-2 text-left font-semibold">Campaign</th>
                <th className="px-2 py-2 text-left font-semibold">Trend</th>
                <th className="px-2 py-2 text-right font-semibold">Spend</th>
                <th className="px-2 py-2 text-right font-semibold">Lead</th>
                <th className="px-2 py-2 text-right font-semibold">Overlap</th>
                <th className="px-2 py-2 text-right font-semibold">Predicted</th>
                <th className="px-2 py-2 text-right font-semibold">Actual</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => {
                const delta = c.actual.performance_index - c.predicted.performance_index;
                return (
                  <tr key={c.id} className="border-t align-top" style={{ borderColor: "var(--gridline)" }}>
                    <td className="px-2 py-2.5">
                      <div className="font-medium">{c.name}</div>
                      <div className="text-[11px] text-muted">{fmtDate(c.launched_at)}</div>
                      {c.learnings[0] && (
                        <div className="mt-1 max-w-sm text-[12px] leading-snug text-ink-2">
                          {c.learnings[0]}
                        </div>
                      )}
                    </td>
                    <td className="px-2 py-2.5 text-ink-2">{c.trend_name}</td>
                    <td className="tnum px-2 py-2.5 text-right">{fmtUsd(c.spend_usd)}</td>
                    <td className="tnum px-2 py-2.5 text-right">{c.activation_lead_days}d</td>
                    <td className="tnum px-2 py-2.5 text-right">{fmtPct(c.portfolio_overlap_pct)}</td>
                    <td className="tnum px-2 py-2.5 text-right text-ink-2">
                      {c.predicted.performance_index.toFixed(1)}
                    </td>
                    <td className="tnum px-2 py-2.5 text-right font-semibold">
                      {c.actual.performance_index.toFixed(1)}
                      <span
                        className="ml-1.5 text-[11px] font-medium"
                        style={{
                          color: delta >= 0 ? "var(--status-good)" : "var(--status-critical)",
                        }}
                      >
                        {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[12px] text-muted">
          Reach across all campaigns:{" "}
          <span className="tnum">
            {fmtInt(campaigns.reduce((s, c) => s + c.actual.reach, 0))}
          </span>{" "}
          people.
        </p>
      </Card>

      <Card title="Brand safety requirements" subtitle="Applied automatically during creator scoring.">
        <ul className="grid gap-2 text-[13px] text-ink-2 sm:grid-cols-3">
          {brand.brand_safety_requirements.map((r) => (
            <li key={r} className="rounded-lg bg-raised px-3 py-2">
              {r}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
