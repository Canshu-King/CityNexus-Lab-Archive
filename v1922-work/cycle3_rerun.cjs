/** CYCLE 3 rerun - input robustness on a stable DB. */
const L = require("./lab_lib.cjs");
const { api, launch, context, attachErrors, BASE, EV, SHOTS, fs } = L;
const R = { steps: [], errors: [] };
const step = (n, v) => { R.steps.push({ n, v: String(v).replace(/\s+/g, " ").slice(0, 340) }); console.log(n, "=>", String(v).replace(/\s+/g, " ").slice(0, 165)); };
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const uniq = (arr) => arr.length === new Set(arr).size;

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  attachErrors(page, R.errors);
  const shot = (n) => page.screenshot({ path: `${SHOTS}/lab_3_${n}.png`, fullPage: true }).catch(() => {});

  // ---- 1. double-tap the journey-creation CTA ----
  await page.goto(BASE + "/", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(2500);
  await page.locator('[data-testid="trial-city"]').fill("\u53a6\u95e8"); await page.waitForTimeout(400);
  await page.locator('[data-testid="trial-arrival"]').fill("\u53a6\u95e8\u9ad8\u5d0e\u56fd\u9645\u673a\u573a");
  await page.locator('[data-testid="trial-departure"]').fill("\u53a6\u95e8\u5317\u7ad9");
  await page.locator('[data-testid="trial-start"]').fill("2026-11-06T10:00");
  await page.locator('[data-testid="trial-end"]').fill("2026-11-08T20:00");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(600);
  await page.locator('[data-testid="trial-budget"]').fill("3000");
  await page.locator('[data-testid="trial-stay-budget"]').fill("1000");
  await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(600);
  await page.locator('[data-testid="trial-create"]').click();
  const disabled = await page.locator('[data-testid="trial-create"]').isDisabled().catch(() => null);
  const second = await page.locator('[data-testid="trial-create"]').click({ force: true, timeout: 4000 }).then(() => "accepted").catch((e) => "blocked:" + e.message.slice(0, 40));
  let jid = null;
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(2000);
    jid = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
    if (jid && !(await page.locator('[data-testid="trial-create"]').count())) break;
  }
  R.jid = jid;
  step("1-create-double-tap", `disabledAfterFirst=${disabled} second=${second} jid=${jid}`);
  await shot("01_create");
  if (!jid) throw new Error("no journey");

  // ---- 2. double-submit the AI sheet ----
  const places = (await api("GET", `/places?city_code=CN-XIAMEN`)).json;
  step("2-places-available", `n=${Array.isArray(places) ? places.length : JSON.stringify(places)}`);
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4500);
  await page.locator('[data-testid="hub-plan-with-ai"]').click(); await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill("\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
  const plansBefore = (await api("GET", `/journeys/${jid}/plans`)).json;
  await page.locator('[data-testid="plan-ai-submit"]').click();
  await page.waitForTimeout(300);
  const busyDisabled = await page.locator('[data-testid="plan-ai-submit"]').isDisabled();
  const secondSubmit = await page.locator('[data-testid="plan-ai-submit"]').click({ timeout: 4000 }).then(() => "accepted").catch((e) => "blocked:" + e.message.slice(0, 40));
  let aiCount = -1, aiText = "";
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(2000);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    aiText = clean(await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => ""));
    if (n !== null) { aiCount = Number(n); break; }
  }
  const plansAfter = (await api("GET", `/journeys/${jid}/plans`)).json;
  const afterIds = (plansAfter ?? []).map((p) => p.id);
  step("2-ai-double-submit", `busyDisabled=${busyDisabled} second=${secondSubmit} planCount=${aiCount} plans ${(plansBefore ?? []).length}->${afterIds.length} uniqueIds=${uniq(afterIds)} text="${aiText.slice(0, 70)}"`);
  await shot("02_ai_double");
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(1500);

  // ---- 3. refresh mid-AI-planning ----
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="hub-plan-with-ai"]').click(); await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill("\u7b2c\u4e8c\u6b21\u89c4\u5212\uff1a\u60f3\u770b\u6d77\u548c\u65e5\u843d\uff0c\u8282\u594f\u8f7b\u677e\u3002");
  await page.locator('[data-testid="plan-ai-submit"]').click();
  await page.waitForTimeout(2500);
  const midSheet = await page.locator('[data-testid="plan-ai-sheet"]').count();
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(8000);
  const after = {
    sheet: await page.locator('[data-testid="plan-ai-sheet"]').count(),
    heading: clean(await page.locator('[data-testid="today-heading"]').innerText().catch(() => "")),
    stuckBusy: await page.locator(".v8-loading").count(),
  };
  const plansMid = (await api("GET", `/journeys/${jid}/plans`)).json;
  step("3-refresh-mid-ai", `sheetBefore=${midSheet} afterReload=${JSON.stringify(after)} plansNow=${plansMid.length} uniqueIds=${uniq(plansMid.map((p) => p.id))}`);
  await shot("03_refresh_mid_ai");

  // ---- 4. very long + emoji AI input ----
  const longZh = "\u5e26\u7238\u5988\u53bb\u53a6\u95e8\u4e09\u5929".repeat(60) + "\u{1F30A}\u{1F3DD}\u{1F600}".repeat(30);
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3500);
  await page.locator('[data-testid="hub-plan-with-ai"]').click(); await page.waitForTimeout(1200);
  await page.locator('[data-testid="plan-ai-input"]').fill(longZh);
  const len = (await page.locator('[data-testid="plan-ai-input"]').inputValue()).length;
  await page.locator('[data-testid="plan-ai-submit"]').click();
  let longCount = -1, longText = "";
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(2000);
    const n = await page.locator('[data-testid="plan-ai-result"]').getAttribute("data-plan-count").catch(() => null);
    longText = clean(await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => ""));
    if (n !== null) { longCount = Number(n); break; }
  }
  step("4-long-emoji-ai", `chars=${len} planCount=${longCount} text="${longText.slice(0, 80)}"`);
  await shot("04_long_emoji");
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(1500);

  // ---- 5. long + emoji in Copilot ----
  await page.goto(BASE + "/v8/agent", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(3500);
  if (!(await page.locator(".cn-copilot-form textarea").count())) {
    await page.locator(".cn-copilot-edge").click().catch(() => {}); await page.waitForTimeout(1500);
  }
  const box = page.locator(".cn-copilot-form textarea");
  let sent = "no textarea";
  if (await box.count()) {
    await box.fill("\u{1F30A}\u{1F3DD}\u{1F600} \u53a6\u95e8\u597d\u73a9\u5417\uff1f".repeat(20));
    const val = await box.inputValue();
    await page.locator(".cn-copilot-form button[type=submit]").click().catch(() => {});
    await page.waitForTimeout(10000);
    const bubbles = await page.locator(".cn-copilot-bubble").count();
    sent = `chars=${val.length} bubbles=${bubbles}`;
  }
  step("5-copilot-long-emoji", sent);
  await shot("05_copilot_long_emoji");

  // ---- 6. repeated Copilot open/close ----
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  const dockSel = ".cn-copilot, [data-testid='v18-copilot-dock']";
  const before = await page.locator(dockSel).count();
  for (let i = 0; i < 8; i++) {
    const edge = page.locator(".cn-copilot-edge");
    if (await edge.count()) await edge.first().click({ timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(300);
    const close = page.locator(".cn-copilot-close");
    if (await close.count()) await close.first().click({ timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(300);
  }
  await page.waitForTimeout(2500);
  step("6-copilot-toggle-x8", `before=${before} after=${await page.locator(dockSel).count()} heading="${clean(await page.locator('[data-testid="today-heading"]').innerText().catch(() => ""))}"`);
  await shot("06_copilot_toggle");

  // ---- 7. double-tap hotel choose ----
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 45; i++) { await page.waitForTimeout(5000); hotels = await page.locator('[data-testid="hotel-card"]').count(); if (hotels > 0) break; }
  let hotelMsg = "no cards";
  if (hotels > 0) {
    const btn = page.locator('[data-testid="hotel-choose"]').first();
    await btn.click();
    const s2 = await btn.click({ force: true, timeout: 4000 }).then(() => "accepted").catch((e) => "blocked:" + e.message.slice(0, 40));
    await page.waitForTimeout(8000);
    hotelMsg = `second=${s2} chosenBadges=${await page.locator('[data-testid="hotel-chosen"]').count()} error="${clean(await page.locator('[data-testid="hotel-error"]').innerText().catch(() => ""))}"`;
  }
  step("7-hotel-double-tap", `cards=${hotels} ${hotelMsg}`);
  await shot("07_hotel_double");
  const stays = (await api("GET", `/journeys/${jid}/stay-options`)).json;
  const selected = (stays.options ?? []).filter((o) => o.status === "SELECTED");
  step("7-hotel-truth", `SELECTED rows=${selected.length} names=${selected.map((o) => o.stay.property_name).join(",")}`);

  // ---- 8. double-submit the manual booking form ----
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  await page.locator('[data-testid="trips-tab-bookings"]').click(); await page.waitForTimeout(3500);
  let bookingMsg = "form missing";
  if (await page.locator('[data-testid="inbox-tab-manual"]').count()) {
    await page.locator('[data-testid="inbox-tab-manual"]').click(); await page.waitForTimeout(600);
    await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
    await page.locator('[data-testid="manual-title"]').fill("\u53a6\u95e8\u5317\u7ad9 \u2192 \u6df1\u5733\u5317\u7ad9");
    await page.locator('[data-testid="manual-ref"]').fill("C3-DOUBLE-0002");
    await page.locator('[data-testid="manual-from"]').fill("\u53a6\u95e8\u5317\u7ad9");
    await page.locator('[data-testid="manual-to"]').fill("\u6df1\u5733\u5317\u7ad9");
    await page.locator('[data-testid="manual-depart"]').fill("2026-11-08T20:00");
    await page.locator('[data-testid="manual-arrive"]').fill("2026-11-08T23:40");
    await page.locator('[data-testid="manual-amount"]').fill("180");
    const submit = page.locator('[data-testid="manual-submit"]');
    await submit.click();
    const s2 = await submit.click({ force: true, timeout: 4000 }).then(() => "accepted").catch((e) => "blocked:" + e.message.slice(0, 40));
    await page.waitForTimeout(9000);
    const drafts = await page.locator('[data-testid="v10-inbox-draft"]').count();
    const refs = await page.locator("text=C3-DOUBLE-0002").count();
    bookingMsg = `second=${s2} drafts=${drafts} refVisible=${refs}`;
  }
  step("8-booking-double-submit", bookingMsg);
  await shot("08_booking_double");

  // ---- 9. repeated primary-CTA taps ----
  await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await page.waitForTimeout(4000);
  for (let i = 0; i < 5; i++) {
    await page.locator('[data-testid="hub-plan-with-ai"]').click({ timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(200);
  }
  await page.waitForTimeout(1500);
  step("9-cta-taps-x5", `sheets=${await page.locator('[data-testid="plan-ai-sheet"]').count()}`);
  await page.locator(".plan-ai-close").click().catch(() => {});
  await page.waitForTimeout(1000);

  // ---- 10. backend duplication audit ----
  const finalPlans = (await api("GET", `/journeys/${jid}/plans`)).json;
  const allStays = (await api("GET", `/journeys/${jid}/stay-options`)).json;
  const wallet = (await api("GET", `/journeys/${jid}/wallet`)).json;
  step("10-backend-audit", `plans=${finalPlans.length} uniqueIds=${uniq(finalPlans.map((p) => p.id))} versionNos=${finalPlans.map((p) => p.version_no).join(",")} | stayOptions=${(allStays.options ?? []).length} SELECTED=${(allStays.options ?? []).filter((o) => o.status === "SELECTED").length} | reservations=${(wallet.reservations ?? []).length} commitments=${(wallet.commitments ?? []).length}`);

  step("page-errors", `${R.errors.length} ${JSON.stringify(R.errors.slice(0, 5))}`);
  fs.writeFileSync(`${EV}/cycle3.json`, JSON.stringify(R, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL:", e.message); R.failure = e.message; fs.writeFileSync(`${EV}/cycle3.json`, JSON.stringify(R, null, 1), "utf8"); process.exit(1); });
