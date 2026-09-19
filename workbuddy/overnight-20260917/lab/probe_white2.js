const { chromium } = require("playwright-core");
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.LOCALAPPDATA + "\\ms-playwright\\chromium-1243\\chrome-win64\\chrome.exe", headless: true });
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 }, locale: "zh-CN" })).newPage();
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.evaluate(() => localStorage.setItem("citynexus.v8.journey_id", "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9"));
  await page.goto("http://localhost:5181/v8/hub", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(8000);
  const info = await page.evaluate(() => {
    const root = document.getElementById("root");
    const body = document.body;
    const cs = (el) => el ? getComputedStyle(el) : null;
    const first = root && root.firstElementChild;
    return {
      rootChildren: root ? root.children.length : -1,
      rootDisplay: cs(root)?.display,
      rootOpacity: cs(root)?.opacity,
      firstTag: first ? first.tagName + "." + first.className : null,
      firstDisplay: cs(first)?.display,
      firstVisibility: cs(first)?.visibility,
      firstText: first ? (first.innerText || "").slice(0, 200) : null,
      bodyBg: cs(body)?.backgroundColor,
      docCTA: document.documentElement.outerHTML.length,
      overlays: Array.from(document.querySelectorAll("body *")).filter((e) => {
        const s = getComputedStyle(e); return s.position === "fixed" && s.display !== "none";
      }).slice(0, 8).map((e) => e.tagName + "." + String(e.className).slice(0, 60)),
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
