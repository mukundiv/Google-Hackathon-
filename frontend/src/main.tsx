import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
// The v2 stylesheet ships in both builds but every rule in it is scoped to
// [data-skin="youtube"], so the classic skin is untouched by it.
import "./v2/theme.css";

if (import.meta.env.VITE_SKIN === "youtube") {
  document.documentElement.setAttribute("data-skin", "youtube");
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
