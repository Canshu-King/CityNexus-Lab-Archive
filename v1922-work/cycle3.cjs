/** CYCLE 3 - input robustness. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const R = { steps: [], errors: [] };
const step = (n, v) => { R.steps.push({ n, v: String(v).replace(/\s+/g, " ").slice(0, 340) }); console.log(n, "=>", String(v).replace(/\s+/g, " ").slice(0, 170)); };
const clean = (s) => String(s).replace(/\s+/g, " ").trim();

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  attachErrors(page, R.errors);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/lab_3_${n}.png`, fullPage: true }).catch(() => {});

  // ---------- 1. double-tap the journey-creation CTA ----------
  await page.goto(BASE + "/", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(2500);
  await page.locator('[data-testid="trial-city"]').fill("厦门"); await page.waitForTimeout(400);
  await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
  await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
  await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
  await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(600);
  await page.locator('[data-testid="trial-budget"]').fill("3000");
  await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(600);
  await page.locator('[data-testid="trial-create"]').click();
  const createDisabled = await page.locator('[data-testid="trial-create"]').isDisabled().catch(() => null);
  const secondTap = await page.locator('[data-testid="trial-create"]').click({ force: true, timeout: 4000 })
    .then(() => "accepted").catch((e) => "blocked: " + e.message.slice(0, 60));
  step("create-double-tap", `disabledAfterFirst=${createDisabled} second=${secondTap}`);
  let jid = null;
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(2000);
    jid = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
    if (jid && !(await page.locator('[data-testid="trial-create"]').count())) break;
  }
  R.jid = jid;
  step("journey-created", `jid=${jid}`);
  await shot("01_after_double_create");
  if (!jid) throw new Error("journey was not created");
  const exp0 = (await api("GET", `/journeys/${jid}/experience`)).json;
  const travelerId = exp0.journey.traveler_id;
  const jr = await api("GET", `/travelers/${travelerId}/journeys`).catch(() => ({ status: 0, json: null }));
  step("journeys-for-traveler", `status=${jr.status} count=${Array.isArray(jr.json) ? jr.json.length : JSON.stringify(jr.json).slice(0, 120)}`);
  R.jid = jid; R.travelerId = travelerId;

  // ---------- 2. double-submit the AI planning sheet ----------
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="hub-plan-with-ai"]').click(); await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
  const plansBefore = (await api("GET", `/journeys/${jid}/plans`)).json;
  await page.locator('[data-testid="plan-ai-submit"]').click();
  await page.waitForTimeout(300);
  const submitDisabled = await page.locator('[data-testid="plan-ai-submit"]').isDisabled();
  const secondSubmit = await page.locator('[data-testid="plan-ai-submit"]').click({ timeout: 4000 })
    .then(() => "accepted").catch((e) => "blocked: " + e.message.slice(0, 60));
  step("ai-double-submit", `submitDisabledWhileBusy=${submitDisabled} second=${secondSubmit}`);
  let aiCount = -1, aiText = "";
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(2000);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    aiText = clean(await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => ""));
    if (n !== null) { aiCount = Number(n); break; }
  }
  const plansAfter = (await api("GET", `/journeys/${jid}/plans`)).json;
  step("ai-double-submit-result", `count=${aiCount} plans ${plansBefore.length}->${plansAfter.length} text="${aiText.slice(0, 90)}"`);
  await shot("02_ai_double_submit");

  // ---------- 3. refresh mid-AI-planning ----------
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(1500);
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="hub-plan-with-ai"]').click(); await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill("第二次规划：想看海和日落，节奏轻松。");
  await page.locator('[data-testid="plan-ai-submit"]').click();
  await page.waitForTimeout(2500);
  const midSheet = await page.locator('[data-testid="plan-ai-sheet"]').count();
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(7000);
  const afterReload = {
    sheet: await page.locator('[data-testid="plan-ai-sheet"]').count(),
    heading: clean(await page.locator('[data-testid="today-heading"]').innerText().catch(() => "")),
    stuckBusy: await page.locator(".v8-loading").count(),
    body: clean(await page.locator("body").innerText().catch(() => "")).slice(0, 160),
  };
  const plansMid = (await api("GET", `/journeys/${jid}/plans`)).json;
  step("refresh-mid-ai", `sheetBeforeRefresh=${midSheet} afterReload=${JSON.stringify(afterReload)} plansNow=${plansMid.length}`);
  await shot("03_after_refresh_mid_ai");

  // ---------- 4. very long + emoji AI input ----------
  const longZh = "带爸妈去厦门三天".repeat(60) + "wave-beach-emoji".repeat(30);
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3500);
  await page.locator('[data-testid="hub-plan-with-ai"]').click(); await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill(longZh);
  const longLen = (await page.locator('[data-testid="plan-ai-input"]').inputValue()).length;
  await page.locator('[data-testid="plan-ai-submit"]').click();
  let longCount = -1, longText = "";
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(2000);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    longText = clean(await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => ""));
    if (n !== null) { longCount = Number(n); break; }
  }
  step("long-emoji-input", `chars=${longLen} planCount=${longCount} text="${longText.slice(0, 90)}"`);
  await shot("04_long_emoji_input");
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(1500);

  // ---------- 5. emoji / long text in the Copilot dock ----------
  await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3500);
  if (!(await page.locator(".cn-copilot-form textarea").count())) {
    await page.locator(".cn-copilot-edge").click().catch(() => {});
    await page.waitForTimeout(1500);
  }
  const copilotBox = page.locator(".cn-copilot-form textarea");
  let copilotSend = null;
  if (await copilotBox.count()) {
    await copilotBox.fill("wave-beach-emoji 厦门好玩吗？".repeat(20));
    copilotSend = await page.locator(".cn-copilot-form button[type=submit]").isDisabled().catch(() => null);
    await page.locator(".cn-copilot-form button[type=submit]").click().catch(() => {});
    await page.waitForTimeout(9000);
  }
  step("copilot-long-emoji", `textareaFound=${await copilotBox.count()} submitDisabled=${copilotSend}`);
  await shot("05_copilot_long_emoji");

  // ---------- 6. repeated Copilot open/close ----------
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  const dockSel = ".cn-copilot, [data-testid='v18-copilot-dock']";
  const before = await page.locator(dockSel).count();
  for (let i = 0; i < 8; i++) {
    const edge = page.locator(".cn-copilot-edge");
    if (await edge.count()) await edge.first().click({ timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(350);
    const closeBtn = page.locator(".cn-copilot-close, .cn-copilot button[aria-label*='关闭'], .cn-copilot button[aria-label*='Close']");
    if (await closeBtn.count()) await closeBtn.first().click({ timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(350);
  }
  await page.waitForTimeout(2500);
  const afterToggle = {
    dock: await page.locator(dockSel).count(),
    body: clean(await page.locator("body").innerText().catch(() => "")).slice(0, 120),
  };
  step("copilot-toggle-x8", `before=${before} after=${JSON.stringify(afterToggle)}`);
  await shot("06_copilot_toggle");

  // ---------- 7. double-tap the hotel choose button ----------
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 45; i++) { await page.waitForTimeout(5000); hotels = await page.locator('[data-testid="hotel-card"]').count(); if (hotels > 0) break; }
  let hotelResult = "no cards";
  if (hotels > 0) {
    const btn = page.locator('[data-testid="hotel-choose"]').first();
    await btn.click();
    const second = await btn.click({ force: true, timeout: 4000 }).then(() => "accepted").catch((e) => "blocked: " + e.message.slice(0, 60));
    await page.waitForTimeout(7000);
    hotelResult = `second=${second} | chosenBadges=${await page.locator('[data-testid="hotel-chosen"]').count()} errors="${clean(await page.locator('[data-testid="hotel-error"]').innerText().catch(() => ""))}"`;
  }
  step("hotel-double-tap", `cards=${hotels} ${hotelResult}`);
  await shot("07_hotel_double_tap");

  // ---------- 8. double-submit the manual booking form ----------
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="trips-tab-bookings"]').click(); await page.waitForTimeout(3500);
  let bookingResult = "form missing";
  if (await page.locator('[data-testid="inbox-tab-manual"]').count()) {
    await page.locator('[data-testid="inbox-tab-manual"]').click(); await page.waitForTimeout(600);
    await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
    await page.locator('[data-testid="manual-title"]').fill("厦门北站 到 深圳北站");
    await page.locator('[data-testid="manual-ref"]').fill("C3-DOUBLE-0001");
    await page.locator('[data-testid="manual-from"]').fill("厦门北站");
    await page.locator('[data-testid="manual-to"]').fill("深圳北站");
    await page.locator('[data-testid="manual-depart"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="manual-arrive"]').fill("2026-11-08T23:40");
    await page.locator('[data-testid="manual-amount"]').fill("180");
    const submit = page.locator('[data-testid="manual-submit"]');
    await submit.click();
    const second = await submit.click({ force: true, timeout: 4000 }).then(() => "accepted").catch((e) => "blocked: " + e.message.slice(0, 60));
    await page.waitForTimeout(9000);
    const drafts = await page.locator('[data-testid="v10-inbox-draft"]').count();
    const memory = clean(await page.locator('[data-testid="v13-2-memory"]').innerText().catch(() => ""));
    bookingResult = `second=${second} | drafts=${drafts} memory="${memory.slice(0, 80)}"`;
  }
  step("booking-double-submit", bookingResult);
  await shot("08_booking_double_submit");

  R.errors = R.errors.slice(0, 12);
  step("page-errors", `${R.errors.length} :: ${JSON.stringify(R.errors.slice(0, 5))}`);
  fs.writeFileSync(`${EV}/cycle3.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL:", e.message); R.failure = e.message; fs.writeFileSync(`${EV}/cycle3.json`, JSON.stringify(R, null, 1), "utf8"); process.exit(1); });
