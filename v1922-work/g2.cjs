
(async () => {
  await fetch(API + "/demo/reset", { method: "POST" });
  const browser = await chromium.launch({ channel: "chrome" });

  // 1-6 全新用户
  {
    const { ctx, page } = await newPage(browser, { locale: "zh-CN" });
    await page.goto(BASE + "/", { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForTimeout(2000);
    rec("01 / 进入新产品", await page.locator('[data-testid="trial-step1-body"]').count() > 0, "");
    await page.locator('[data-testid="trial-city"]').fill("厦门");
    await page.locator('[data-testid="trial-arrival"]').fill("厦门高崎国际机场");
    await page.locator('[data-testid="trial-departure"]').fill("厦门北站");
    const inf = await page.locator('[data-testid="trial-inferred"]').innerText().catch(() => "");
    rec("02 自动推断国家/货币/时区", inf.includes("中国") && inf.includes("人民币"), inf);
    await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(400);
    await page.locator('[data-testid="trial-next"]').click(); await page.waitForTimeout(400);
    rec("03 三步创建流程", await page.locator('[data-testid="trial-step3-body"]').count() > 0, "");
    await page.locator('[data-testid="trial-create"]').click();
    await page.waitForTimeout(5000);
    rec("04 AI 规划面板打开", await page.locator('[data-testid="plan-ai-sheet"]').count() > 0, "");
    await page.locator('[data-testid="plan-ai-input"]').fill("我和朋友两个人去厦门，想轻松一点，想去鼓浪屿，不想太赶。");
    await page.locator('[data-testid="plan-ai-submit"]').click();
    await page.waitForTimeout(4500);
    const res = await page.locator('[data-testid="plan-ai-result"]').innerText().catch(() => "");
    rec("05 诚实规划进度/结果", res.length > 5, res.split("\n")[0]);
    await page.screenshot({ path: SHOTS + "/A1_create_ai.png", fullPage: true });
    await ctx.close();
  }
