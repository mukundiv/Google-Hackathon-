import type { CaptureWindow } from "../../lib/api";
import { chartColors } from "../../lib/theme";

/** capture window = time-to-live − activation lead time, as one bar.
 *
 * The identity is the whole argument, so it is drawn rather than asserted:
 * the grey block is time the brand loses to its own process, the coloured
 * block is what is left to actually capture.
 */
export function CaptureWindowBar({ window: w }: { window: CaptureWindow }) {
  const c = chartColors();
  const total = Math.max(w.ttl_days, w.activation_lead_days) || 1;
  const leadPct = Math.min(100, (w.activation_lead_days / total) * 100);
  const windowPct = Math.max(0, Math.min(100, (w.capture_window_days / total) * 100));
  const closed = w.capture_window_days <= 0;

  return (
    <div>
      <div className="flex h-9 w-full overflow-hidden rounded-lg bg-raised" role="img"
        aria-label={`Time to live ${w.ttl_days} days, activation lead ${w.activation_lead_days} days, capture window ${w.capture_window_days} days`}>
        <div
          className="flex items-center justify-center text-[11px] font-semibold text-white"
          style={{ width: `${leadPct}%`, background: c.muted, marginRight: 2 }}
        >
          {leadPct > 16 && `${w.activation_lead_days}d lead`}
        </div>
        {closed ? (
          <div
            className="flex flex-1 items-center justify-center text-[11px] font-semibold"
            style={{
              background: `color-mix(in srgb, ${c.critical} 16%, transparent)`,
              color: c.critical,
            }}
          >
            window already closed
          </div>
        ) : (
          <>
            <div
              className="flex items-center justify-center text-[11px] font-semibold text-white"
              style={{ width: `${windowPct}%`, background: c.good }}
            >
              {windowPct > 20 && `${w.capture_window_days}d usable`}
            </div>
            <div className="flex-1" />
          </>
        )}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-[12px] text-ink-2">
        <span>
          <strong className="tnum text-ink">{w.ttl_days}d</strong> until the trend stops
          mattering
        </span>
        <span aria-hidden="true" className="text-muted">−</span>
        <span>
          <strong className="tnum text-ink">{w.activation_lead_days}d</strong> to get live
        </span>
        <span aria-hidden="true" className="text-muted">=</span>
        <span>
          <strong className="tnum" style={{ color: closed ? c.critical : c.good }}>
            {w.capture_window_days}d
          </strong>{" "}
          of capture window
        </span>
      </div>
    </div>
  );
}
