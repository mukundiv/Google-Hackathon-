import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
// Every skin stylesheet ships in every build, but each one's rules are scoped
// to its own [data-skin="…"], so a skin that is not selected contributes
// nothing. That is what lets one tree hold three presentations without any of
// them being able to affect the others.
import "./v2/theme.css";
import "./v3/theme.css";

const SKINS = ["youtube", "kairos"];
const skin = import.meta.env.VITE_SKIN;
if (SKINS.includes(skin)) {
  document.documentElement.setAttribute("data-skin", skin);
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
