import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CalibrationEntry, LearningState } from "../../lib/api";
import { fmtShortDate } from "../../lib/format";
import { chartColors } from "../../lib/theme";
import { DataTable, Legend, TableToggle } from "../ui";

/** How the engine re-weighted each signal after seeing results.
 *
 * Polarity data: a weight went up or it went down, around a meaningful zero.
 * That is a diverging encoding — two poles and a neutral midpoint — not a
 * categorical one.
 */
export function WeightDeltaChart({
  calibration,
  height = 230,
}: {
  calibration: CalibrationEntry[];
  height?: number;
}) {
  const c = chartColors();
  const [showTable, setShowTable] = useState(false);
  const data = calibration.map((e) => ({
    label: e.label,
    delta: (e.weight_after - e.weight_before) * 100,
    before: e.weight_before * 100,
    after: e.weight_after * 100,
    corr: e.correlation_with_outcome,
  }));

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <Legend
          items={[
            { label: "Weight increased", color: c.series1 },
            { label: "Weight decreased", color: c.critical },
          ]}
        />
        <TableToggle open={showTable} onToggle={() => setShowTable((s) => !s)} />
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 4, right: 20, bottom: 4, left: 96 }}
        >
          <CartesianGrid stroke={c.grid} strokeWidth={1} horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 11 }}
            stroke={c.baseline}
            tickFormatter={(v) => `${v > 0 ? "+" : ""}${v}`}
          />
          <YAxis
            type="category"
            dataKey="label"
            tick={{ fontSize: 12 }}
            stroke={c.baseline}
            width={96}
          />
          <ReferenceLine x={0} stroke={c.baseline} strokeWidth={1.5} />
          <Tooltip
            cursor={{ fill: c.grid, fillOpacity: 0.35 }}
            contentStyle={{
              background: c.surface,
              border: `1px solid ${c.grid}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(v: unknown) => [
              `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(1)} pts`,
              "Change",
            ]}
          />
          <Bar dataKey="delta" radius={3} isAnimationActive={false}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.delta >= 0 ? c.series1 : c.critical} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {showTable && (
        <DataTable
          columns={["Signal", "Before", "After", "Change", "Correlation with outcome"]}
          rows={data.map((d) => [
            d.label,
            `${d.before.toFixed(1)}%`,
            `${d.after.toFixed(1)}%`,
            `${d.delta > 0 ? "+" : ""}${d.delta.toFixed(1)}`,
            d.corr.toFixed(2),
          ])}
        />
      )}
    </div>
  );
}

/** Predicted against delivered, campaign by campaign. */
export function PredictionTrendChart({
  state,
  height = 230,
}: {
  state: LearningState;
  height?: number;
}) {
  const c = chartColors();
  const [showTable, setShowTable] = useState(false);
  const data = state.prediction_error_trend;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <Legend
          items={[
            { label: "Predicted", color: c.series1 },
            { label: "Actual", color: c.series2 },
          ]}
        />
        <TableToggle open={showTable} onToggle={() => setShowTable((s) => !s)} />
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -18 }}>
          <CartesianGrid stroke={c.grid} strokeWidth={1} vertical={false} />
          <XAxis
            dataKey="launched_at"
            tickFormatter={fmtShortDate}
            tick={{ fontSize: 11 }}
            stroke={c.baseline}
            minTickGap={30}
          />
          <YAxis tick={{ fontSize: 11 }} stroke={c.baseline} width={44} domain={[40, 100]} />
          <Tooltip
            cursor={{ stroke: c.baseline, strokeWidth: 1 }}
            contentStyle={{
              background: c.surface,
              border: `1px solid ${c.grid}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(l, p) => (p?.[0]?.payload?.name ?? fmtShortDate(String(l))) as string}
            formatter={(v: unknown, n: unknown) => [
              Number(v).toFixed(1),
              String(n) === "predicted" ? "Predicted" : "Actual",
            ]}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke={c.series1}
            strokeWidth={2}
            dot={{ r: 4, strokeWidth: 2, stroke: c.surface }}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke={c.series2}
            strokeWidth={2}
            dot={{ r: 4, strokeWidth: 2, stroke: c.surface }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      {showTable && (
        <DataTable
          columns={["Campaign", "Launched", "Predicted", "Actual", "Error"]}
          rows={data.map((d) => [
            d.name,
            fmtShortDate(d.launched_at),
            d.predicted.toFixed(1),
            d.actual.toFixed(1),
            `${d.error > 0 ? "+" : ""}${d.error.toFixed(1)}`,
          ])}
        />
      )}
    </div>
  );
}
