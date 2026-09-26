import type { ReactNode } from "react";
import { verdictStyle } from "../lib/theme";

export function Card({
  title,
  subtitle,
  actions,
  children,
  className = "",
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-xl bg-surface ring-1 ring-hairline ${className}`}
      style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}
    >
      {(title || actions) && (
        <header className="flex flex-wrap items-start justify-between gap-3 px-5 pt-4 pb-3">
          <div className="min-w-0">
            {title && <h2 className="text-[15px] font-semibold leading-tight">{title}</h2>}
            {subtitle && <p className="mt-1 text-[13px] leading-snug text-ink-2">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      <div className="px-5 pb-5">{children}</div>
    </section>
  );
}

/** A headline figure. Used where a chart would be overkill — a single number
 *  with its label is the clearest form for one value. */
export function StatTile({
  label,
  value,
  unit,
  note,
  tone = "neutral",
  size = "md",
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  note?: ReactNode;
  tone?: "neutral" | "good" | "warning" | "critical";
  size?: "md" | "lg";
}) {
  const toneVar =
    tone === "good"
      ? "var(--status-good)"
      : tone === "warning"
        ? "var(--status-warning)"
        : tone === "critical"
          ? "var(--status-critical)"
          : "var(--text-primary)";
  return (
    <div className="rounded-lg bg-raised px-4 py-3 ring-1 ring-hairline">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted">{label}</div>
      <div
        className={`mt-1 font-semibold leading-none ${size === "lg" ? "text-4xl" : "text-2xl"}`}
        style={{ color: toneVar }}
      >
        {value}
        {unit && <span className="ml-1 text-base font-medium text-ink-2">{unit}</span>}
      </div>
      {note && <div className="mt-1.5 text-[12px] leading-snug text-ink-2">{note}</div>}
    </div>
  );
}

/** Verdict never travels as colour alone — always icon + word. */
export function VerdictPill({ verdict, size = "md" }: { verdict: string; size?: "sm" | "md" }) {
  const v = verdictStyle[verdict] ?? verdictStyle.PASS;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold uppercase tracking-wide ${
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-[11px]"
      }`}
      style={{
        color: `var(${v.varName})`,
        background: `color-mix(in srgb, var(${v.varName}) 12%, transparent)`,
        boxShadow: `inset 0 0 0 1px color-mix(in srgb, var(${v.varName}) 35%, transparent)`,
      }}
    >
      <span aria-hidden="true">{v.icon}</span>
      {v.label}
    </span>
  );
}

export function Badge({
  children,
  tone = "neutral",
  title,
}: {
  children: ReactNode;
  tone?: "neutral" | "good" | "warning" | "critical" | "info";
  title?: string;
}) {
  const map: Record<string, string> = {
    neutral: "var(--text-muted)",
    good: "var(--status-good)",
    warning: "var(--status-warning)",
    critical: "var(--status-critical)",
    info: "var(--series-1)",
  };
  return (
    <span
      title={title}
      className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide"
      style={{
        color: map[tone],
        background: `color-mix(in srgb, ${map[tone]} 10%, transparent)`,
      }}
    >
      {children}
    </span>
  );
}

/** Where a number came from. Verified and inferred data must never look alike. */
export function ProvenanceTag({ provenance }: { provenance: string }) {
  const map: Record<string, { tone: "good" | "info" | "warning"; text: string; help: string }> = {
    verified: { tone: "good", text: "Verified", help: "From the channel owner's YouTube Analytics" },
    measured: { tone: "info", text: "Measured", help: "Computed from public YouTube data" },
    estimated: { tone: "warning", text: "Estimated", help: "Inferred — not owner-verified" },
  };
  const m = map[provenance] ?? map.estimated;
  return (
    <Badge tone={m.tone} title={m.help}>
      {m.text}
    </Badge>
  );
}

export function Meter({
  value,
  max = 100,
  color = "var(--series-1)",
  height = 8,
}: {
  value: number;
  max?: number;
  color?: string;
  height?: number;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div
      className="w-full overflow-hidden rounded-full bg-raised"
      style={{ height }}
      role="img"
      aria-label={`${value.toFixed(0)} out of ${max}`}
    >
      <div
        style={{ width: `${pct}%`, background: color, height: "100%", borderRadius: 4 }}
      />
    </div>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 text-[13px] text-ink-2">
      <span
        className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
        aria-hidden="true"
      />
      {label}…
    </div>
  );
}

export function ErrorNote({ error }: { error: unknown }) {
  return (
    <div
      className="rounded-lg px-4 py-3 text-[13px]"
      style={{
        color: "var(--status-critical)",
        background: "color-mix(in srgb, var(--status-critical) 8%, transparent)",
      }}
    >
      <strong className="font-semibold">Could not load.</strong>{" "}
      {error instanceof Error ? error.message : String(error)}
      <div className="mt-1 text-ink-2">Is the API running on port 8000?</div>
    </div>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted">
      {children}
    </div>
  );
}

/** Every chart ships with a table view so identity is never colour-only. */
export function TableToggle({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      className="rounded px-2 py-1 text-[11px] font-medium text-ink-2 ring-1 ring-hairline hover:bg-raised"
    >
      {open ? "Hide table" : "Table view"}
    </button>
  );
}

export function DataTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: (string | number)[][];
}) {
  return (
    <div className="mt-3 max-h-72 overflow-auto rounded-lg ring-1 ring-hairline">
      <table className="w-full text-[12px]">
        <thead className="sticky top-0 bg-raised">
          <tr>
            {columns.map((c) => (
              <th key={c} className="px-3 py-2 text-left font-semibold text-ink-2">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t" style={{ borderColor: "var(--gridline)" }}>
              {r.map((cell, j) => (
                <td key={j} className={`px-3 py-1.5 ${j > 0 ? "tnum" : ""}`}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Legend({ items }: { items: { label: string; color: string; dashed?: boolean }[] }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
      {items.map((it) => (
        <span key={it.label} className="inline-flex items-center gap-1.5 text-[12px] text-ink-2">
          <span
            aria-hidden="true"
            style={{
              width: 14,
              height: it.dashed ? 0 : 10,
              borderRadius: it.dashed ? 0 : 3,
              background: it.dashed ? "transparent" : it.color,
              borderTop: it.dashed ? `2px dashed ${it.color}` : undefined,
              display: "inline-block",
            }}
          />
          {it.label}
        </span>
      ))}
    </div>
  );
}
