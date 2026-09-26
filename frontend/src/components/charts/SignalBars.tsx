import type { SignalScore } from "../../lib/api";
import { chartColors } from "../../lib/theme";
import { ProvenanceTag } from "../ui";

/** The five signals behind one creator's score.
 *
 * One measure across five named categories, so a plain bar per row with the
 * value direct-labelled beats any chart library here — and it leaves room for
 * the provenance tag and rationale that make the number interrogable.
 */
export function SignalBars({
  signals,
  expanded = false,
}: {
  signals: SignalScore[];
  expanded?: boolean;
}) {
  const c = chartColors();
  return (
    <div className="space-y-2.5">
      {signals.map((s) => (
        <div key={s.name}>
          <div className="flex items-baseline justify-between gap-2">
            <div className="flex items-center gap-2 text-[12px]">
              <span className="font-medium">{s.label}</span>
              <ProvenanceTag provenance={s.provenance} />
              <span className="text-[11px] text-muted">
                weight {(s.weight * 100).toFixed(0)}%
              </span>
            </div>
            <span className="tnum text-[13px] font-semibold">{s.score.toFixed(0)}</span>
          </div>
          <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-raised">
            <div
              style={{
                width: `${Math.max(0, Math.min(100, s.score))}%`,
                height: "100%",
                background: c.series1,
                borderRadius: 4,
              }}
            />
          </div>
          {expanded && (
            <div className="mt-1.5 text-[12px] leading-snug text-ink-2">
              {s.rationale}
              {s.evidence.length > 0 && (
                <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px] text-muted">
                  {s.evidence.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
