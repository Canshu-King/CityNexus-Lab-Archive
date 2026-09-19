
  // ---- 21. final agreement: Trips / Live / backend ----
  const final = await api("GET", `/journeys/${JID}/experience`);
  const fa = final.json?.active_plan?.activities ?? [];
  const finalIds = fa.map((a) => a.id).join(",");
  const finalTitles = fa.map((a) => String(a.title).slice(0, 14)).join(" / ");
  rec("/api", "final-truth", `${fa.length} activities`,
      `changed=${finalIds !== beforeIds} lockedKept=${fa.filter((a) => a.locked).length} | ${finalTitles}`);
  await go("/v8/trips");
  const tripsAfter = await page.locator('[data-testid="trip-stop"]').count();
  await go("/v8/live");
  const liveAfter = await txt('[data-testid="live-next"]');
  rec("/v8/trips", "trips-after-replan", `${tripsAfter} stops`, "Trips and Live must agree with the backend");
  rec("/v8/live", "live-after-replan", liveAfter ? "has-next" : "no-next", `next="${liveAfter}"`);
  await shot("C1_22_trips_after");
  const agree = tripsAfter === fa.length;
  rec("/api", "triple-agreement", agree ? "consistent" : "MISMATCH",
      `trips=${tripsAfter} backend=${fa.length} live="${liveAfter.slice(0, 40)}"`);

  // ---- 22. language 中文 -> EN -> 中文 ----
  await go("/v8/hub");
  const zhHeading = await txt('[data-testid="today-heading"]');
  await page.locator('[data-testid="topbar-language"]').click();
  await page.waitForTimeout(2500);
  const enHeading = await txt('[data-testid="today-heading"]');
  await page.locator('[data-testid="topbar-language"]').click();
  await page.waitForTimeout(2500);
  const zhAgain = await txt('[data-testid="today-heading"]');
  rec("/v8/hub", "language-roundtrip", zhHeading && enHeading && zhAgain ? "ok" : "broken",
      `zh="${zhHeading.slice(0, 22)}" en="${enHeading.slice(0, 26)}" zh2="${zhAgain.slice(0, 22)}"`);
  await shot("C1_23_language");

  // ---- 23. hard refresh keeps the truth ----
  await go("/v8/trips");
  const beforeRefresh = await page.locator('[data-testid="trip-stop"]').count();
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const afterRefresh = await page.locator('[data-testid="trip-stop"]').count();
  rec("/v8/trips", "hard-refresh", afterRefresh === beforeRefresh ? "stable" : "changed",
      `${beforeRefresh} -> ${afterRefresh}`);
  await shot("C1_24_refresh");

  // ---- 24. browser back / forward ----
  await go("/v8/hub");
  await page.locator('[data-testid="trips-tab-nav"]').click().catch(async () => {
    const nav = page.locator('nav button', { hasText: "Trips" }).first();
    if (await nav.count()) await nav.click();
  });
  await page.waitForTimeout(2500);
  const onTrips = await page.locator('[data-testid="trip-stop"]').count();
  await page.goBack();
  await page.waitForTimeout(2500);
  const backOk = await has('[data-testid="today-heading"]');
  await page.goForward();
  await page.waitForTimeout(2500);
  const forwardOk = (await page.locator('[data-testid="trip-stop"]').count()) > 0 || (await has('[data-testid="trips-tabs"]'));
  rec("/v8", "back-forward", backOk && forwardOk ? "ok" : "broken",
      `trips=${onTrips} back=${backOk} forward=${forwardOk}`);
  await shot("C1_25_backforward");

  // ---- 25. Copilot can answer a question about the replanned trip ----
  await go("/v8/agent");
  await page.waitForTimeout(1500);
  const box2 = page.locator('.cn-copilot-form textarea');
  if (await box2.count()) {
    await box2.fill("现在第一天怎么安排？");
    await page.locator('.cn-copilot-form button[type="submit"]').click();
    await page.waitForTimeout(20000);
  }
  rec("/v8/agent", "copilot-after-replan", (await txt('.cn-copilot-history')).length > 60 ? "answered" : "empty", "");
  await shot("C1_26_copilot_after");

  fs.writeFileSync(EV + "/VISIBLE_UI_TRACE.json", JSON.stringify({
    run: "canonical-e2e-1", journey_id: JID, started: T[0]?.ts, finished: new Date().toISOString(),
    viewport: "390x844 (mobile, dpr 3)", copilot_useful: copilotUseful,
    replan: { target: String(target.title), preserved, removed: (diff.removed ?? []).length, added: (diff.added ?? []).length,
              before_titles: beforeTitles, after_titles: finalTitles, triple_agreement: agree },
    trace: T, errors: errors.slice(0, 12),
  }, null, 1), "utf8");
  T.forEach((t) => console.log(`${t.route.padEnd(11)} ${t.action.padEnd(24)} ${String(t.status).padEnd(16)} ${t.result.slice(0, 96)}`));
  console.log("JID:", JID, "| ERRORS:", errors.length, errors.slice(0, 4));
  await browser.close();
})().catch(async (e) => {
  console.error("FAIL:", e.message);
  try { fs.writeFileSync(EV + "/VISIBLE_UI_TRACE.json", JSON.stringify({ run: "canonical-e2e-1", journey_id: JID, failed: String(e.message), trace: T }, null, 1), "utf8"); } catch {}
  T.forEach((t) => console.log(`  ${t.route.padEnd(11)} ${t.action.padEnd(24)} ${String(t.status).padEnd(16)} ${t.result.slice(0, 96)}`));
  process.exit(1);
});
