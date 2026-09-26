import { useState } from "react";
import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { CreatorScore } from "../../lib/api";
import { fmtCompact } from "../../lib/format";
import { chartColors } from "../../lib/theme";
import { DataTable, Legend, TableToggle } from "../ui";

/** Reach ≠ relevance.
 *
 * Subscribers on a log x-axis against opportunity score on y. If audience size
 * bought relevance the cloud would slope up; the point of the chart is that it
 * does not.
 */
export function ReachRelevanceChart({
  scores,
  selectedIds = [],
  height = 300,
}: {
  scores: CreatorScore[];
  selectedIds?: string[];
  height?: number;
}) {
  const c = chartColors();
  const [showTable, setShowTable] = useState(false);
  const chosen = new Set(selectedIds);

  const data = scores.map((s) => ({
    x: s.subscribers,
    y: s.composite,
    name: s.creator_name,
    archetype: s.archetype ?? "",
    inPortfolio: chosen.has(s.creator_id),
  }));

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <Legend
          items={[
            { label: "Creator", color: c.series1 },
            ...(selectedIds.length ? [{ label: "In recommended portfolio", color: c.series2 }] : []),
          ]}
        />
        <TableToggle open={showTable} onToggle={() => setShowTable((s) => !s)} />
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 18, left: -18 }}>
          <CartesianGrid stroke={c.grid} strokeWidth={1} />
          <XAxis
            type="number"
            dataKey="x"
            scale="log"
            domain={["dataMin", "dataMax"]}
            tickFormatter={(v) => fmtCompact(Number(v))}
            tick={{ fontSize: 11 }}
            stroke={c.baseline}
            label={{
              value: "Subscribers (log scale)",
              position: "insideBottom",
              offset: -10,
              fontSize: 11,
              fill: c.muted,
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={[0, 100]}
            tick={{ fontSize: 11 }}
            stroke={c.baseline}
            width={44}
          />
          <ZAxis range={[90, 90]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3", stroke: c.baseline }}
            contentStyle={{
              background: c.surface,
              border: `1px solid ${c.grid}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            content={({ payload }) => {
              const p = payload?.[0]?.payload;
              if (!p) return null;
              return (
                <div
                  style={{
                    background: c.surface,
                    border: `1px solid ${c.grid}`,
                    borderRadius: 8,
                    padding: "8px 10px",
                    fontSize: 12,
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{p.name}</div>
                  <div style={{ color: c.ink2 }}>{p.archetype}</div>
                  <div style={{ marginTop: 4 }} className="tnum">
                    {fmtCompact(p.x)} subs · score {p.y.toFixed(1)}
                  </div>
                </div>
              );
            }}
          />
          <Scatter data={data} isAnimationActive={false}>
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={d.inPortfolio ? c.series2 : c.series1}
                fillOpacity={d.inPortfolio ? 1 : 0.65}
                stroke={c.surface}
                strokeWidth={2}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      {showTable && (
        <DataTable
          columns={["Creator", "Subscribers", "Score", "In portfolio"]}
          rows={data
            .sort((a, b) => b.y - a.y)
            .map((d) => [d.name, fmtCompact(d.x), d.y.toFixed(1), d.inPortfolio ? "yes" : "—"])}
        />
      )}
    </div>
  );
}
