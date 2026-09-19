
async function c4Flow(browser, vp, results) {
  await resetDemo();
  const journeyId = "22222222-2222-4222-8222-222222222222";
  const { imported, confirmed } = await importAndConfirm(
    journeyId,
    c4Reservation(`MOBILE-C4-${vp.name}`),
  );
  const generated = await api(`/journeys/${journeyId}/plans/generate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  const picked = await selectFirstPlan(journeyId);
  results.flows.push({
    viewport: vp.name,
    flow: "C4_ANCHORED_JOURNEY",
    import: imported.status,
    confirm: confirmed.status,
    generate: generated.status,
    plans: picked.list ? picked.list.length : 0,
    select: picked.select.status,
    start: picked.start.status,
  });
}

async function renderRoute(page, viewport, path, results, pageErrors) {
  await page.goto(BASE + path, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForTimeout(1200);
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    textLength: document.body ? document.body.innerText.length : 0,
  }));
  const panelCount = await page
    .locator('[data-testid="recovery-required-panel"]')
    .count();
  results.viewports.push({
    viewport,
    route: path,
    rendered: overflow.textLength > 0,
    horizontal_overflow: overflow.scrollWidth > overflow.clientWidth + 1,
    recovery_panel_present: panelCount > 0,
    page_errors: pageErrors.slice(0, 5),
  });
}
