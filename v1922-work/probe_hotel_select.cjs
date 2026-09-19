const L = require("./lab_lib.cjs");
const JID = process.argv[2];
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
(async () => {
  const b = await L.launch(); const ctx = await L.context(b); const p = await ctx.newPage();
  const errs = []; L.attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  await p.goto(L.BASE + "/v8/trips", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(4000);
  await p.locator('[data-testid="trips-tab-stay"]').click();
  let hotels = 0;
  for (let i = 0; i < 45; i++) { await p.waitForTimeout(5000); hotels = await p.locator('[data-testid="hotel-card"]').count(); if (hotels > 0) break; }
  console.log("cards", hotels);
  for (let i = 0; i < Math.min(hotels, 6); i++) {
    const name = clean(await p.locator('[data-testid="hotel-name"]').nth(i).innerText().catch(() => ""));
    await p.locator('[data-testid="hotel-choose"]').nth(i).click();
    await p.waitForTimeout(7000);
    const chosen = await p.locator('[data-testid="hotel-chosen"]').count();
    const err = clean(await p.locator('[data-testid="hotel-error"]').innerText().catch(() => ""));
    console.log(i, name, "chosen=", chosen, "err=", err.slice(0, 200));
    if (chosen) break;
  }
  await p.screenshot({ path: L.SHOTS + "/probe_hotel_select.png", fullPage: true }).catch(() => {});
  const stays = await L.api("GET", `/journeys/${JID}/stay-options`);
  console.log("SELECTED rows:", (stays.json.options || []).filter(o => o.status === "SELECTED").length);
  console.log("ERRS", errs.slice(0, 6));
  await b.close();
})().catch(e => { console.error("FAIL", e.message); process.exit(1); });
