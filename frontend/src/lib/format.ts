export const fmtInt = (n: number) => new Intl.NumberFormat("en-US").format(Math.round(n));

export const fmtUsd = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);

export const fmtCompact = (n: number) =>
  new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n);

export const fmtPct = (n: number, digits = 0) => `${n.toFixed(digits)}%`;

export const fmtDate = (iso: string) =>
  new Date(iso + (iso.length === 10 ? "T00:00:00" : "")).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

export const fmtShortDate = (iso: string) =>
  new Date(iso + (iso.length === 10 ? "T00:00:00" : "")).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });

/** "4 days" / "49 hours" — a deadline inside three days is more legible, and
 *  more honest about the urgency, in hours. Rounding 49 hours up to "2 days"
 *  also contradicted the rationale text, which quotes the hour figure. */
export const fmtDuration = (hours: number) => {
  if (hours >= 72) return `${Math.round(hours / 24)} days`;
  return `${Math.round(hours)} hours`;
};
