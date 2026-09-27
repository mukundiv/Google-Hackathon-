import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
// The v2 stylesheet ships in both builds but every rule in it is scoped to
// [data-skin="youtube"], so the classic skin is untouched by it.
import "./v2/theme.css";

if (import.meta.env.VITE_SKIN === "youtube") {
  document.documentElement.setAttribute("data-skin", "youtube");
}

/** Load the data before the app does.
 *
 * The artifact build inlines the snapshot on `window.__DEMO_DATA__`; the
 * deployed build ships it as a file beside the page. Fetching it here, before
 * dynamically importing App, means the data layer still just reads the global
 * at module load and needs no knowledge of where it came from.
 */
async function boot() {
  if (import.meta.env.VITE_STATIC_DATA && !window.__DEMO_DATA__) {
    try {
      const res = await fetch("./demo-data.json");
      if (res.ok) window.__DEMO_DATA__ = await res.json();
    } catch {
      // No snapshot: the app falls through to the live API, and shows its own
      // error state if that is not there either.
    }
  }
  const { default: App } = await import("./App");
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}

void boot();
