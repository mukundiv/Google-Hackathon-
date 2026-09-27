import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // GitHub Pages serves a project site from /<repo>/, so assets need that
  // prefix; everywhere else the app sits at the root. Hash routing and the
  // relative snapshot fetch mean this is the only place the subpath matters.
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // One bundle, no code splitting. The demo ships as a single
        // self-contained HTML file that has to work from a file:// URL, and a
        // split chunk there is blocked by CORS — the page silently renders
        // nothing. There is no size win to give up either: the whole app is
        // one screen's worth of code.
        inlineDynamicImports: true,
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // VITE_API_TARGET lets docker-compose point this at the api service;
      // running the two locally needs no configuration at all.
      "/api": {
        target: process.env.VITE_API_TARGET ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
