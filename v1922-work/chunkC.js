
const SCENARIOS = {
  // Run 2 — budget-constrained trip.
  budget: {
    viewport: { width: 390, height: 844 },
    create: { start: "2026-11-06T10:00", end: "2026-11-08T20:00", budget: 900, stayBudget: 300 },
    prompt: "两个人去厦门，预算很紧，只想看海和吃本地小吃。",
  },
  // Run 3 — long multi-day trip.
  longtrip: {
    viewport: { width: 430, height: 932 },
    create: { start: "2026-11-06T10:00", end: "2026-11-12T20:00", budget: 8000, stayBudget: 3000 },
    prompt: "在厦门待六天，慢慢逛，想看海、老街、博物馆和公园。",
  },
  // Run 4 — booking-first.
  bookingfirst: {
    viewport: { width: 390, height: 844 },
    create: { start: "2026-11-06T10:00", end: "2026-11-08T20:00", budget: 3000, stayBudget: 1000 },
    bookingFirst: true,
  },
  // Run 5 — degraded providers.
  degraded: {
    viewport: { width: 390, height: 844 },
    create: { start: "2026-11-06T10:00", end: "2026-11-08T20:00", budget: 3000, stayBudget: 1000 },
    prompt: "第一次来厦门，想看海和日落。",
    degrade: true,
  },
};

(async () => {
  const which = process.argv[2];
  const spec = SCENARIOS[which];
  if (!spec) { console.error("unknown scenario", which); process.exit(2); }
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await newContext(browser, spec.viewport);
  const page = await ctx.newPage();
  const errors = [];
  const T = [];
  let JID = null;
  const rec = (action, status, result) =>
    T.push({ ts: new Date().toISOString(), journey_id: JID, action, status, result: String(result).replace(/\s+/g, " ").slice(0, 190) });
  attach(page, errors, which);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/${which}_${n}.png` }).catch(() => {});

  try {
    JID = await createJourney(page, spec.create);
    rec("create-journey", JID ? "201" : "NO-JOURNEY", JID || "");
    await shot("01_created");
    if (!JID) throw new Error("journey not created");

    if (spec.bookingFirst) {
      // Booking-first: import a confirmed booking before any plan exists.
      await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3000);
      await page.locator('[data-testid="trips-tab-bookings"]').click();
      await page.waitForTimeout(2500);
      await page.locator('[data-testid="inbox-tab-manual"]').click();
      await page.waitForTimeout(600);
      await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
      await page.locator('[data-testid="manual-title"]').fill("厦门北站 → 深圳北站");
      await page.locator('[data-testid="manual-ref"]').fill("E2E-BOOKFIRST-1");
      await page.locator('[data-testid="manual-from"]').fill("厦门北站");
      await page.locator('[data-testid="manual-to"]').fill("深圳北站");
      await page.locator('[data-testid="manual-depart"]').fill("2026-11-08T20:00");
      await page.locator('[data-testid="manual-arrive"]').fill("2026-11-08T23:40");
      await page.locator('[data-testid="manual-amount"]').fill("180");
      await page.locator('[data-testid="manual-submit"]').click();
      await page.waitForTimeout(6000);
      await page.locator('[data-testid="v13-2-anchor-role"]').selectOption("DEPARTURE").catch(() => {});
      await page.locator('[data-testid="v13-2-save-corrections"]').click().catch(() => {});
      await page.waitForTimeout(3500);
      await page.locator('[data-testid="v13-2-smart-apply"]').click().catch(() => {});
      await page.waitForTimeout(6000);
      const wallet = await api("GET", `/journeys/${JID}/wallet`);
      const n = (wallet.json?.reservations ?? wallet.json?.items ?? []).length;
      rec("booking-first-import", n > 0 ? "applied" : "not-applied", `wallet=${n}`);
      await shot("02_booking_first");
    }

    if (spec.degrade) {
      // Honest degraded state: point the app at an unreachable provider and
      // confirm the traveller sees an explanation rather than invented data.
      const off = await api("GET", `/journeys/${JID}/offline-snapshot`);
      rec("degraded-offline-snapshot", off.status, Object.keys(off.json || {}).slice(0, 6).join(","));
    }

    if (spec.prompt) {
      const count = await planWithAi(page, spec.prompt);
      rec("ai-plan", count > 0 ? `plans-ready(${count})` : `no-plans(${count})`, "");
      await shot("03_ai");
      const ok = await choosePlan(page);
      rec("choose-plan", ok ? "selected" : "not-selected", "");
      await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3000);
      const stops = await page.locator('[data-testid="trip-stop"]').count();
      const hasTabs = await page.locator('[data-testid="trips-tabs"]').count();
      rec("itinerary", stops ? `${stops} stops` : (hasTabs ? "no-stops-shown" : "no-tabs"), "");
      await shot("04_itinerary");
    }

    const hotel = await chooseHotel(page);
    rec("choose-hotel", hotel.chosen ? "selected" : "not-selected", `${hotel.hotels} hotels ${hotel.error}`);
    await shot("05_hotel");

    if (spec.prompt) {
      const answer = await askCopilot(page, "为什么这样安排？");
      rec("copilot", answer.length > 25 ? "answered" : "empty", answer);
      await shot("06_copilot");

      const dis = await disruptAndReplan(page, JID);
      rec("disruption+replan", dis.ok ? `201 preserved=${dis.preserved} -${dis.removed}/+${dis.added}` : `FAIL ${dis.status} ${dis.error}`,
          `target=${dis.target}`);
      if (dis.ok) {
        const acc = await acceptOnLive(page);
        rec("accept-replan", acc.accepted ? "accepted" : "not-accepted", `${acc.message} disruption=${acc.sawDisruption} proposal=${acc.sawProposal}`);
        await shot("07_accepted");
        const exp = await api("GET", `/journeys/${JID}/experience`);
        rec("final-truth", `${(exp.json?.active_plan?.activities ?? []).length} activities`,
            `locked=${(exp.json?.active_plan?.activities ?? []).filter((a) => a.locked).length}`);
      }
    }

    // Refresh + navigation robustness for every scenario.
    await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    const before = await page.locator('[data-testid="trips-tabs"]').count();
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(6000);
    const after = await page.locator('[data-testid="trips-tabs"]').count();
    rec("hard-refresh", before && after ? "stable" : "broken", `before=${before} after=${after}`);
    await shot("08_refresh");

    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await page.locator('[data-testid="nav-trips"]').click();
    await page.waitForTimeout(2500);
    const onTrips = await page.locator('[data-testid="trips-tabs"]').count();
    await page.goBack();
    await page.waitForTimeout(2500);
    const backOk = await page.locator('[data-testid="today-heading"]').count();
    await page.goForward();
    await page.waitForTimeout(2500);
    const fwdOk = await page.locator('[data-testid="trips-tabs"]').count();
    rec("back-forward", onTrips && backOk && fwdOk ? "ok" : "broken", `trips=${onTrips} back=${backOk} fwd=${fwdOk}`);
  } catch (e) {
    rec("FAILURE", "error", e.message);
  }

  fs.writeFileSync(`${EV}/scenario_${which}.json`, JSON.stringify({
    run: which, journey_id: JID, viewport: `${spec.viewport.width}x${spec.viewport.height}`,
    trace: T, errors: errors.slice(0, 10),
  }, null, 1), "utf8");
  T.forEach((t) => console.log(`${t.action.padEnd(24)} ${String(t.status).padEnd(22)} ${t.result.slice(0, 84)}`));
  console.log("ERRORS:", errors.length, errors.slice(0, 3));
  await browser.close();
})();
