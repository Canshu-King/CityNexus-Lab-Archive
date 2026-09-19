import { expect, test } from "@playwright/test";

const isDesktopProject = () => test.info().project.name === "desktop-chromium";
const isMobileProject = () => test.info().project.name !== "desktop-chromium";

async function expandTimelineIfCompact(page: import("@playwright/test").Page) {
  const expand = page.getByTestId("timeline-expand");
  if ((await expand.count()) > 0 && (await expand.isVisible())) {
    await expand.click({ force: true });
  }
}

test.describe("V18.2 traveler-first experience acceptance", () => {
  test("1 · desktop shell keeps SYSTEM secondary and Journey Pulse primary", async ({ page }) => {
    test.skip(!isDesktopProject(), "desktop shell only");
    await page.goto("/#/journey");
    await expect(page.getByTestId("journey-pulse")).toBeVisible();
    await expect(page.getByTestId("pulse-now")).toContainText("Five Great Avenues");
    await expect(page.getByTestId("pulse-next")).toContainText("Haihe River cruise");
    await expect(page.getByTestId("pulse-risk")).toContainText("Rain band");
    await expect(page.getByTestId("pulse-action")).toContainText("Review rain-safe recovery");
    await expect(page.getByTestId("nav-journey")).toBeVisible();
    await expect(page.getByTestId("nav-stay")).toBeVisible();
    await expect(page.getByTestId("nav-wallet")).toBeVisible();
    // SYSTEM is secondary and collapsed by default.
    await expect(page.getByTestId("nav-recovery")).toHaveCount(0);
    await page.locator(".desktop-nav__group-toggle").click();
    await expect(page.getByTestId("nav-recovery")).toBeVisible();
    await expect(page.getByTestId("nav-intelligence")).toBeVisible();
    await expect(page.getByTestId("nav-twin")).toBeVisible();
    // Primary view must not lead with internal architecture.
    const pulseText = await page.getByTestId("journey-pulse").innerText();
    expect(pulseText).not.toContain("PlanVersion");
    expect(pulseText).not.toContain("CP-SAT");
    await expect(page.getByTestId("technical-evidence")).not.toHaveAttribute("open", "");
  });

  test("2 · journey page orders Pulse → Today timeline → Live map and keeps detail collapsed", async ({ page }) => {
    await page.goto("/#/journey");
    const pulse = page.getByTestId("journey-pulse");
    const timeline = page.getByTestId("today-timeline");
    const map = page.getByTestId("map-canvas");
    await expect(pulse).toBeVisible();
    await expect(timeline).toBeVisible();
    await expect(map).toBeVisible();
    const pulseBox = await pulse.boundingBox();
    const timelineBox = await timeline.boundingBox();
    const mapBox = await map.boundingBox();
    expect(pulseBox && timelineBox && mapBox ? pulseBox.y < Math.min(timelineBox.y, mapBox.y) : false).toBeTruthy();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("3 · DIRECT What-If creates no Agent run", async ({ page }) => {
    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-whatif").click();
    const assistant = page.getByTestId("copilot-message").last();
    await expect(assistant).toContainText("WHAT_IF");
    await expect(assistant).toContainText("DIRECT");
    await expect(page.getByTestId("agent-run-timeline")).toHaveCount(0);
  });

  test("4 · recorded Hermes run is truthful, approval-gated, and never advances on a timer", async ({ page }) => {
    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expandTimelineIfCompact(page);
    const timeline = page.getByTestId("agent-run-timeline");
    await expect(timeline).toBeVisible();
    await expect(timeline).toHaveAttribute("data-source", "RECORDED_FIXTURE");
    await expect(page.getByTestId("timeline-source")).toContainText("RECORDED_FIXTURE");
    await expect(page.getByTestId("timeline-step")).toHaveCount(0);

    // No timer-driven progress: count stays put while we wait.
    await page.waitForTimeout(1500);
    await expect(page.getByTestId("timeline-step")).toHaveCount(0);

    for (let index = 0; index < 14; index += 1) {
      await page.getByTestId("timeline-next").click();
    }
    await expect(page.getByTestId("timeline-step")).toHaveCount(14);
    await expect(timeline).toHaveAttribute("data-run-status", "approval_required");
    await expect(page.getByTestId("timeline-step").first()).toContainText("Understood request");
    await expect(page.getByTestId("timeline-step").nth(3)).toContainText(/Check/);
    await expect(page.getByTestId("approval-panel")).toBeVisible();
    await expect(page.getByTestId("approval-approve")).toHaveClass(/btn--approve/);
    await expect(page.getByTestId("approval-reject")).toHaveClass(/btn--reject/);
    await page.getByTestId("approval-approve").click();
    await expect(page.getByTestId("approval-panel")).toHaveAttribute("data-approval-state", "approved");
    await expect(page.getByTestId("approval-state-copy")).toContainText("Approved");
  });

  test("5 · failed and stopped runs stay readable; long tool names stay contained", async ({ page }) => {
    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("agent-run-timeline")).toBeVisible();

    await page.getByTestId("fixture-failed").click();
    await expandTimelineIfCompact(page);
    for (let index = 0; index < 6; index += 1) await page.getByTestId("timeline-next").click();
    await expect(page.getByTestId("agent-run-timeline")).toHaveAttribute("data-run-status", "failed");
    await expect(page.getByTestId("timeline-step").last()).toHaveAttribute("data-status", "failed");
    await expect(page.getByTestId("timeline-step").last()).toContainText("provider");

    await page.getByTestId("fixture-stopped").click();
    await expandTimelineIfCompact(page);
    for (let index = 0; index < 5; index += 1) await page.getByTestId("timeline-next").click();
    await expect(page.getByTestId("agent-run-timeline")).toHaveAttribute("data-run-status", "stopped");
    await expect(page.getByTestId("timeline-step").last()).toHaveAttribute("data-status", "stopped");

    const tool = page.locator(".timeline-step__tool").last();
    await expect(tool).toContainText("citynexus.search_city_services_for_rain_safe_indoor_activity_candidates");
    const toolBox = await tool.boundingBox();
    const viewport = page.viewportSize();
    expect(toolBox && viewport ? toolBox.width <= viewport.width : false).toBeTruthy();
  });

  test("6 · recovery diff explains why, protects commitments, and makes approval distinct", async ({ page }) => {
    await page.goto("/#/recovery");
    await expect(page.getByTestId("recovery-diff")).toBeVisible();
    await expect(page.getByTestId("recovery-before")).toContainText("Ancient Culture Street");
    await expect(page.getByTestId("recovery-after")).toContainText("Tianjin Museum");
    await expect(page.getByTestId("recovery-why")).toContainText("Heavy rain");
    await expect(page.getByTestId("recovery-protected-list")).toContainText("Haihe River cruise");
    await expect(page.getByTestId("recovery-time-delta")).toHaveText("0 min");
    await expect(page.getByTestId("recovery-cost-delta")).toHaveText("¥0");
    await expect(page.getByTestId("recovery-walking-delta")).toHaveText("-14 min");
    await expect(page.getByTestId("recovery-travel-delta")).toHaveText("+6 min");
    await expect(page.getByTestId("recovery-approve")).toHaveClass(/btn--approve/);
    await expect(page.getByTestId("recovery-reject")).toHaveClass(/btn--reject/);
    await page.getByTestId("recovery-approve").click();
    await expect(page.getByTestId("recovery-approval")).toHaveAttribute("data-approval-state", "approved");
    await page.getByTestId("recovery-review").click();
    await expect(page.getByTestId("recovery-approval")).toHaveAttribute("data-approval-state", "review_requested");
    await expect(page.getByTestId("recovery-approval-state")).toContainText("Changes requested");
  });

  test("7 · mobile mini composer and bottom sheet surface mission, step, approval", async ({ page }) => {
    test.skip(!isMobileProject(), "mobile only");
    await page.goto("/#/journey");
    const mini = page.getByTestId("copilot-mini-composer");
    await expect(mini).toBeVisible();
    await expect(mini).toHaveAttribute("data-mini-state", "idle");
    await expect(mini.locator("input")).toHaveAttribute("placeholder", /Ask CityNexus/);
    await mini.locator("input").fill("Find a rain-safe alternative");
    await mini.locator("button").click();
    await expect(page.getByTestId("copilot-dock")).toHaveClass(/is-open/);
    await expect(page.getByTestId("copilot-mission")).toContainText("Rain-safe");
    await expect(page.getByTestId("timeline-expand")).toBeVisible();
    // Full technical timeline is hidden until expanded.
    await expect(page.getByTestId("timeline-step")).toHaveCount(0);
    await page.getByTestId("timeline-expand").focus();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("timeline-collapse")).toBeVisible();
    await page.getByTestId("timeline-next").click();
    await expect(page.getByTestId("timeline-step")).toHaveCount(1);
    await page.getByTestId("timeline-collapse").click();
    await expect(page.getByTestId("timeline-step")).toHaveCount(0);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("8 · mobile map sheet content changes by 24/55/90 state", async ({ page }) => {
    test.skip(!isMobileProject(), "mobile only");
    await page.goto("/#/map");
    await page.getByTestId("sheet-24").click();
    await expect(page.getByTestId("sheet-content-24")).toContainText("Now");
    await page.getByTestId("sheet-55").click();
    await expect(page.getByTestId("sheet-content-55")).toContainText("Route");
    await page.getByTestId("sheet-90").click();
    await expect(page.getByTestId("sheet-content-90")).toContainText("Tianjin Museum");
    const heights = await page
      .getByTestId("bottom-nav-item")
      .evaluateAll((elements) => elements.map((element) => element.getBoundingClientRect().height));
    expect(heights.length).toBe(5);
    for (const height of heights) expect(height).toBeGreaterThanOrEqual(44);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("9 · Chinese long content stays readable without horizontal overflow", async ({ page }) => {
    await page.goto("/?locale=zh#/journey");
    await expect(page.getByTestId("route-heading")).toContainText("你的下一座城市");
    await expect(page.getByTestId("pulse-now")).toContainText("五大道");
    await page.goto("/?locale=zh#/recovery");
    await expect(page.getByTestId("recovery-why")).toContainText("强降雨");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("10 · reduced motion keeps state clarity with zero-duration motion", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/?locale=en#/journey");
    await expect(page.locator("html")).toHaveAttribute("data-reduced-motion", "true");
    const duration = await page
      .locator(".pulse-card")
      .first()
      .evaluate((element) => getComputedStyle(element).animationDuration);
    const seconds = Number.parseFloat(duration);
    expect(Number.isFinite(seconds) ? seconds : -1).toBeLessThan(0.01);
    await page.goto("/#/map");
    await expect(page.getByTestId("map-canvas")).toHaveAttribute("data-camera-duration", "0");
  });

  test("11 · failure and offline states show a useful next action", async ({ page }) => {
    for (const status of ["hermes_unavailable", "deepseek_unavailable", "provider_unavailable", "offline_stale"]) {
      await page.goto(`/?runtime=${status}#/journey`);
      const banner = page.getByTestId("runtime-status-banner");
      await expect(banner).toBeVisible();
      await expect(banner).toHaveAttribute("data-status", status);
      await expect(banner.locator("button")).toBeVisible();
      await expect(page.getByTestId("journey-pulse")).toBeVisible();
    }
  });

  test("12 · Copilot is keyboard openable and Escape returns focus", async ({ page }) => {
    test.skip(!isDesktopProject(), "desktop keyboard flow");
    await page.goto("/#/journey");
    const dock = page.getByTestId("copilot-dock");
    await expect(dock).toHaveClass(/is-open/);
    await page.keyboard.press("Escape");
    await expect(dock).toHaveClass(/is-collapsed/);
    const edge = dock.locator(".copilot-edge");
    await expect(edge).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(dock).toHaveClass(/is-open/);
    await expect(page.getByTestId("copilot-input")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dock).toHaveClass(/is-collapsed/);
    await expect(edge).toBeFocused();
  });

  test("13 · key routes produce no console or page errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
    for (const route of ["journey", "live", "map", "copilot", "wallet", "recovery", "intelligence", "twin", "me"]) {
      await page.goto(`/#/${route}`);
      await expect(page.getByTestId("route-heading")).toBeVisible();
    }
    expect(errors).toEqual([]);
  });

  test("14 · unresolved and stale evidence block approval with a clear next action", async ({ page }) => {
    await page.goto("/?evidence=unresolved#/recovery");
    await expect(page.getByTestId("recovery-diff")).toHaveAttribute("data-evidence-state", "unresolved");
    await expect(page.locator(".recovery__evidence")).toHaveAttribute("data-evidence-state", "unresolved");
    await expect(page.getByTestId("recovery-approve")).toBeDisabled();
    await expect(page.getByTestId("recovery-approval-state")).toContainText("Proposal only");
    await page.goto("/?evidence=stale#/recovery");
    await expect(page.locator(".recovery__evidence")).toHaveAttribute("data-evidence-state", "stale");
    await expect(page.getByTestId("recovery-approve")).toBeDisabled();
  });
});
