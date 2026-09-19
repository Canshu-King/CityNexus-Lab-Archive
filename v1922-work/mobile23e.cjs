
async function staleFlow(vp, page, results, pageErrors) {
  await api("/demo/reset", { method: "POST" });
  await api(`/journeys/${JID}/plans/generate`, { method: "POST", body: JSON.stringify({}) });
  const plans = await api(`/journeys/${JID}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  if (list.length) {
    await api(`/journeys/${JID}/plans/${list[0].id}/select`, { method: "POST" });
  }
  const { execFileSync } = require("node:child_process");
  try {
    execFileSync(
      process.env.LAB_PY || "D:/moodle/CityNexus/.venv/Scripts/python.exe",
      [process.env.EXPIRE_SCRIPT, list[0].id],
      { stdio: "pipe" },
    );
  } catch {
    // the stale assertions below still report the observed behaviour
  }
  const listed = await api(`/journeys/${JID}/plans`);
  const flagged = (Array.isArray(listed.body) ? listed.body : []).find(
    (p) => p.id === list[0].id,
  );
  const started = await api(`/journeys/${JID}/start`, { method: "POST" });
  const experience = await api(`/journeys/${JID}/experience`);
  await openRoute(page, "/v8/authoritative");
  const panelVisible =
    (await page.locator('[data-testid="recovery-required-panel"]').count()) > 0;
  const flags = (experience.body && experience.body.experience_flags) || {};
  results.flows.push({
    viewport: vp.name,
    flow: "STALE_CANDIDATE_WARNING",
    candidate_flagged_stale: flagged ? flagged.stale : null,
    candidate_selectable: flagged ? flagged.selectable : null,
    start_status: started.status,
    start_message: String(
      (started.body && started.body.error && started.body.error.message) || "",
    ).slice(0, 120),
    journey_status: (await api(`/journeys/${JID}`)).body.status,
    flags_staleness: flags.staleness,
    panel_visible: panelVisible,
    page_errors: pageErrors.slice(0, 3),
  });
}

async function gpsFlow(browser, vp, results) {
  for (const gps of ["allowed", "denied"]) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
      permissions: gps === "allowed" ? ["geolocation"] : [],
      geolocation: gps === "allowed" ? { latitude: 39.1, longitude: 117.18 } : undefined,
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    await openRoute(page, "/v8/live");
    const state = await page.evaluate(() => ({
      textLength: document.body ? document.body.innerText.length : 0,
      overflow:
        document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    }));
    results.flows.push({
      viewport: vp.name,
      flow: `GPS_${gps.toUpperCase()}`,
      rendered: state.textLength > 0,
      horizontal_overflow: state.overflow,
      page_errors: errors.slice(0, 3),
    });
    await context.close();
  }
}
