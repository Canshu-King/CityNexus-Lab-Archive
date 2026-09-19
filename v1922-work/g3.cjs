
  // 6-15 demo 行程
  await fetch(`${API}/journeys/${JID}/plans/generate`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  {
    const { ctx, page } = await newPage(browser, { locale: "zh-CN" });
    await bind(page);
    await page.goto(BASE + "/v8/hub", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(3000);
    const cards = await page.locator('[data-testid="plan-cmp-card"]').count();
    rec("06 比较候选方案", cards >= 2, `cards=${cards}`);
    await page.screenshot({ path: SHOTS + "/A2_compare.png", fullPage: true });
    await page.locator('[data-testid="plan-cmp-choose"]').first().click();
    await page.waitForTimeout(4000);
    rec("07 采用方案", await page.locator('[data-testid="plan-comparison"]').count() === 0, "");
    await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    const stops = await page.locator('[data-testid="trip-stop"]').count();
    rec("08 逐日行程详情", stops > 0, `stops=${stops}`);
    const tripsBody = await page.locator("body").innerText();
    rec("09 活动详情(时间+时长)", /\d{1,2}:\d{2}/.test(tripsBody) && (tripsBody.includes("h ") || tripsBody.includes("小时")), "");
    rec("10 住宿入口可见", tripsBody.includes("住宿") || tripsBody.includes("Stay") || tripsBody.includes("STAY"), "");
    await page.screenshot({ path: SHOTS + "/A3_itinerary.png", fullPage: true });
    await page.goto(BASE + "/v8/map", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    const mapBody = await page.locator("body").innerText();
    rec("11 地图正确/诚实空态", !mapBody.includes("Tianjin") && !mapBody.includes("天津"), mapBody.includes("No map location") || mapBody.includes("尚未获取") ? "empty-state" : "rendered");
    await page.goto(BASE + "/v8/agent", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2000);
    await page.locator('[data-testid="v15-copilot-input"]').fill("鼓浪屿好玩吗");
    await page.locator('[data-testid="v15-copilot-submit"]').click();
    await page.waitForTimeout(4000);
    const agentBody = await page.locator("body").innerText();
    rec("12 Copilot 回答问题", agentBody.length > 400, "");
    rec("13 无原始枚举泄露", !/REQUEST_PLACE_SEARCH|REQUEST_REPLAN|ACCEPT_REPLAN|PlanVersion|semantic_key|C4_Anchored/.test(agentBody), "");
    await page.goto(BASE + "/v8/trips", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2500);
    rec("14 预订/钱包不白屏", (await page.locator("body").innerText()).length > 300, "");
    const before = (await page.locator("body").innerText()).slice(0, 24);
    await page.locator('[data-testid="topbar-language"]').first().click().catch(() => {});
    await page.waitForTimeout(1200);
    const afterTxt = await page.locator("body").innerText();
    rec("15 语言切换不破坏流程", before !== afterTxt.slice(0, 24) && afterTxt.length > 300, `${before.split("\n")[0]} -> ${afterTxt.slice(0, 24).split("\n")[0]}`);
    await page.screenshot({ path: SHOTS + "/A4_lang.png", fullPage: true });
    await ctx.close();
  }
