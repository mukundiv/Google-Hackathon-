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
const OUT = "demo.html";

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

// Published as a document fragment, not a full document: the Artifact host
// wraps the file in its own doctype/head/body skeleton (which supplies charset,
// viewport and the phone safe-area padding), so shipping our own would nest one
// document inside another. Everything else — title, styles, data, app — belongs
// here at the top level.
const html = `<title>Creator Opportunity Engine</title>
<style>${css}</style>
<div id="root"></div>
<script>window.__DEMO_DATA__ = ${safeData};</script>
<script type="module">${js}</script>
`;

writeFileSync(OUT, html);
const mb = (Buffer.byteLength(html) / 1_048_576).toFixed(2);
console.log(`wrote ${OUT} (${mb} MB)`);
