import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { WeightDeltaChart } from "../../components/charts/LearningCharts";
import {
  Answer,
  BigNumber,
  Card,
  Failed,
  Loading,
  PillButton,
  ShowWorking,
} from "../ui";

const SIGNAL_LABEL: Record<string, string> = {
  content_fit: "Already covers this",
  audience_fit: "Right audience",
  brand_fit: "Suits your brand",
  momentum: "Growing on this topic",
  proven_performance: "Past results with you",
};

/** The same signals as noun phrases, for running inside a sentence. The label
 *  versions are written to sit in a table column and read as nonsense mid-clause
 *  ("we now trust already covers this more than suits your brand"). */
const SIGNAL_PHRASE: Record<string, string> = {
  content_fit: "whether a creator already covers the topic",
  audience_fit: "whether they have the right audience",
  brand_fit: "whether they suit the brand",
  momentum: "whether they are growing on the topic",
  proven_performance: "how they performed for you before",
};

/** A plausible result for the campaign this tool just recommended, so the loop
 *  can be closed live instead of waiting weeks for real data. */
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
  learnings: ["Community creators with no prior brand history outperformed repeat partners."],
};

export function LearningPage() {
  const qc = useQueryClient();
  const [busy, setBusy] = useState<string | null>(null);
  const { data, isLoading, error } = useQuery({ queryKey: ["learning"], queryFn: api.learning });

  const refresh = () =>
    Promise.all(
      ["learning", "scores", "portfolio", "scout", "brand", "health"].map((k) =>
        qc.invalidateQueries({ queryKey: [k] }),
      ),
    );

  const observe = useMutation({
    mutationFn: () => api.observe(SAMPLE_RESULT),
    onMutate: () => setBusy("observe"),
    onSettled: async () => {
      await refresh();
      setBusy(null);
    },
  });
  const apply = useMutation({
    mutationFn: api.applyLearning,
    onMutate: () => setBusy("apply"),
    onSettled: async () => {
      await refresh();
      setBusy(null);
    },
  });
  const reset = useMutation({
    mutationFn: api.resetLearning,
    onMutate: () => setBusy("reset"),
    onSettled: async () => {
      await refresh();
      setBusy(null);
    },
  });
  if (isLoading) return <Loading label="Reading your campaign history" />;
  if (error || !data) return <Failed error={error} />;

  const up = [...data.calibration].filter((c) => c.weight_after > c.weight_before);
  const down = [...data.calibration].filter((c) => c.weight_after < c.weight_before);
  const biggestUp = up.sort((a, b) => b.weight_after - b.weight_before - (a.weight_after - a.weight_before))[0];
  const biggestDown = down.sort((a, b) => a.weight_after - a.weight_before - (b.weight_after - b.weight_before))[0];

  return (
    <>
      <Answer
        eyebrow="What we learned"
        headline={
          biggestUp && biggestDown ? (
            <>
              We now weigh{" "}
              <span style={{ color: "var(--brand)" }}>
                {SIGNAL_PHRASE[biggestUp.signal] ?? biggestUp.label.toLowerCase()}
              </span>{" "}
              more heavily than{" "}
              {SIGNAL_PHRASE[biggestDown.signal] ?? biggestDown.label.toLowerCase()}.
            </>
          ) : (
            "Not enough campaigns yet to change anything."
          )
        }
        sub={`Your ${data.campaigns_learned_from} campaigns tell us which signals actually predicted results. The ones that did get more say in the score; the ones that didn't get less. Every new campaign nudges it again.`}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <BigNumber value={data.campaigns_learned_from} label="Campaigns learned from" />
        </Card>
        <Card>
          <BigNumber
            value={data.activation_lead_days}
            unit="days"
            label="Your launch speed, re-learned"
          />
        </Card>
        <Card>
          <BigNumber
            value={data.pending_change ? "Ready" : "In use"}
            label={data.pending_change ? "A better weighting is waiting" : "Latest weighting applied"}
            tone={data.pending_change ? "warning" : "good"}
          />
        </Card>
      </div>

      <Card className="mt-4" title="Try it" sub="Feed in a result and watch the model change.">
        <div className="flex flex-wrap gap-2">
          <PillButton onClick={() => observe.mutate()} disabled={busy !== null}>
            {busy === "observe" ? "Adding…" : "Add a campaign result"}
          </PillButton>
          <PillButton
            variant="quiet"
            onClick={() => apply.mutate()}
            disabled={busy !== null || !data.pending_change}
          >
            {busy === "apply" ? "Applying…" : "Use the new weighting"}
          </PillButton>
          <PillButton variant="quiet" onClick={() => reset.mutate()} disabled={busy !== null}>
            Start over
          </PillButton>
        </div>
        <p className="mt-3 text-[13px] leading-snug text-ink-2">
          After applying, go back to <strong>Who qualifies</strong> — the ranking will have moved.
          That is the point: the scores are not a fixed formula, they are what your own results
          taught us.
        </p>
      </Card>

      <Card className="mt-4" title="What changed" sub="How much say each signal now has.">
        <WeightDeltaChart calibration={data.calibration} height={210} />

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="mb-2 text-[13px] font-medium" style={{ color: "var(--series-1)" }}>
              Trusted more
            </h3>
            <ul className="space-y-1.5 text-[13px]">
              {up.map((c) => (
                <li key={c.signal} className="flex justify-between gap-3">
                  <span className="text-ink-2">{SIGNAL_LABEL[c.signal] ?? c.label}</span>
                  <span className="tnum font-medium">
                    +{((c.weight_after - c.weight_before) * 100).toFixed(1)} pts
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="mb-2 text-[13px] font-medium" style={{ color: "var(--series-2)" }}>
              Trusted less
            </h3>
            <ul className="space-y-1.5 text-[13px]">
              {down.map((c) => (
                <li key={c.signal} className="flex justify-between gap-3">
                  <span className="text-ink-2">{SIGNAL_LABEL[c.signal] ?? c.label}</span>
                  <span className="tnum font-medium">
                    {((c.weight_after - c.weight_before) * 100).toFixed(1)} pts
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <ShowWorking label="How the re-weighting works">
          <p>{data.summary}</p>
          <p className="mt-3">{data.current.note}</p>
          <table className="mt-4 w-full text-[12px]">
            <thead>
              <tr className="text-muted">
                <th className="py-1.5 text-left font-medium">Signal</th>
                <th className="py-1.5 text-right font-medium">Say before</th>
                <th className="py-1.5 text-right font-medium">Say now</th>
                <th className="py-1.5 text-right font-medium">How well it predicted</th>
              </tr>
            </thead>
            <tbody>
              {data.calibration.map((c) => (
                <tr key={c.signal} className="border-t" style={{ borderColor: "var(--gridline)" }}>
                  <td className="py-1.5">{SIGNAL_LABEL[c.signal] ?? c.label}</td>
                  <td className="tnum py-1.5 text-right">{(c.weight_before * 100).toFixed(1)}%</td>
                  <td className="tnum py-1.5 text-right">{(c.weight_after * 100).toFixed(1)}%</td>
                  <td className="tnum py-1.5 text-right">
                    {c.correlation_with_outcome.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-muted">
            The last column is how closely each signal tracked what campaigns actually delivered,
            from −1 to 1. With only {data.campaigns_learned_from} campaigns the new weighting is
            deliberately blended with the starting one, so a short history nudges the model
            rather than rewriting it.
          </p>
        </ShowWorking>
      </Card>
    </>
  );
}
