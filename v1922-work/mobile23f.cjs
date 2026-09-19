
async function main() {
  const results = { viewports: [], flows: [] };
  const browser = await chromium.launch({ channel: "chrome" });
  const VIEWPORTS = [
    { name: "390x844", width: 390, height: 844, mobile: true },
    { name: "430x932", width: 430, height: 932, mobile: true },
  ];
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (e) => pageErrors.push(String(e)));
    page.on("console", (m) => {
      if (m.type() === "error") pageErrors.push(m.text());
    });

    await arrivalBoundaryFlow(vp, results);
    await departureBoundaryFlow(vp, results);
    await recoveryFlow(vp, page, results, pageErrors);
    await acknowledgeFlow(vp, page, results, pageErrors);
    await noAlternativeFlow(vp, results);
    await replacementResolvesFlow(vp, page, results, pageErrors);
    await staleFlow(vp, page, results, pageErrors);
    await gpsFlow(browser, vp, results);
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
