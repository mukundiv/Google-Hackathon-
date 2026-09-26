/**
 * Bundle the built console into one self-contained HTML file.
 *
 * The console normally fetches from the API. This inlines the CSS, the JS and
 * a frozen snapshot of real engine output, so the whole thing is a single file
 * that can be hosted anywhere or opened from disk — no server, no keys, no
 * install. The page reads the snapshot from `window.__DEMO_DATA__`; see the
 * static branch in src/lib/api.ts.
 *
 *   npm run build && node scripts/build-static-demo.mjs
 */

import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const DIST = "dist";
const DATA = "public/demo-data.json";

// Two outputs, because the two destinations want different things.
//
//   demo.html            a fragment, for publishing as an Artifact: the host
//                        wraps it in its own doctype/head/body skeleton, so
//                        shipping our own would nest a document in a document.
//   demo-standalone.html a complete document, for opening from disk, emailing
//                        or hosting anywhere. This one MUST carry a doctype:
//                        without it a browser falls back to quirks mode and
//                        the layout collapses.
const OUT_FRAGMENT = "demo.html";
const OUT_STANDALONE = "demo-standalone.html";

const assets = readdirSync(join(DIST, "assets"));
const jsFile = assets.find((f) => f.endsWith(".js"));
const cssFile = assets.find((f) => f.endsWith(".css"));
if (!jsFile || !cssFile) {
  console.error("No built assets found — run `npm run build` first.");
  process.exit(1);
}

const js = readFileSync(join(DIST, "assets", jsFile), "utf8");
const css = readFileSync(join(DIST, "assets", cssFile), "utf8");
const data = readFileSync(DATA, "utf8");

// `</script>` inside the JSON would close the tag early; escaping the slash is
// inert in JSON but keeps the parser out of trouble.
const safeData = data.replace(/<\//g, "<\\/");

const head = `<title>Creator Opportunity Engine</title>
<style>${css}</style>
<div id="root"></div>
<script>window.__DEMO_DATA__ = ${safeData};</script>
<script type="module">${js}</script>
`;

const standalone = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <meta name="description" content="A decision engine for YouTube creator campaigns: when to act, who to activate, where to invest." />
${head.replace(/^/gm, "    ").replace(/^ {4}<div id="root"><\/div>[\s\S]*$/m, "")}
  </head>
  <body>
    <div id="root"></div>
    <script>window.__DEMO_DATA__ = ${safeData};</script>
    <script type="module">${js}</script>
  </body>
</html>
`;

writeFileSync(OUT_FRAGMENT, head);
writeFileSync(OUT_STANDALONE, standalone);

const mb = (b) => (Buffer.byteLength(b) / 1_048_576).toFixed(2);
console.log(`wrote ${OUT_FRAGMENT}   ${mb(head)} MB  (fragment, for the Artifact)`);
console.log(`wrote ${OUT_STANDALONE}   ${mb(standalone)} MB  (full document, for sharing)`);
