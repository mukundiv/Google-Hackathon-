import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Badge } from "./ui";

const STAGES = [
  { to: "/", label: "Brand Portal", step: "00", blurb: "History and insight" },
  { to: "/scout", label: "Trend Scout", step: "01", blurb: "What's emerging?" },
  { to: "/capture", label: "Capture Window", step: "02", blurb: "Is there still time?" },
  { to: "/creators", label: "Creator Score", step: "03", blurb: "Who can own it?" },
  { to: "/portfolio", label: "Portfolio", step: "04", blurb: "Where to invest?" },
  { to: "/learning", label: "Learning Loop", step: "05", blurb: "What improves next?" },
];

function ThemeToggle() {
  const [theme, setTheme] = useState<string>(
    () => localStorage.getItem("coe-theme") ?? "dark",
  );
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("coe-theme", theme);
    } catch {
      /* private mode — the toggle still works for this session */
    }
  }, [theme]);
  return (
    <button
      onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
      className="rounded-md px-2 py-1 text-[12px] text-ink-2 ring-1 ring-hairline hover:bg-raised"
      aria-label="Toggle colour theme"
    >
      {theme === "dark" ? "☼ Light" : "☾ Dark"}
    </button>
  );
}

/** Per-source live/mock badges.
 *
 * The console must never leave anyone guessing whether a number came from a
 * live Google API or the seeded world.
 */
function ProviderBadges() {
  const { data } = useQuery({ queryKey: ["health"], queryFn: api.health, refetchInterval: 30_000 });
  if (!data) return null;
  const labels: Record<string, string> = {
    gemini: "Gemini",
    youtube: "YouTube",
    trends: "Trends",
    analytics: "Analytics",
  };
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {Object.entries(data.providers).map(([key, p]) => (
        <Badge
          key={key}
          tone={p.live ? "good" : "neutral"}
          title={
            p.live
              ? `${labels[key]}: live — ${p.detail}`
              : `${labels[key]}: mock data${p.detail ? ` — ${p.detail}` : ""}`
          }
        >
          {labels[key]} {p.live ? "live" : "mock"}
        </Badge>
      ))}
    </div>
  );
}

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <aside className="shrink-0 border-b border-hairline bg-surface lg:w-64 lg:border-b-0 lg:border-r">
        <div className="px-5 py-5">
          <div className="text-[11px] font-semibold uppercase tracking-widest text-muted">
            Creator
          </div>
          <div className="text-[17px] font-semibold leading-tight">Opportunity Engine</div>
          <p className="mt-1 text-[12px] leading-snug text-ink-2">
            When to act, who to activate, where to invest.
          </p>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:overflow-visible">
          {STAGES.map((s) => (
            <NavLink
              key={s.to}
              to={s.to}
              end={s.to === "/"}
              className={({ isActive }) =>
                `flex shrink-0 items-start gap-2.5 rounded-lg px-3 py-2 text-left transition-colors ${
                  isActive ? "bg-raised" : "hover:bg-raised/60"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className="mt-0.5 tnum text-[10px] font-semibold"
                    style={{ color: isActive ? "var(--series-1)" : "var(--text-muted)" }}
                  >
                    {s.step}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-[13px] font-medium leading-tight">{s.label}</span>
                    <span className="hidden text-[11px] leading-tight text-muted lg:block">
                      {s.blurb}
                    </span>
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline bg-surface px-4 py-3 sm:px-6">
          <ProviderBadges />
          <ThemeToggle />
        </header>
        <main className="mx-auto max-w-[1180px] px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
