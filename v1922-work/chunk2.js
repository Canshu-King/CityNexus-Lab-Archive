
  // ---- 8. AI planning ----
  await go("/v8/hub");
  await page.locator('[data-testid="hub-plan-with-ai"]').click();
  await page.waitForTimeout(1200);
  const sheet = await has('[data-testid="plan-ai-sheet"]');
  await page.locator('[data-testid="plan-ai-input"]').fill("第一次来厦门，想看海、老街和日落，不想太赶。");
  await page.locator('[data-testid="plan-ai-submit"]').click();
  let aiDone = false;
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(2000);
    const result = await txt('[data-testid="plan-ai-result"]');
    if (/NO_PLANS_PRODUCED|SKIPPED_EXTERNAL_DEPENDENCY/.test(result)) break;
    const n = await page.locator('[data-testid="plan-cmp-card"]').count();
    if (n > 0) { aiDone = true; break; }
  }
  const aiResult = await txt('[data-testid="plan-ai-result"]');
  rec("/v8/hub", "ai-plan", sheet ? (aiDone ? "plans-ready" : "no-plans") : "sheet-missing", aiResult);
  await shot("C1_06_ai");
  await page.keyboard.press("Escape").catch(() => {});
  await page.locator('[data-testid="plan-ai-sheet"] button[aria-label]').first().click().catch(() => {});
  await page.waitForTimeout(1500);

  // ---- 9. compare + choose ----
  await go("/v8/hub");
  const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
  const bands = [];
  for (let i = 0; i < cards; i++) bands.push((await page.locator('[data-testid="plan-cmp-band"]').nth(i).innerText().catch(() => "")).trim());
  rec("/v8/hub", "plan-compare", `${cards} cards`, bands.join(" / "));
  await shot("C1_07_compare");
  if (cards === 0) throw new Error("no candidate plans to compare");
  await page.locator('[data-testid="plan-cmp-choose"]').first().click();
  let chosen = false;
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(1500);
    if (!(await has('[data-testid="plan-comparison"]'))) { chosen = true; break; }
  }
  rec("/v8/hub", "choose-plan", chosen ? "selected" : "still-visible", "");
  await page.waitForTimeout(2500);
  await shot("C1_08_today");

  // ---- 10. itinerary on Trips ----
  await go("/v8/trips");
  const stops = await page.locator('[data-testid="trip-stop"]').count();
  const days = await page.locator('[data-testid="trip-day-strip"] [data-testid]').count();
  const protectedN = await page.locator('[data-testid="trip-stop-protected"]').count();
  rec("/v8/trips", "itinerary", `${stops} stops`, `days=${days} protected=${protectedN}`);
  await shot("C1_09_itinerary");
  if (stops === 0) throw new Error("itinerary is empty after choosing a plan");
