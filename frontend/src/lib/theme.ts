/** Chart colour roles, resolved from the CSS custom properties in index.css.
 *
 * Reading them at call time rather than hard-coding hex keeps the charts
 * correct across the light/dark switch, since Recharts needs real colour
 * values rather than `var(...)` references in several places.
 */
export function cssVar(name: string, fallback = "#888"): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export const chartColors = () => ({
  series1: cssVar("--series-1", "#2a78d6"),
  series2: cssVar("--series-2", "#eb6834"),
  series3: cssVar("--series-3", "#1baf7a"),
  grid: cssVar("--gridline", "#e1e0d9"),
  baseline: cssVar("--baseline", "#c3c2b7"),
  muted: cssVar("--text-muted", "#898781"),
  ink: cssVar("--text-primary", "#0b0b0b"),
  ink2: cssVar("--text-secondary", "#52514e"),
  surface: cssVar("--surface-1", "#fcfcfb"),
  good: cssVar("--status-good", "#0ca30c"),
  warning: cssVar("--status-warning", "#fab219"),
  critical: cssVar("--status-critical", "#d03b3b"),
});

/** Status colours are reserved and always ship with an icon and a label,
 *  never colour alone. */
export const verdictStyle: Record<string, { label: string; icon: string; varName: string }> = {
  ACT: { label: "Act", icon: "▲", varName: "--status-good" },
  MARGINAL: { label: "Marginal", icon: "◆", varName: "--status-warning" },
  PASS: { label: "Pass", icon: "■", varName: "--status-critical" },
};
