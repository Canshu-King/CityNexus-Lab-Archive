/** CYCLE 1 follow-up: is Today's clock timezone-correct and consistent with Trips? */
const L = require("./lab_lib.cjs");
const { launch, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
const R = { jid: JID, runs: [] };
(async () => {
  const browser = await launch();
  for (const tz of ["Asia/Shanghai", "UTC", "America/New_York"]) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN", timezoneId: tz });
    const page = await ctx.newPage();
    await page.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const today = {
      heading: (await page.locator('[data-testid="today-heading"]').innerText().catch(() => "")).trim(),
      when: (await page.locator('[data-testid="today-when"]').innerText().catch(() => "")).trim(),
      next: (await page.locator('[data-testid="today-next"]').innerText().catch(() => "")).replace(/\n/g, " | ").trim(),
    };
    await page.screenshot({ path: `${SHOTS}/lab_1_tz_${tz.replace(/\//g, "-")}_hub.png` }).catch(() => {});
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    const trips = {
      dayStrip: (await page.locator('[data-testid="trip-day-strip"]').innerText().catch(() => "")).replace(/\n/g, " | ").trim(),
      firstStop: (await page.locator('[data-testid="trip-stop"]').first().innerText().catch(() => "")).replace(/\n/g, " | ").trim().slice(0, 160),
    };
    await page.screenshot({ path: `${SHOTS}/lab_1_tz_${tz.replace(/\//g, "-")}_trips.png` }).catch(() => {});
    await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    const live = { current: (await page.locator('[data-testid="live-journey-current"]').innerText().catch(() => "")).trim() };
    R.runs.push({ deviceTimezone: tz, today, trips, live });
    console.log(tz, JSON.stringify({ today, trips, live }));
    await ctx.close();
  }
  fs.writeFileSync(`${EV}/cycle1_tz_result.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
