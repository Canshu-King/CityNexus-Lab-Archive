const L = require("./lab_lib.cjs");
const JID = process.argv[2];
(async () => {
  const b = await L.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, locale: "zh-CN" });
  const p = await ctx.newPage();
  const errs = []; L.attachErrors(p, errs);
  await p.addInitScript(`window.localStorage.setItem("citynexus.v8.journey_id", ${JSON.stringify(JID)});`);
  const read = async () => ({
    path: new URL(p.url()).pathname,
    stayExplorer: await p.locator('[data-testid="v8-stay-explorer"]').count(),
    tripsTabs: await p.locator('[data-testid="trips-tabs"]').count(),
    breadcrumb: (await p.locator(".v8-breadcrumb").innerText().catch(() => "")).replace(/\s+/g, " ").trim(),
  });
  await p.goto(L.BASE + "/v8/hub", { waitUntil: "domcontentloaded" }); await p.waitForTimeout(5000);
  const navBtn = p.locator(".v8-nav button").filter({ hasText: "住宿选择" });
  console.log("nav buttons matching 住宿选择:", await navBtn.count());
  if (await navBtn.count()) { await navBtn.first().click(); await p.waitForTimeout(4000); }
  console.log("after nav click :", JSON.stringify(await read()));
  await p.screenshot({ path: L.SHOTS + "/probe_route_after_click.png", fullPage: true }).catch(() => {});
  await p.reload({ waitUntil: "domcontentloaded" }); await p.waitForTimeout(6000);
  console.log("after reload    :", JSON.stringify(await read()));
  await p.screenshot({ path: L.SHOTS + "/probe_route_after_reload.png", fullPage: true }).catch(() => {});
  for (const r of ["/v8/stay", "/v8/stays", "/v8/discover", "/v8/studio", "/v8/intelligence", "/v8/twin", "/v8/authoritative", "/v8/bookings"]) {
    await p.goto(L.BASE + r, { waitUntil: "domcontentloaded" }); await p.waitForTimeout(3000);
    console.log(r.padEnd(20), "->", JSON.stringify(await read()));
  }
  console.log("ERRS", errs.slice(0, 5));
  await b.close();
})().catch((e) => { console.error("FAIL", e.message); process.exit(1); });
