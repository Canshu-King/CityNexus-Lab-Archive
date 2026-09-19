
  // ---- 11. activity detail ----
  await page.locator('[data-testid="trip-stop"]').first().click();
  await page.waitForTimeout(2000);
  const detailOpen = await has('[data-testid="activity-detail"]');
  const detail = detailOpen
    ? [await txt('[data-testid="activity-title"]'), await txt('[data-testid="activity-location"]'),
       await txt('[data-testid="activity-duration"]'), await txt('[data-testid="activity-cost"]')].join(" | ")
    : "";
  rec("/v8/trips", "activity-detail", detailOpen ? "opened" : "MISSING", detail);
  await shot("C1_10_detail");
  if (detailOpen) {
    await page.locator('[data-testid="activity-map"]').click().catch(() => {});
    await page.waitForTimeout(2000);
    rec("/v8/trips", "detail-show-on-map", (await has('[data-testid="v8-maplibre-panel"]')) ? "map-shown" : "no-map", "");
    await shot("C1_11_detail_map");
    await go("/v8/trips");
    await page.locator('[data-testid="trip-stop"]').first().click();
    await page.waitForTimeout(1500);
    await page.locator('[data-testid="activity-back"]').click().catch(() => {});
    await page.waitForTimeout(1200);
    rec("/v8/trips", "detail-back", (await has('[data-testid="trip-stop"]')) ? "returned" : "stuck", "");
  }

  // ---- 12. hotels: compare + choose ----
  await page.locator('[data-testid="trips-tab-stay"]').click();
  await page.waitForTimeout(9000);
  const hotels = await page.locator('[data-testid="hotel-card"]').count();
  const hotelNames = [];
  for (let i = 0; i < Math.min(hotels, 4); i++) hotelNames.push((await txt(`[data-testid="hotel-name"] >> nth=${i}`)).slice(0, 24));
  rec("/v8/trips", "hotel-compare", `${hotels} hotels`, hotelNames.join(" / "));
  await shot("C1_12_hotels");
  let hotelOk = false;
  let hotelErr = "";
  for (let i = 0; i < Math.min(hotels, 5); i++) {
    await page.locator('[data-testid="hotel-choose"]').nth(i).click();
    await page.waitForTimeout(5500);
    if (await has('[data-testid="hotel-chosen"]')) { hotelOk = true; break; }
    hotelErr = await txt('[data-testid="hotel-error"]');
    if (/冲突/.test(hotelErr)) break;
  }
  rec("/v8/trips", "choose-hotel", hotelOk ? "selected" : "not-selected", hotelErr);
  await shot("C1_13_hotel_chosen");
  if (!hotelOk) throw new Error("no hotel could be selected: " + hotelErr);
