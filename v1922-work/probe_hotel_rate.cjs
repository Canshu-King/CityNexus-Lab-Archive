/**
 * How often can the traveller actually pin a hotel after choosing an AI plan?
 * Repeats the real UI flow and records the refusal reason for the first hotel.
 */
const L = require("./lab_lib.cjs");
const { api, launch, context, BASE, EV, SHOTS, fs } = L;
const clean = (s) => String(s).replace(/\s+/g, " ").trim();
const N = Number(process.argv[2] || 3);

(async () => {
  const browser = await launch();
  const out = { runs: [] };

  for (let run = 1; run <= N; run++) {
    const ctx = await context(browser);
    const page = await ctx.newPage();
    const errs = [];
    L.attachErrors(page, errs);
    const rec = { run };
    try {
      const c = await L.wizardCreateWithOptions(page, { city: "\u53a6\u95e8", budget: 3000, stayBudget: 1000 });
      rec.jid = c.jid;
      const ai = await L.runAiPlan(page, "\u7b2c\u4e00\u6b21\u6765\u53a6\u95e8\uff0c\u60f3\u770b\u6d77\u3001\u8001\u8857\u548c\u65e5\u843d\uff0c\u4e0d\u60f3\u592a\u8d76\u3002");
      rec.aiPlans = ai.count;
      const cmp = await L.chooseFirstPlan(page);
      rec.cards = cmp.cards;
      rec.chosen = cmp.chosen;

      const expBefore = (await api("GET", `/journeys/${c.jid}/experience`)).json;
      rec.planBefore = {
        id: expBefore.active_plan?.id ?? null,
        status: expBefore.active_plan?.status ?? null,
        activities: (expBefore.active_plan?.activities ?? []).length,
        locked: (expBefore.active_plan?.activities ?? []).filter((a) => a.locked).length,
        failures: expBefore.experience_flags?.feasibility_failures ?? [],
      };

      await page.goto(BASE + "/v8/trips", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3500);
      await page.locator('[data-testid="trips-tab-stay"]').click();
      let cards = 0;
      for (let i = 0; i < 45; i++) {
        await page.waitForTimeout(5000);
        cards = await page.locator('[data-testid="hotel-card"]').count();
        if (cards > 0) break;
      }
      rec.hotelCards = cards;
      rec.tries = [];
      for (let i = 0; i < Math.min(cards, 10); i++) {
        const name = clean(await page.locator('[data-testid="hotel-name"]').nth(i).innerText().catch(() => ""));
        await page.locator('[data-testid="hotel-choose"]').nth(i).click();
        await page.waitForTimeout(6500);
        const chosen = (await page.locator('[data-testid="hotel-chosen"]').count()) > 0;
        const err = clean(await page.locator('[data-testid="hotel-error"]').innerText().catch(() => ""));
        rec.tries.push({ name, chosen, err });
        if (chosen) break;
      }
      rec.pinned = rec.tries.some((t) => t.chosen);
      rec.refusal = rec.tries.find((t) => t.err)?.err ?? "";
      const expAfter = (await api("GET", `/journeys/${c.jid}/experience`)).json;
      rec.planAfter = {
        id: expAfter.active_plan?.id ?? null,
        activities: (expAfter.active_plan?.activities ?? []).length,
        locked: (expAfter.active_plan?.activities ?? []).filter((a) => a.locked).length,
      };
      await page.screenshot({ path: `${SHOTS}/lab_4_run${run}.png`, fullPage: true }).catch(() => {});
    } catch (e) {
      rec.error = e.message;
    }
    rec.pageErrors = errs.slice(0, 3);
    out.runs.push(rec);
    console.log("run", run, "->", JSON.stringify({ pinned: rec.pinned, refusal: (rec.refusal || "").slice(0, 120), aiPlans: rec.aiPlans, cards: rec.hotelCards, planBefore: rec.planBefore }));
    await ctx.close();
  }

  out.pinnedCount = out.runs.filter((r) => r.pinned).length;
  out.total = out.runs.length;
  console.log("PINNED", out.pinnedCount, "/", out.total);
  fs.writeFileSync(`${EV}/cycle4_hotel_rate.json`, JSON.stringify(out, null, 1), "utf8");
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
