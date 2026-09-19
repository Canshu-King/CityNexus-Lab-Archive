
async function gpsFlow(browser, vp, results) {
  for (const gps of ["allowed", "denied"]) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      permissions: gps === "allowed" ? ["geolocation"] : [],
      geolocation:
        gps === "allowed" ? { latitude: 39.1, longitude: 117.18 } : undefined,
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto(BASE + "/v8/live", {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.waitForTimeout(1500);
    const state = await page.evaluate(() => ({
      textLength: document.body ? document.body.innerText.length : 0,
      overflow:
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth + 1,
    }));
    results.flows.push({
      viewport: vp.name,
      flow: `GPS_${gps.toUpperCase()}`,
      rendered: state.textLength > 0,
      horizontal_overflow: state.overflow,
      page_errors: errors.slice(0, 3),
    });
    await context.close();
  }
}

async function main() {
  const results = { viewports: [], flows: [] };
  const browser = await chromium.launch({ channel: "chrome" });
  const mode = process.env.PROBE_MODE || "all";
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    page.on("console", (message) => {
      if (message.type() === "error") pageErrors.push(message.text());
    });

    if (mode === "all" || mode === "c4") {
      await c4Flow(browser, vp, results);
      await renderRoute(page, vp.name, "/v8/authoritative", results, pageErrors);
    }
    if (mode === "all" || mode === "recovery") {
      await recoveryFlow(browser, vp, results, page, pageErrors);
    }
    if (mode === "all" || mode === "stale") {
      await staleFlow(browser, vp, results, page, pageErrors);
    }
    if (mode === "all" || mode === "gps") {
      await gpsFlow(browser, vp, results);
    }
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(OUT, JSON.stringify(results, null, 1));
  console.log(JSON.stringify(results, null, 1));
}

main().catch((error) => {
  console.error("PROBE_FAILED", error);
  process.exit(1);
});
