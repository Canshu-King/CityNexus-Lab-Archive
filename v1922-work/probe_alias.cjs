const L = require("./lab_lib.cjs");
const JID = process.argv[2];
(async () => {
  const b = await L.launch();
  // desktop viewport so the Stay Explorer route is the intended surface
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, locale: "zh-CN" });
  const p = await ctx.newPage();
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const read = async () => ({
    path: new URL(p.url()).pathname,
    stayExplorer: await p.locator('[data-testid="v8-stay-explorer"]').count(),
    tripsTabs: await p.locator('[data-testid="trips-tabs"]').count(),
    breadcrumb: (await p.locator(".v8-breadcrumb").innerText().catch(() => "")).replace(/\s+/g, " ").trim(),
  });
  // 1) navigate by clicking the desktop nav item
  await p.goto(L.BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(5000);
  await p.getByRole("button", { name: /住宿选择|Stay Explorer/ }).first().click().catch(async () => {
    await p.locator(".v8-nav button", { hasText: "住宿选择" }).first().click();
  });
  await p.waitForTimeout(4000);
  console.log("after nav click:", JSON.stringify(await read()));
  await p.screenshot({ path: L.SHOTS + "/probe_alias_after_click.png" }).catch(() => {});
  // 2) hard refresh on that URL
  await p.reload({ waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  console.log("after reload   :", JSON.stringify(await read()));
  await p.screenshot({ path: L.SHOTS + "/probe_alias_after_reload.png" }).catch(() => {});
  // 3) deep link
  await p.goto(L.BASE + "/v8/stay", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  console.log("deep link      :", JSON.stringify(await read()));
  // 4) other desktop aliases
  for (const r of ["/v8/bookings", "/v8/wallet", "/v8/itinerary", "/v8/home"]) {
    await p.goto(L.BASE + r, { waitUntil: "domcontentloaded" }); await p.waitForTimeout(3500);
    console.log(r, "->", JSON.stringify(await read()));
  }
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
