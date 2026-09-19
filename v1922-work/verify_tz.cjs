const L = require("./lab_lib.cjs");
const { launch, BASE, EV, SHOTS, fs } = L;
const JID = process.argv[2];
(async () => {
  const browser = await launch();
  const out = [];
  for (const tz of ["Asia/Shanghai", "UTC", "America/New_York"]) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: "zh-CN", timezoneId: tz });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", (e) => errs.push(String(e).slice(0, 160)));
    await page.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const today = {
      when: (await page.locator('[data-testid="today-when"]').innerText().catch(() => "")).trim(),
      next: (await page.locator('[data-testid="today-next"]').innerText().catch(() => "")).replace(/\n/g, " | ").trim(),
      arrival: (await page.locator('.v8-anchor-row').innerText().catch(() => "")).replace(/\n/g, " | ").trim(),
    };
    await page.screenshot({ path: `${SHOTS}/lab_1_fixed_${tz.replace(/\//g, "-")}_hub.png` }).catch(() => {});
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    const first = (await page.locator('[data-testid="trip-stop"]').first().innerText().catch(() => "")).replace(/\n/g, " | ").trim().slice(0, 120);
    await page.goto(BASE + "/v8/live", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    const live = (await page.locator('.v8-live-now').innerText().catch(() => "")).replace(/\n/g, " | ").trim().slice(0, 160);
    await page.screenshot({ path: `${SHOTS}/lab_1_fixed_${tz.replace(/\//g, "-")}_live.png` }).catch(() => {});
    out.push({ tz, today, tripsFirstStop: first, live, pageErrors: errs });
    console.log(tz, "|", today.when, "|", today.next.slice(0, 60), "|", first, "|", live.slice(0, 70));
    await ctx.close();
  }
  fs.writeFileSync(`${EV}/cycle1_fix_verify.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
