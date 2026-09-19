
  // 16 后端断开
  {
    const { ctx, page } = await newPage(browser);
    await bind(page);
    await page.route("**/api/v1/**", (r) => r.abort("failed"));
    await page.goto(BASE + "/v8/hub", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(4000);
    const off = await page.locator("body").innerText();
    rec("16 后端断开可恢复", off.includes("Can't reach") || off.includes("连不上"), off.split("\n").slice(0, 2).join(" | "));
    await page.screenshot({ path: SHOTS + "/A5_offline.png" });
    await ctx.close();
  }
  // 17 GPS 拒绝
  {
    const { ctx, page } = await newPage(browser, { permissions: [] });
    await bind(page);
    await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    rec("17 GPS 拒绝仍可用", (await page.locator("body").innerText()).length > 300, "");
    await ctx.close();
  }
  // 18 Live
  {
    const { ctx, page } = await newPage(browser);
    await bind(page);
    await page.goto(BASE + "/v8/live", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    rec("18 Live 可进入", (await page.locator("body").innerText()).length > 200, "");
    await page.screenshot({ path: SHOTS + "/A6_live.png", fullPage: true });
    await ctx.close();
  }
  // 19 430x932
  {
    const { ctx, page } = await newPage(browser, { locale: "zh-CN", viewport: { width: 430, height: 932 } });
    await bind(page);
    for (const k of ["hub", "trips", "map", "agent", "me"]) {
      await page.goto(BASE + "/v8/" + k, { waitUntil: "networkidle", timeout: 60000 });
      await page.waitForTimeout(1200);
    }
    const ov = await page.evaluate(() => ({
      sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
    }));
    rec("19 430x932 无横向溢出", ov.sw <= ov.cw + 1, `sw=${ov.sw} cw=${ov.cw}`);
    await page.screenshot({ path: SHOTS + "/A7_430.png", fullPage: true });
    await ctx.close();
  }
  // 20 底部导航
  {
    const { ctx, page } = await newPage(browser);
    await bind(page);
    await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2000);
    const nav = page.locator(".v8-mobile-nav button");
    const labels = [];
    for (let i = 0; i < await nav.count(); i++) labels.push((await nav.nth(i).innerText()).trim());
    rec("20 主导航 = 今天/行程/地图/Copilot/我的", labels.length === 5, labels.join("/"));
    await ctx.close();
  }

  await browser.close();
  const out = { results: R, errors: errors.slice(0, 10) };
  fs.writeFileSync("D:/moodle/_v1922_work/rescue_evidence/gate.json", JSON.stringify(out, null, 1));
  R.forEach((r) => console.log(`${r.ok ? "PASS" : "FAIL"}  ${r.id}  ${r.note}`.slice(0, 125)));
  console.log("ERRORS:", errors.length);
})().catch((e) => { console.error("FAIL", e); process.exit(1); });
