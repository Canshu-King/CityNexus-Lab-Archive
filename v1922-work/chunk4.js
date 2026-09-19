
  // ---- 13. prove the pinned truth survived: POIs, day, duration, locked ----
  const truth = await api("GET", `/journeys/${JID}/experience`);
  const acts = (truth.json?.active_plan?.activities ?? []);
  const pois = acts.filter((a) => String(a.type || a.kind || "").toUpperCase().includes("ACTIVITY") || /景点/.test(String(a.title)));
  const locked = acts.filter((a) => a.locked === true);
  const pinnedTitles = locked.map((a) => String(a.title).slice(0, 18));
  const planDays = new Set(acts.map((a) => String(a.start_at ?? a.start_time ?? "").slice(0, 10)).filter(Boolean));
  rec("/api", "truth-after-hotel", `${acts.length} activities`,
      `pois=${pois.length} locked=${locked.length} days=${[...planDays].join(",")} | ${pinnedTitles.join(" / ")}`);
  const after = await api("GET", `/journeys/${JID}/stay-options`);
  const selOpt = (after.json?.options ?? []).find((o) => o.status === "SELECTED");
  rec("/api", "stay-truth", selOpt ? "SELECTED" : "NONE",
      selOpt ? `${selOpt.property_name} in=${selOpt.check_in_at} out=${selOpt.check_out_at}` : "");
  if (!selOpt) throw new Error("stay option is not authoritative after selection");
  if (pois.length === 0) throw new Error("the chosen plan lost its POIs after the hotel was pinned");

  // ---- 14. booking import through the visible form ----
  await go("/v8/trips");
  await page.locator('[data-testid="trips-tab-bookings"]').click();
  await page.waitForTimeout(3000);
  const inboxThere = await has('[data-testid="inbox-tab-manual"]');
  if (inboxThere) {
    await page.locator('[data-testid="inbox-tab-manual"]').click();
    await page.waitForTimeout(600);
    await page.locator('[data-testid="manual-type"]').selectOption("RAIL");
    await page.locator('[data-testid="manual-title"]').fill("厦门北站 → 深圳北站");
    await page.locator('[data-testid="manual-ref"]').fill("E2E-CHAIN-0001");
    await page.locator('[data-testid="manual-amount"]').fill("180");
    await page.locator('[data-testid="manual-submit"]').click();
    await page.waitForTimeout(6000);
  }
  const draftShown = await has('[data-testid="v10-inbox-draft"]');
  const interp = draftShown ? await txt('[data-testid="v13-2-interpretation"]') : "";
  rec("/v8/trips", "booking-manual-draft", draftShown ? "draft-created" : "MISSING", interp);
  await shot("C1_14_booking_draft");
  let applied = false;
  if (draftShown) {
    await page.locator('[data-testid="v13-2-smart-apply"]').click().catch(() => {});
    await page.waitForTimeout(5000);
    applied = /已|applied|CONFIRMED/i.test(await txt('[data-testid="v10-inbox-draft"]'));
  }
  const wallet = await api("GET", `/journeys/${JID}/wallet`);
  const resv = (wallet.json?.reservations ?? wallet.json?.items ?? []);
  rec("/v8/trips", "booking-import", applied ? "applied" : "not-applied", `wallet=${Array.isArray(resv) ? resv.length : 0} entries`);
  await shot("C1_15_booking_applied");

  // ---- 15. booking visible in Trips / wallet ----
  await go("/v8/trips");
  await page.locator('[data-testid="trips-tab-bookings"]').click();
  await page.waitForTimeout(2500);
  const bookingsText = (await txt('[data-testid="trips-tabs"] ~ *')).slice(0, 0);
  const bookingVisible = await page.locator('text=E2E-CHAIN-0001').count();
  const bookingVisible2 = await page.locator('text=厦门北站').count();
  rec("/v8/trips", "booking-visible", bookingVisible + bookingVisible2 > 0 ? "visible" : "not-visible",
      `ref=${bookingVisible} title=${bookingVisible2}`);
  await shot("C1_16_booking_visible");
