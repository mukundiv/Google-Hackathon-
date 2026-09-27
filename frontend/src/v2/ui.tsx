import type { ReactNode } from "react";

/** The one-sentence answer each screen opens with, before any number. */
export function Answer({
  eyebrow,
  headline,
  sub,
}: {
  eyebrow: string;
  headline: ReactNode;
  sub?: ReactNode;
}) {
  return (
    <header className="mb-6">
      <div className="mb-2 text-[12px] font-medium uppercase tracking-wider text-muted">
        {eyebrow}
      </div>
      <h1 className="v2-answer">{headline}</h1>
      {sub && <p className="v2-sub mt-3">{sub}</p>}
    </header>
  );
}

export function Card({
  title,
  sub,
  children,
  className = "",
}: {
  title?: ReactNode;
  sub?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-xl bg-surface p-4 ring-1 ring-hairline sm:p-5 ${className}`}
      style={{ borderRadius: "var(--radius-card)" }}
    >
      {title && (
        <div className="mb-3">
          <h2 className="text-[15px] font-medium leading-tight">{title}</h2>
          {sub && <p className="mt-1 text-[13px] leading-snug text-ink-2">{sub}</p>}
        </div>
      )}
      {children}
    </section>
  );
}

/** Everything technical lives in here: the curve fit, the solver, the
 *  evidence. Nothing is removed from the product — it just stops arriving
 *  before anyone asked for it. */
export function ShowWorking({
  label = "Show the working",
  children,
}: {
  label?: string;
  children: ReactNode;
}) {
  return (
    <details className="v2-working mt-4 rounded-xl bg-raised ring-1 ring-hairline">
      <summary className="flex items-center gap-2 px-4 py-3 text-[13px] font-medium text-ink-2">
        <span
          aria-hidden="true"
          className="inline-block text-[10px]"
          style={{ color: "var(--text-muted)" }}
        >
          ▶
        </span>
        {label}
      </summary>
      <div className="border-t px-4 py-4 text-[13px] leading-relaxed" style={{ borderColor: "var(--gridline)" }}>
        {children}
      </div>
    </details>
  );
}

/** Verdicts never use brand red — see the note in theme.css. Icon and word
 *  travel with the colour, so the state never depends on hue alone. */
const VERDICTS: Record<string, { label: string; icon: string; color: string; hint: string }> = {
  ACT: { label: "Act now", icon: "▲", color: "var(--status-good)", hint: "There is time to ship into this" },
  MARGINAL: { label: "Tight", icon: "◆", color: "var(--status-warning)", hint: "Only with a fast approval path" },
  PASS: { label: "Skip", icon: "■", color: "var(--verdict-pass)", hint: "It closes before you could launch" },
};

export function Verdict({ verdict, size = "md" }: { verdict: string; size?: "sm" | "md" }) {
  const v = VERDICTS[verdict] ?? VERDICTS.PASS;
  return (
    <span
      title={v.hint}
      className={`v2-pill inline-flex items-center gap-1.5 font-medium ${
        size === "sm" ? "px-2.5 py-1 text-[11px]" : "px-3 py-1.5 text-[13px]"
      }`}
      style={{
        color: v.color,
        background: `color-mix(in srgb, ${v.color} 13%, transparent)`,
      }}
    >
      <span aria-hidden="true">{v.icon}</span>
      {v.label}
    </span>
  );
}

export function verdictHint(verdict: string): string {
  return (VERDICTS[verdict] ?? VERDICTS.PASS).hint;
}

/** YouTube's signature control shape. */
export function PillButton({
  children,
  onClick,
  href,
  variant = "brand",
  disabled,
  full,
}: {
  children: ReactNode;
  onClick?: () => void;
  href?: string;
  variant?: "brand" | "quiet";
  disabled?: boolean;
  full?: boolean;
}) {
  const style =
    variant === "brand"
      ? { background: "var(--brand)", color: "var(--on-brand)" }
      : { background: "var(--surface-2)", color: "var(--text-primary)" };
  const cls = `v2-pill inline-flex items-center justify-center gap-2 px-5 py-2.5 text-[14px] font-medium transition-opacity disabled:opacity-40 ${
    full ? "w-full" : ""
  }`;
  if (href) {
    return (
      <a href={href} className={cls} style={style}>
        {children}
      </a>
    );
  }
  return (
    <button onClick={onClick} disabled={disabled} className={cls} style={style}>
      {children}
    </button>
  );
}

/** The single figure a screen is about. Used sparingly — at most two per
 *  screen, where the old version showed five. */
export function BigNumber({
  value,
  unit,
  label,
  tone = "neutral",
}: {
  value: ReactNode;
  unit?: string;
  label: string;
  tone?: "neutral" | "good" | "warning" | "pass";
}) {
  const color =
    tone === "good"
      ? "var(--status-good)"
      : tone === "warning"
        ? "var(--status-warning)"
        : tone === "pass"
          ? "var(--verdict-pass)"
          : "var(--text-primary)";
  return (
    <div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-[40px] font-bold leading-none tracking-tight" style={{ color }}>
          {value}
        </span>
        {unit && <span className="text-[16px] font-medium text-ink-2">{unit}</span>}
      </div>
      <div className="mt-1.5 text-[13px] text-ink-2">{label}</div>
    </div>
  );
}

export function Chip({
  children,
  tone = "neutral",
  title,
}: {
  children: ReactNode;
  tone?: "neutral" | "good" | "warning" | "brand" | "info";
  title?: string;
}) {
  const map: Record<string, string> = {
    neutral: "var(--text-secondary)",
    good: "var(--status-good)",
    warning: "var(--status-warning)",
    brand: "var(--brand)",
    info: "var(--series-1)",
  };
  return (
    <span
      title={title}
      className="v2-pill inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium"
      style={{ color: map[tone], background: `color-mix(in srgb, ${map[tone]} 12%, transparent)` }}
    >
      {children}
    </span>
  );
}

/** "Confirmed by the creator" beats "verified provenance" for everyone who
 *  did not build this. */
export function DataSource({ provenance }: { provenance: string }) {
  const map: Record<string, { tone: "good" | "info" | "warning"; text: string; help: string }> = {
    verified: {
      tone: "good",
      text: "Confirmed by the creator",
      help: "Straight from this channel owner's own YouTube Analytics",
    },
    measured: {
      tone: "info",
      text: "Measured",
      help: "Counted from public YouTube data",
    },
    estimated: {
      tone: "warning",
      text: "Our estimate",
      help: "Inferred from public signals — the creator has not confirmed it",
    },
  };
  const m = map[provenance] ?? map.estimated;
  return (
    <Chip tone={m.tone} title={m.help}>
      {m.text}
    </Chip>
  );
}

export function Bar({ value, color = "var(--series-1)" }: { value: number; color?: string }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-raised">
      <div
        style={{
          width: `${Math.max(0, Math.min(100, value))}%`,
          height: "100%",
          background: color,
          borderRadius: 999,
        }}
      />
    </div>
  );
}

export function Loading({ label = "Working" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2.5 py-16 text-[14px] text-ink-2">
      <span
        aria-hidden="true"
        className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
      />
      {label}…
    </div>
  );
}

export function Failed({ error }: { error: unknown }) {
  return (
    <div
      className="rounded-xl px-4 py-3 text-[14px]"
      style={{
        color: "var(--status-critical)",
        background: "color-mix(in srgb, var(--status-critical) 10%, transparent)",
      }}
    >
      <strong className="font-medium">Something didn't load.</strong>{" "}
      {error instanceof Error ? error.message : String(error)}
    </div>
  );
}

/** The step-to-step spine. Every screen ends with the next question. */
export function NextStep({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <div className="mt-8 flex justify-end">
      <PillButton onClick={onClick}>{label} →</PillButton>
    </div>
  );
}
