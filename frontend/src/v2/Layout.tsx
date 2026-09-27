import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, isStaticDemo } from "../lib/api";
import { AskPanel, GeminiGlyph } from "./AskPanel";
import { Chip } from "./ui";

/** Steps named as questions, so the rail tells you what the tool does before
 *  you have clicked anything. */
const STEPS = [
  { to: "/", label: "Your brand", n: "1" },
  { to: "/scout", label: "What's emerging", n: "2" },
  { to: "/capture", label: "Is there time?", n: "3" },
  { to: "/creators", label: "Who qualifies", n: "4" },
  { to: "/portfolio", label: "Where the money goes", n: "5" },
  { to: "/learning", label: "What we learned", n: "6" },
];

function ThemeToggle() {
  const [theme, setTheme] = useState<string>(() => {
    try {
      return localStorage.getItem("coe-theme-v2") ?? "light";
    } catch {
      return "light";
    }
  });
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("coe-theme-v2", theme);
    } catch {
      /* private browsing — the toggle still works for this session */
    }
  }, [theme]);
  return (
    <button
      onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
      className="v2-pill px-3 py-1.5 text-[13px] font-medium text-ink-2 ring-1 ring-hairline hover:bg-raised"
      aria-label="Switch between light and dark"
    >
      {theme === "dark" ? "☀ Light" : "☾ Dark"}
    </button>
  );
}

function SourceChips() {
  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: isStaticDemo ? false : 30_000,
  });
  if (!data) return null;
  const live = Object.values(data.providers).filter((p) => p.live).length;
  const total = Object.keys(data.providers).length;
  return (
    <Chip
      tone={live > 0 ? "good" : "neutral"}
      title={
        live > 0
          ? `${live} of ${total} data sources are live Google APIs`
          : "Running on saved data — no live API calls. Add an API key to switch a source to live."
      }
    >
      {live > 0 ? `${live}/${total} live` : "Saved data"}
    </Chip>
  );
}

export function LayoutV2() {
  const [askOpen, setAskOpen] = useState(false);
  return (
    <div className="min-h-screen">
      <header
        className="sticky z-20 flex items-center justify-between gap-3 border-b border-hairline bg-surface px-4 py-2.5 sm:px-6"
        style={{ top: "env(safe-area-inset-top, 0px)" }}
      >
        <div className="flex min-w-0 items-center gap-2.5">
          {/* A play glyph, not YouTube's mark: the tool works with YouTube
              data, it is not published by YouTube. */}
          <span
            aria-hidden="true"
            className="grid h-6 w-9 shrink-0 place-items-center rounded-md"
            style={{ background: "var(--brand)" }}
          >
            <svg width="10" height="11" viewBox="0 0 10 11" fill="none" aria-hidden="true">
              <path d="M9 5.5 0 11V0z" fill="#fff" />
            </svg>
          </span>
          <div className="min-w-0">
            <div className="truncate text-[16px] font-medium tracking-tight leading-none">KAIROS</div>
            <div className="mt-1 hidden truncate text-[11px] leading-none text-muted sm:block">
              Powered by Google
            </div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            onClick={() => setAskOpen(true)}
            className="v2-pill inline-flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium"
            style={{ background: "var(--brand)", color: "var(--on-brand)" }}
          >
            <GeminiGlyph size={15} />
            <span className="hidden sm:inline">Ask Gemini</span>
            <span className="sm:hidden">Ask</span>
          </button>
          <SourceChips />
          <ThemeToggle />
        </div>
      </header>

      <div className="lg:flex">
        <nav
          aria-label="Steps"
          className="border-b border-hairline bg-surface lg:w-60 lg:shrink-0 lg:border-b-0 lg:border-r"
        >
          <ul className="flex gap-1 overflow-x-auto px-3 py-2 lg:flex-col lg:overflow-visible lg:py-3">
            {STEPS.map((s) => (
              <li key={s.to} className="shrink-0 lg:shrink">
                <NavLink
                  to={s.to}
                  end={s.to === "/"}
                  className={({ isActive }) =>
                    `v2-pill flex items-center gap-2.5 px-3 py-2 text-[14px] transition-colors lg:rounded-lg ${
                      isActive ? "font-medium" : "text-ink-2 hover:bg-raised"
                    }`
                  }
                  style={({ isActive }) =>
                    isActive ? { background: "var(--surface-2)" } : undefined
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        aria-hidden="true"
                        className="grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] font-medium"
                        style={
                          isActive
                            ? { background: "var(--brand)", color: "var(--on-brand)" }
                            : { background: "var(--surface-2)", color: "var(--text-secondary)" }
                        }
                      >
                        {s.n}
                      </span>
                      <span className="whitespace-nowrap">{s.label}</span>
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <main className="min-w-0 flex-1">
          <div className="mx-auto max-w-[980px] px-4 py-7 sm:px-6">
            <Outlet />
          </div>
        </main>
      </div>

      <AskPanel open={askOpen} onClose={() => setAskOpen(false)} />
    </div>
  );
}
