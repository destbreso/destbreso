// Every frame of the hero's SVG as a PNG at twice its size, its animation paused at the middle of each generation, for
// build.sh to join into a GIF. Needs playwright-core (PLAYWRIGHT: the path to its index.js) and a Chromium (CHROME).
//   node tools/hero/frames.mjs hero.svg out-dir 30
import { createRequire } from "node:module";
import { mkdirSync, readFileSync } from "node:fs";

const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT);
const [svgPath, dir, count] = process.argv.slice(2);
const fps = 15;
mkdirSync(dir, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROME });
const page = await browser.newPage({ viewport: { width: 1200, height: 300 }, deviceScaleFactor: 2 });
await page.setContent(`<body style="margin:0">${readFileSync(svgPath, "utf8")}</body>`);
for (let i = 0; i < Number(count); i++) {
  const t = ((i + 0.5) / fps) * 1000;
  await page.evaluate((t) => document.querySelector("svg").getAnimations({ subtree: true }).forEach((a) => { a.pause(); a.currentTime = t; }), t);
  await page.screenshot({ path: `${dir}/f${String(i).padStart(3, "0")}.png` });
}
await browser.close();
