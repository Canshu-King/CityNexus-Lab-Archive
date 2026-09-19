/** Is "no hotel can be selected" deterministic? Try every offered hotel. */
const L = require("./lab_lib.cjs");
const { api, launch, context, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();

(async () => {
  const browser = await launch();
  const ctx = await context(browser);
  const page = await ctx.newPage();
  const errs = [];
  L.attachErrors(page, errs);
  const out = { attempts: [] };

  const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 3000, stayBudget: 1000 });
  const jid = c.jid;
  out.jid = jid;
  const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
  out.aiPlans = ai.count;
  const cmp = await L.chooseFirstPlan(page);
  out.planCards = cmp.cards;
  out.planChosen = cmp.chosen;

  // exercise the stay surface the way a traveller does
  await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3500);
  await page.locator('[data-testid="trips-tab-stay"]').click();
  let cards = 0;
  for (let i = 0; i < 45; i++) {
    await page.waitForTimeout(5000);
    cards = await page.locator('[data-testid="hotel-card"]').count();
    if (cards > 0) break;
  }
  out.hotelCards = cards;
  for (let i = 0; i < cards; i++) {
    const name = clean(await page.locator('[data-testid="hotel-name"]').nth(i).innerText().catch(() => ""));
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(7000);
    const chosen = await page.locator('[data-testid="hotel-chosen"]').count();
    const err = clean(await page.locator('[data-testid="hotel-error"]').innerText().catch(() => ""));
    out.attempts.push({ i, name, chosen: Boolean(chosen), error: err });
    if (chosen) break;
  }
  await page.screenshot({ path: `${SHOTS}/lab_4_probe_hotels.png`, fullPage: true }).catch(() => {});
  out.anyChosen = out.attempts.some((a) => a.chosen);

  // backend view of the same journey
  const exp = (await api("GET", `/journeys/${jid}/experience`)).json;
  out.plan = {
    id: exp.active_plan?.id ?? null,
    status: exp.active_plan?.status ?? null,
    activities: (exp.active_plan?.activities ?? []).length,
    locked: (exp.active_plan?.activities ?? []).filter((a) => a.locked).length,
  };
  out.selectedOptionId = exp.selected_option_id;
  const stays = (await api("GET", `/journeys/${jid}/stay-options`)).json;
  out.stayOptions = (stays.options ?? []).length;
  out.selectedStays = (stays.options ?? []).filter((o) => o.status === "SELECTED").length;
  out.flags = exp.experience_flags;
  out.errors = errs.slice(0, 6);

  console.log(JSON.stringify(out, null, 1));
  fs.writeFileSync(`${EV}/cycle4_hotel_probe.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
