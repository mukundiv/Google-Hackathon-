import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type Opportunity } from "../lib/api";
import { fmtDuration } from "../lib/format";
import { useSelection } from "../state";
import { ErrorNote, Meter, SectionLabel, Spinner, VerdictPill } from "../components/ui";

/** Stage 01 — Gemini scouts the live web for what is emerging in the niche.
 *
 * Citations are shown on every card: Google's Search-grounding terms require
 * it, and a trend claim without a source is not worth acting on anyway.
 */
function TrendCard({ o, onOpen }: { o: Opportunity; onOpen: () => void }) {
  const w = o.window;
  const closed = w.verdict === "PASS";
  return (
    <article
      className="flex flex-col rounded-xl bg-surface p-4 ring-1 ring-hairline transition-shadow hover:shadow-md"
      style={{ opacity: closed ? 0.82 : 1 }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-[15px] font-semibold leading-tight">{o.trend.name}</h3>
          <div className="mt-0.5 text-[11px] uppercase tracking-wide text-muted">
            {w.stage} · {o.trend.category.replace(/_/g, " ")}
          </div>
        </div>
        <VerdictPill verdict={w.verdict} size="sm" />
      </div>

      <p className="mt-2 text-[13px] leading-snug text-ink-2">{o.trend.description}</p>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-raised py-2">
          <div className="tnum text-[17px] font-semibold" style={{ color: closed ? "var(--status-critical)" : "var(--status-good)" }}>
            {w.capture_window_days}d
          </div>
          <div className="text-[10px] uppercase tracking-wide text-muted">window</div>
        </div>
        <div className="rounded-lg bg-raised py-2">
          <div className="tnum text-[17px] font-semibold">{w.current_momentum.toFixed(0)}</div>
          <div className="text-[10px] uppercase tracking-wide text-muted">momentum</div>
        </div>
        <div className="rounded-lg bg-raised py-2">
          <div className="tnum text-[17px] font-semibold">{o.creator_supply_index.toFixed(0)}</div>
          <div className="text-[10px] uppercase tracking-wide text-muted">supply</div>
        </div>
      </div>

      <div className="mt-3">
        <div className="mb-1 flex items-baseline justify-between text-[11px] text-muted">
          <span>Opportunity strength</span>
          <span className="tnum font-semibold text-ink-2">{o.strength.toFixed(0)}/100</span>
        </div>
        <Meter value={o.strength} />
      </div>

      {w.launch_within_hours ? (
        <div className="mt-3 rounded-lg px-3 py-2 text-[12px]" style={{ background: "color-mix(in srgb, var(--status-warning) 12%, transparent)" }}>
          <strong>Commit within {fmtDuration(w.launch_within_hours)}</strong> to land content
          before the peak.
        </div>
      ) : null}

      {o.trend.citations.length > 0 && (
        <details className="mt-3 text-[12px]">
          <summary className="cursor-pointer text-muted hover:text-ink-2">
            {o.trend.citations.length} source{o.trend.citations.length > 1 ? "s" : ""}
          </summary>
          <ul className="mt-2 space-y-2">
            {o.trend.citations.map((cit) => (
              <li key={cit.url}>
                <a
                  href={cit.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="font-medium underline decoration-dotted underline-offset-2"
                  style={{ color: "var(--series-1)" }}
                >
                  {cit.title}
                </a>
                <div className="text-[11px] text-muted">{cit.publisher}</div>
                {cit.snippet && (
                  <p className="mt-0.5 leading-snug text-ink-2">{cit.snippet}</p>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}

      <button
        onClick={onOpen}
        className="mt-3 w-full rounded-md py-2 text-[13px] font-medium ring-1 ring-hairline hover:bg-raised"
      >
        Examine capture window →
      </button>
    </article>
  );
}

export function ScoutPage() {
  const navigate = useNavigate();
  const { setTrendId } = useSelection();
  const { data, isLoading, error } = useQuery({
    queryKey: ["scout"],
    queryFn: () => api.scout(undefined, 8),
  });

  if (isLoading) return <Spinner label="Gemini is scouting the niche" />;
  if (error || !data) return <ErrorNote error={error} />;

  const actionable = data.opportunities.filter((o) => o.window.verdict !== "PASS");
  const rejected = data.opportunities.filter((o) => o.window.verdict === "PASS");

  const open = (id: string) => {
    setTrendId(id);
    navigate("/capture");
  };

  return (
    <div className="space-y-5">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-widest text-muted">
          01 · Listen
        </div>
        <h1 className="mt-1 text-2xl font-semibold">Trend Scout</h1>
        <p className="mt-1 max-w-3xl text-[14px] leading-snug text-ink-2">
          Gemini searches the open web for what is emerging in{" "}
          <strong className="text-ink">{data.brief.niche}</strong> for{" "}
          {data.brief.audience.genders.join("/")} {data.brief.audience.age_min}–
          {data.brief.audience.age_max} in {data.brief.audience.geos.join("/")}. Each candidate is
          then measured against search momentum and YouTube publishing velocity, and judged against
          this brand's {data.activation_lead_days}-day activation lead time.
        </p>
      </div>

      <div>
        <SectionLabel>Actionable now — {actionable.length}</SectionLabel>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {actionable.map((o) => (
            <TrendCard key={o.trend.id} o={o} onOpen={() => open(o.trend.id)} />
          ))}
        </div>
      </div>

      {rejected.length > 0 && (
        <div>
          <SectionLabel>Rejected — the moment passes before this brand could ship</SectionLabel>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {rejected.map((o) => (
              <TrendCard key={o.trend.id} o={o} onOpen={() => open(o.trend.id)} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
