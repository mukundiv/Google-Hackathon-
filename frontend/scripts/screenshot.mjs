import { chromium } from "playwright";

const OUT = process.env.SHOT_DIR ?? "./screenshots";
const pages = [
  ["brand", "/#/"],
  ["scout", "/#/scout"],
  ["capture", "/#/capture"],
  ["creators", "/#/creators"],
  ["portfolio", "/#/portfolio"],
  ["learning", "/#/learning"],
];

const browser = await chromium.launch({ ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
const problems = [];
page.on("console", (m) => { if (m.type() === "error") problems.push(`console: ${m.text().slice(0, 200)}`); });
page.on("pageerror", (e) => problems.push(`pageerror: ${String(e).slice(0, 200)}`));

for (const [name, path] of pages) {
  await page.goto(`http://127.0.0.1:5173${path}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(4500);
  const spinner = await page.locator("text=/Loading|Scouting|Fitting|Solving|Scoring|Reading/i").count();
  const err = await page.locator("text=Could not load").count();
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
  const h1 = await page.locator("h1").first().textContent().catch(() => "(none)");
  console.log(`${name.padEnd(10)} h1="${(h1 ?? "").trim().slice(0, 42)}" spinner=${spinner} error=${err}`);
}
await browser.close();
console.log(problems.length ? "\nPROBLEMS:\n" + [...new Set(problems)].join("\n") : "\nno console errors");
