import { expect, test } from "@playwright/test";

test.describe("V18 Experience Reference acceptance", () => {
  test("1 · DIRECT What-If stays simulation-only and creates no Agent run", async ({ page, isMobile }) => {
    await page.goto(isMobile ? "/#/copilot" : "/#/today");
    if (!isMobile) {
      await page.getByTestId("copilot-quick-whatif").click();
    } else {
      await page.getByTestId("copilot-quick-whatif").click();
    }
    const assistant = page.getByTestId("copilot-message").last();
    await expect(assistant).toContainText("WHAT_IF");
    await expect(assistant).toContainText("DIRECT");
    await expect(page.getByTestId("agent-run-timeline")).toHaveCount(0);
    await expect(page.getByTestId("timeline-source")).toHaveCount(0);
  });

  test("2 · recorded Hermes multi-step run is labelled RECORDED_FIXTURE and never advances on a timer", async ({ page }) => {
    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("agent-run-timeline")).toBeVisible();
    await expect(page.getByTestId("timeline-source")).toContainText("RECORDED_FIXTURE");
    await expect(page.getByTestId("timeline-step")).toHaveCount(0);

    await page.getByTestId("timeline-next").click();
    await page.getByTestId("timeline-next").click();
    await page.getByTestId("timeline-next").click();
    await expect(page.getByTestId("timeline-step")).toHaveCount(3);

    // No setTimeout/setInterval progress: the count must not move on its own.
    await page.waitForTimeout(1400);
    await expect(page.getByTestId("timeline-step")).toHaveCount(3);

    await page.getByTestId("timeline-replay").click();
    await expect(page.getByTestId("timeline-step")).toHaveCount(9, { timeout: 20_000 });
    await expect(page.getByTestId("timeline-step").last()).toHaveAttribute("data-status", "done");
  });

  test("3 · recovery before/after diff preserves protected commitments", async ({ page }) => {
    await page.goto("/#/recovery");
    await expect(page.getByTestId("recovery-diff")).toBeVisible();
    await expect(page.getByTestId("recovery-before")).toContainText("Haihe River cruise");
    await expect(page.getByTestId("recovery-after")).toContainText("Tianjin Museum indoor window");
    await expect(page.getByTestId("recovery-protected")).toContainText("C4 commitments preserved");
    await expect(page.getByTestId("recovery-cost-delta")).toHaveText("¥0");
    await expect(page.getByTestId("recovery-travel-delta")).toHaveText("+6 min");
  });

  test("4 · Chinese locale renders without horizontal overflow", async ({ page }) => {
    await page.goto("/?locale=zh#/today");
    await expect(page.getByTestId("route-heading")).toContainText("你的下一座城市");
    await expect(page.getByTestId("pulse-now")).toContainText("五大道");
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("5 · reduced motion collapses animation and map camera durations", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/?locale=en#/today");
    await expect(page.locator("html")).toHaveAttribute("data-reduced-motion", "true");
    const duration = await page
      .locator(".pulse-card")
      .first()
      .evaluate((element) => getComputedStyle(element).animationDuration);
    const durationSeconds = Number.parseFloat(duration);
    expect(Number.isFinite(durationSeconds) ? durationSeconds : -1).toBeLessThan(0.01);
    await page.goto("/#/map");
    await expect(page.getByTestId("map-canvas")).toHaveAttribute("data-camera-duration", "0");
  });

  test("6 · mobile map sheet 24/55/90 and 44px touch targets", async ({ page, isMobile }) => {
    test.skip(!isMobile, "mobile viewport only");
    await page.goto("/#/map");
    const sheet = page.getByTestId("map-sheet");
    await expect(sheet).toHaveAttribute("data-sheet-state", "55");

    await page.getByTestId("sheet-24").click();
    await expect(sheet).toHaveAttribute("data-sheet-state", "24");
    await page.waitForTimeout(400);
    const height24 = (await sheet.boundingBox())?.height ?? 0;

    await page.getByTestId("sheet-90").click();
    await expect(sheet).toHaveAttribute("data-sheet-state", "90");
    await page.waitForTimeout(400);
    const height90 = (await sheet.boundingBox())?.height ?? 0;

    expect(height90).toBeGreaterThan(height24);

    const heights = await page
      .getByTestId("bottom-nav-item")
      .evaluateAll((elements) => elements.map((element) => element.getBoundingClientRect().height));
    expect(heights.length).toBe(5);
    for (const height of heights) expect(height).toBeGreaterThanOrEqual(44);

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

  test("7 · failed and stopped fixtures are truthful and long tool names stay contained", async ({ page }) => {
    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("agent-run-timeline")).toBeVisible();

    await page.getByTestId("fixture-failed").click();
    await expect(page.getByTestId("timeline-step")).toHaveCount(0);
    const failedSteps = page.getByTestId("timeline-step");
    const failedTotal = 6;
    for (let index = 0; index < failedTotal; index += 1) {
      await page.getByTestId("timeline-next").click();
    }
    await expect(failedSteps).toHaveCount(failedTotal);
    await expect(failedSteps.last()).toHaveAttribute("data-status", "failed");

    await page.getByTestId("fixture-stopped").click();
    await expect(page.getByTestId("timeline-step")).toHaveCount(0);
    for (let index = 0; index < 3; index += 1) {
      await page.getByTestId("timeline-next").click();
    }
    await expect(page.getByTestId("timeline-step").last()).toHaveAttribute("data-status", "stopped");

    const tool = page.locator(".timeline-step__tool").last();
    await expect(tool).toContainText("citynexus.search_city_services_for_rain_safe_indoor_activity_candidates");
    const toolBox = await tool.boundingBox();
    const viewport = page.viewportSize();
    expect(toolBox && viewport ? toolBox.width <= viewport.width : false).toBeTruthy();

    await page.getByTestId("timeline-stop").click();
    await expect(page.locator(".fixture-banner.stopped").first()).toBeVisible();
  });
