
  // ---- 16. Copilot: a real question in Chinese ----
  await go("/v8/agent");
  await page.waitForTimeout(1500);
  const dockOpen = await has('[data-testid="v18-copilot-dock"]');
  const askBox = page.locator('.cn-copilot-form textarea');
  if (await askBox.count()) {
    await askBox.fill("鼓浪屿好玩吗？");
    await page.locator('.cn-copilot-form button[type="submit"]').click();
  } else if (await has('[data-testid="agent-command"]')) {
    await page.locator('[data-testid="agent-command"]').fill("鼓浪屿好玩吗？");
    await page.locator('[data-testid="run-agent-command"]').click();
  }
  let answer = "";
  for (let i = 0; i < 45; i++) {
    await page.waitForTimeout(2000);
    answer = (await txt('.cn-copilot-history')) || (await txt('[data-testid="agent-mission-result"]'));
    if (answer.length > 60 && !/思考|working|正在/.test(answer.slice(-12))) break;
  }
  rec("/v8/agent", "copilot-question", dockOpen ? (answer.length > 40 ? "answered" : "empty") : "no-dock",
      answer.replace(/\n/g, " ").slice(0, 170));
  await shot("C1_17_copilot");
  const copilotUseful = /鼓浪屿|轮渡|日光岩|菽庄|海|景点|建议|可以/.test(answer);

  // ---- 17. map with real Xiamen coordinates ----
  await go("/v8/map");
  await page.waitForTimeout(4000);
  const mapPanel = await has('[data-testid="v8-maplibre-panel"]');
  const mapEmpty = await has('[data-testid="v8-map-empty"]');
  const canvasBox = await page.locator('[data-testid="v8-maplibre-panel"] canvas').first().boundingBox().catch(() => null);
  rec("/v8/map", "map", mapPanel ? "panel" : mapEmpty ? "empty" : "MISSING",
      `canvas=${canvasBox ? `${Math.round(canvasBox.width)}x${Math.round(canvasBox.height)}` : "none"}`);
  await shot("C1_18_map");
  if (!mapPanel) throw new Error("the map panel did not render for the Xiamen trip");

  // ---- 18. Live journey ----
  await go("/v8/live");
  await page.waitForTimeout(5000);
  const liveNext = await txt('[data-testid="live-next"]');
  const liveDisruption0 = await has('[data-testid="live-disruption"]');
  rec("/v8/live", "live-open", liveNext ? "has-next" : "no-next",
      `next="${liveNext}" disruption=${liveDisruption0}`);
  await shot("C1_19_live");

  // ---- 19. targeted mutable-POI disruption -> governed replan ----
  const exp = await api("GET", `/journeys/${JID}/experience`);
  const liveActs = exp.json?.active_plan?.activities ?? [];
  const mutable = liveActs.find((a) => !a.locked && String(a.title || "").includes("景点"));
  const target = mutable ?? liveActs.find((a) => !a.locked);
  if (!target) throw new Error("no mutable activity to disrupt");
  const beforeIds = liveActs.map((a) => a.id).join(",");
  const beforeTitles = liveActs.map((a) => String(a.title).slice(0, 14)).join(" / ");
  const ev = await api("POST", `/journeys/${JID}/events`, {
    event_type: "CLOSURE", severity: "MAJOR", affected_activity_id: target.id,
    provenance: "USER_REPORTED", payload: { source: "traveller-report" },
  });
  rec("/api", "disruption-event", ev.status, `CLOSURE -> ${String(target.title).slice(0, 20)} (${ev.json?.id ? "id ok" : JSON.stringify(ev.json).slice(0, 120)})`);
  const prop = await api("POST", `/journeys/${JID}/replans`, { trigger_event_id: ev.json?.id });
  const preserved = prop.json?.locked_commitments_preserved;
  const diff = prop.json?.diff ?? {};
  rec("/api", "replan-proposal", prop.status,
      `preserved=${preserved} removed=${(diff.removed ?? []).length} added=${(diff.added ?? []).length} ${prop.json?.error?.code ?? ""}`);
  if (!prop.json?.id) throw new Error("no replan proposal: " + JSON.stringify(prop.json).slice(0, 200));

  // ---- 20. the traveller sees it on Live and accepts it in the UI ----
  await go("/v8/live");
  await page.waitForTimeout(5000);
  const sawDisruption = await has('[data-testid="live-disruption"]');
  const sawProposal = await has('[data-testid="live-proposal"]');
  const affected = await txt('[data-testid="live-affected"]');
  const unchanged = await txt('[data-testid="live-unchanged"]');
  rec("/v8/live", "disruption-visible", sawDisruption ? "shown" : "hidden",
      `proposal=${sawProposal} affected="${affected}" unchanged="${unchanged.slice(0, 60)}"`);
  await shot("C1_20_live_disruption");
  if (!sawProposal) throw new Error("the traveller cannot see the replan proposal");
  await page.locator('[data-testid="live-accept"]').first().click();
  let accepted = false;
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(2000);
    const msg = await txt('[data-testid="live-message"]');
    if (/已|updated/.test(msg)) { accepted = true; break; }
    if (await has('[data-testid="live-handled"]')) { accepted = true; break; }
  }
  rec("/v8/live", "accept-replan", accepted ? "accepted" : "not-accepted", await txt('[data-testid="live-message"]'));
  await shot("C1_21_live_accepted");
