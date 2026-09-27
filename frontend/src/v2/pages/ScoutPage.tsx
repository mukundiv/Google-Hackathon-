import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, type Opportunity } from "../../lib/api";
import { fmtDuration } from "../../lib/format";
import { useSelection } from "../../state";
import { Answer, Bar, Card, Chip, Failed, Loading, ShowWorking, Verdict } from "../ui";

function TrendCard({ o, onOpen }: { o: Opportunity; onOpen: () => void }) {
  const w = o.window;
  const skip = w.verdict === "PASS";
  return (
    <button
      onClick={onOpen}
      className="flex w-full flex-col rounded-xl bg-surface p-4 text-left ring-1 ring-hairline transition-shadow hover:shadow-md"
      style={{ borderRadius: "var(--radius-card)", opacity: skip ? 0.85 : 1 }}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[16px] font-medium leading-snug">{o.trend.name}</h3>
        <Verdict verdict={w.verdict} size="sm" />
      </div>

      <p className="mt-2 line-clamp-3 text-[13px] leading-snug text-ink-2">
        {o.trend.description}
      </p>

      <div className="mt-3 flex items-baseline gap-2">
        <span
          className="text-[26px] font-bold leading-none"
          style={{ color: skip ? "var(--verdict-pass)" : "var(--status-good)" }}
        >
          {skip ? "—" : `${Math.round(w.capture_window_days)}`}
        </span>
        <span className="text-[13px] text-ink-2">
          {skip ? "already closed" : "days to act"}
        </span>
      </div>

      {!skip && w.launch_within_hours ? (
        <div className="mt-2 text-[12px]" style={{ color: "var(--status-warning)" }}>
          Decide within {fmtDuration(w.launch_within_hours)}
        </div>
      ) : null}

      <div className="mt-3">
        <div className="mb-1 flex justify-between text-[11px] text-muted">
          <span>How good this looks</span>
          <span className="tnum">{Math.round(o.strength)}/100</span>
        </div>
        <Bar
          value={o.strength}
          color={skip ? "var(--verdict-pass)" : "var(--series-1)"}
        />
      </div>
    </button>
  );
}

export function ScoutPage() {
  const navigate = useNavigate();
  const { setTrendId } = useSelection();
  const { data, isLoading, error } = useQuery({
    queryKey: ["scout"],
    queryFn: () => api.scout(undefined, 8),
  });

  if (isLoading) return <Loading label="Searching for what's emerging" />;
  if (error || !data) return <Failed error={error} />;

  const act = data.opportunities.filter((o) => o.window.verdict !== "PASS");
  const skip = data.opportunities.filter((o) => o.window.verdict === "PASS");
  const open = (id: string) => {
    setTrendId(id);
    navigate("/capture");
  };

  return (
    <>
      <Answer
        eyebrow="What's emerging"
        headline={
          <>
            <span style={{ color: "var(--status-good)" }}>{act.length} worth acting on.</span>{" "}
            {skip.length} to skip.
          </>
        }
        sub={`We searched the web for what's rising in ${data.brief.niche}, then checked each one against how fast you can move. Pick one to see the timing.`}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {act.map((o) => (
          <TrendCard key={o.trend.id} o={o} onOpen={() => open(o.trend.id)} />
        ))}
      </div>

      <h2 className="mb-3 mt-8 text-[15px] font-medium">
        Not worth it — these close before you could launch
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {skip.map((o) => (
          <TrendCard key={o.trend.id} o={o} onOpen={() => open(o.trend.id)} />
        ))}
      </div>

      <Card className="mt-6" title="Where these came from">
        <p className="text-[13px] leading-relaxed text-ink-2">
          Each trend was found by searching the open web, then measured against how much people
          are searching for it and how much content creators are already making about it. The
          sources behind every claim are listed here.
        </p>
        <ShowWorking label="See the sources and the numbers">
          <div className="space-y-5">
            {data.opportunities.map((o) => (
              <div key={o.trend.id}>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-[13px] font-medium">{o.trend.name}</h3>
                  <Chip tone="neutral">{o.window.stage}</Chip>
                  <Chip tone="neutral" title="How much content creators are making about it">
                    creator coverage {Math.round(o.creator_supply_index)}/100
                  </Chip>
                </div>
                <p className="mt-1 text-ink-2">{o.creator_supply_note}</p>
                {o.trend.citations.length > 0 && (
                  <ul className="mt-1.5 space-y-1">
                    {o.trend.citations.map((c) => (
                      <li key={c.url}>
                        <a
                          href={c.url}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="underline decoration-dotted underline-offset-2"
                          style={{ color: "var(--series-1)" }}
                        >
                          {c.title}
                        </a>
                        <span className="text-muted"> — {c.publisher}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </ShowWorking>
      </Card>
    </>
  );
}
