import { useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CaptureWindow, MomentumPoint } from "../../lib/api";
import { fmtShortDate } from "../../lib/format";
import { chartColors } from "../../lib/theme";
import { DataTable, Legend, TableToggle } from "../ui";

/** The Capture Window, drawn.
 *
 * Observed momentum runs to today; the fitted curve continues past it. The two
 * are the same measure at different levels of certainty, so they share a hue
 * and separate by dash — the forecast must not look like a measurement.
 */
export function MomentumChart({
  observed,
  projection,
  window: w,
  height = 300,
}: {
  observed: MomentumPoint[];
  projection: MomentumPoint[];
  window: CaptureWindow;
  height?: number;
}) {
  const c = chartColors();
  const [showTable, setShowTable] = useState(false);

  const { data, today, launchBy, windowEnd } = useMemo(() => {
    // Only the recent past matters for reading the shape; six months of flat
    // pre-trend baseline just squashes the interesting part.
    const recent = observed.slice(-80);
    const merged = new Map<string, { day: string; observed?: number; projected?: number }>();
    for (const p of recent) merged.set(p.day, { day: p.day, observed: p.value });
    for (const p of projection) {
      const row = merged.get(p.day) ?? { day: p.day };
      row.projected = p.value;
      merged.set(p.day, row);
    }
    const rows = [...merged.values()].sort((a, b) => a.day.localeCompare(b.day));
    const todayKey = projection[0]?.day ?? recent[recent.length - 1]?.day ?? "";
    const idx = (d: number) => {
      const t = new Date(todayKey + "T00:00:00");
      t.setDate(t.getDate() + Math.round(d));
      return t.toISOString().slice(0, 10);
    };
    return {
      data: rows,
      today: todayKey,
      launchBy: idx(w.activation_lead_days),
      windowEnd: idx(w.ttl_days),
    };
  }, [observed, projection, w]);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <Legend
          items={[
            { label: "Observed momentum", color: c.series1 },
            { label: "Forecast", color: c.series1, dashed: true },
            { label: "Relevance threshold", color: c.muted, dashed: true },
          ]}
        />
        <TableToggle open={showTable} onToggle={() => setShowTable((s) => !s)} />
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -18 }}>
          <defs>
            <linearGradient id="momentumFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={c.series1} stopOpacity={0.22} />
              <stop offset="100%" stopColor={c.series1} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={c.grid} strokeWidth={1} vertical={false} />
          <XAxis
            dataKey="day"
            tickFormatter={fmtShortDate}
            tick={{ fontSize: 11 }}
            stroke={c.baseline}
            minTickGap={44}
          />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} stroke={c.baseline} width={44} />

          {/* The window the brand can actually use, and the part of it that
              activation lead time eats before anything ships. */}
          <ReferenceArea
            x1={today}
            x2={launchBy}
            fill={c.muted}
            fillOpacity={0.14}
            label={{ value: "activation lead", position: "insideTop", fontSize: 10, fill: c.muted }}
          />
          <ReferenceArea
            x1={launchBy}
            x2={windowEnd}
            fill={w.verdict === "PASS" ? c.critical : c.good}
            fillOpacity={0.12}
            label={{
              value: w.verdict === "PASS" ? "already closed" : "capture window",
              position: "insideTop",
              fontSize: 10,
              fill: w.verdict === "PASS" ? c.critical : c.good,
            }}
          />
          <ReferenceLine
            y={w.relevance_threshold}
            stroke={c.muted}
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
          <ReferenceLine x={today} stroke={c.ink2} strokeWidth={1.5} label={{ value: "today", position: "top", fontSize: 10, fill: c.ink2 }} />

          <Area
            type="monotone"
            dataKey="observed"
            stroke="none"
            fill="url(#momentumFill)"
            isAnimationActive={false}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="observed"
            stroke={c.series1}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="projected"
            stroke={c.series1}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            isAnimationActive={false}
            connectNulls={false}
          />
          <Tooltip
            cursor={{ stroke: c.baseline, strokeWidth: 1 }}
            contentStyle={{
              background: c.surface,
              border: `1px solid ${c.grid}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(l) => fmtShortDate(String(l))}
            formatter={(v: unknown, n: unknown) => [
              `${Number(v).toFixed(1)}`,
              String(n) === "observed" ? "Observed" : "Forecast",
            ]}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {showTable && (
        <DataTable
          columns={["Date", "Observed", "Forecast"]}
          rows={data
            .filter((_, i) => i % 4 === 0)
            .map((r) => [
              fmtShortDate(r.day),
              r.observed?.toFixed(1) ?? "—",
              r.projected?.toFixed(1) ?? "—",
            ])}
        />
      )}
    </div>
  );
}
