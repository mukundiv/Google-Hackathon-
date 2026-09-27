import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PortfolioComparison } from "../../lib/api";
import { chartColors } from "../../lib/theme";
import { DataTable, Legend, TableToggle } from "../ui";

/** Naive top-ranked picks against the optimised mix.
 *
 * Both measures are percentages of the same audience, so they share one axis.
 * Coverage wants to be high and overlap wants to be low, which the subtitle
 * has to say — the chart alone cannot carry that.
 */
export interface CompareLabels {
  coverage: string;
  overlap: string;
  naive: string;
  optimized: string;
}

const DEFAULT_LABELS: CompareLabels = {
  coverage: "Target coverage",
  overlap: "Audience overlap",
  naive: "Top-ranked selection",
  optimized: "Optimised portfolio",
};

export function PortfolioCompareChart({
  comparison,
  height = 240,
  labels = DEFAULT_LABELS,
}: {
  comparison: PortfolioComparison;
  height?: number;
  labels?: CompareLabels;
}) {
  const c = chartColors();
  const [showTable, setShowTable] = useState(false);

  const data = [
    {
      metric: labels.coverage,
      naive: comparison.naive.coverage_pct,
      optimized: comparison.optimized.coverage_pct,
    },
    {
      metric: labels.overlap,
      naive: comparison.naive.overlap_pct,
      optimized: comparison.optimized.overlap_pct,
    },
  ];

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <Legend
          items={[
            { label: labels.naive, color: c.series1 },
            { label: labels.optimized, color: c.series2 },
          ]}
        />
        <TableToggle open={showTable} onToggle={() => setShowTable((s) => !s)} />
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 16, right: 16, bottom: 4, left: -18 }} barGap={2}>
          <CartesianGrid stroke={c.grid} strokeWidth={1} vertical={false} />
          <XAxis dataKey="metric" tick={{ fontSize: 12 }} stroke={c.baseline} />
          <YAxis
            tick={{ fontSize: 11 }}
            stroke={c.baseline}
            width={44}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            cursor={{ fill: c.grid, fillOpacity: 0.35 }}
            contentStyle={{
              background: c.surface,
              border: `1px solid ${c.grid}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(v: unknown, n: unknown) => [
              `${Number(v).toFixed(1)}%`,
              String(n) === "naive" ? labels.naive : labels.optimized,
            ]}
          />
          <Bar dataKey="naive" fill={c.series1} radius={[4, 4, 0, 0]} isAnimationActive={false}>
            <LabelList
              dataKey="naive"
              position="top"
              fontSize={11}
              fill={c.ink2}
              formatter={(v: unknown) => `${Number(v).toFixed(0)}%`}
            />
          </Bar>
          <Bar dataKey="optimized" fill={c.series2} radius={[4, 4, 0, 0]} isAnimationActive={false}>
            <LabelList
              dataKey="optimized"
              position="top"
              fontSize={11}
              fill={c.ink2}
              formatter={(v: unknown) => `${Number(v).toFixed(0)}%`}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {showTable && (
        <DataTable
          columns={["Metric", labels.naive, labels.optimized]}
          rows={data.map((d) => [d.metric, `${d.naive.toFixed(1)}%`, `${d.optimized.toFixed(1)}%`])}
        />
      )}
    </div>
  );
}
