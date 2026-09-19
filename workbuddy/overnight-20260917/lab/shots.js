// WorkBuddy red-team screenshot tool (isolated copy only)
// Usage: node shots.js <url> <outPrefix> [width] [height] [clickFlow]
const { chromium } = require("playwright-core");
const path = require("path");
const fs = require("fs");

const EXE = process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe";
const OUT = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\screenshots";

(async () => {
  const [url, prefix, w = "390", h = "844"] = process.argv.slice(2);
  if (!url || !prefix) { console.error("need url + prefix"); process.exit(1); }
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const ctx = await browser.newContext({
    viewport: { width: parseInt(w), height: parseInt(h) },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
    locale: "zh-CN",
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push("console.error: " + m.text()); });
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(4000);
  fs.mkdirSync(OUT, { recursive: true });
  await page.screenshot({ path: path.join(OUT, `${prefix}_${w}x${h}.png`), fullPage: false });
  // full page for density audit
  await page.screenshot({ path: path.join(OUT, `${prefix}_${w}x${h}_full.png`), fullPage: true });
  const title = await page.title();
  const text = (await page.locator("body").innerText().catch(() => "")).slice(0, 3000);
  fs.writeFileSync(path.join(OUT, `${prefix}_${w}x${h}_text.txt`), `TITLE: ${title}\nURL: ${page.url()}\nERRORS:\n${errors.join("\n")}\n\nTEXT:\n${text}`, "utf8");
  console.log(JSON.stringify({ ok: true, title, url: page.url(), errors }, null, 2));
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
