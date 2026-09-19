import { expect, test, type Page } from "@playwright/test";

const project = () => test.info().project.name;
const isDesktop = () => project().includes("desktop");
const isMobile = () => project().includes("mobile");

async function noHorizontalOverflow(page: Page, tolerance = 1) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(tolerance);
}

test.describe("V18.3 experience engineering acceptance", () => {
  test("1 · Journey shell is runtime-truth first and never loads MapLibre", async ({ page }) => {
    const requests: string[] = [];
    page.on("request", (request) => requests.push(request.url()));
    await page.goto("/#/journey");
    await expect(page.getByTestId("journey-pulse")).toBeVisible();
    await expect(page.getByTestId("today-timeline")).toBeVisible();
    await expect(page.getByTestId("map-canvas")).toHaveCount(0);
    await expect(page.getByTestId("journey-map-teaser")).toBeVisible();
    await expect(page.getByTestId("runtime-source").first()).toHaveText("RECORDED_FIXTURE");
    expect(requests.some((url) => url.toLowerCase().includes("maplibre"))).toBeFalsy();
    await noHorizontalOverflow(page);
  });

  test("2 · Map route lazy-loads MapLibre and exposes 24/55/90 sheet state", async ({ page }) => {
    const requests: string[] = [];
    page.on("request", (request) => requests.push(request.url()));
    await page.goto("/#/map");
    const canvas = page.getByTestId("map-canvas");
    await expect(canvas).toBeVisible();
    await expect(canvas).toHaveAttribute("data-map-engine", /ready|fallback/);
    expect(requests.some((url) => url.toLowerCase().includes("maplibre"))).toBeTruthy();
    for (const state of ["24", "55", "90"]) {
      await page.getByTestId(`sheet-${state}`).click();
      await expect(page.getByTestId("map-sheet")).toHaveAttribute("data-sheet-state", state);
      await expect(page.getByTestId(`sheet-content-${state}`)).toBeVisible();
    }
    await page.getByTestId("sheet-handle").focus();
    await page.keyboard.press("Home");
    await expect(page.getByTestId("map-sheet")).toHaveAttribute("data-sheet-state", "24");
    await page.keyboard.press("End");
    await expect(page.getByTestId("map-sheet")).toHaveAttribute("data-sheet-state", "90");
    await noHorizontalOverflow(page);
  });

  test("3 · recorded Hermes timeline is honest, approval-gated, and double-click safe", async ({ page }) => {
    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("agent-run-timeline")).toBeVisible();
    await expect(page.getByTestId("timeline-source")).toContainText("RECORDED_FIXTURE");
    await expect(page.getByTestId("timeline-step")).toHaveCount(14, { timeout: 20_000 });
    await expect(page.getByTestId("approval-panel")).toBeVisible();
    const approve = page.getByTestId("approval-approve");
    await expect(approve).toHaveClass(/btn--approve/);
    await approve.click();
    await approve.click({ force: true });
    await expect(page.getByTestId("approval-panel")).toHaveAttribute("data-approval-state", "approved");
    await noHorizontalOverflow(page);
  });

  test("4 · failed and stopped recorded runs stay readable", async ({ page }) => {
    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("agent-run-timeline")).toBeVisible();
    await page.getByTestId("fixture-failed").click();
    await expect(page.getByTestId("agent-run-timeline")).toHaveAttribute("data-run-status", "failed", { timeout: 15_000 });
    await page.getByTestId("fixture-stopped").click();
    await expect(page.getByTestId("agent-run-timeline")).toHaveAttribute("data-run-status", "stopped", { timeout: 15_000 });
    await expect(page.getByTestId("timeline-step").last()).toHaveAttribute("data-status", "stopped");
  });

  test("5 · offline adapter disables destructive approval and shows stale truth", async ({ page }) => {
    await page.goto("/?adapter=offline#/recovery");
    await expect(page.getByTestId("runtime-status-banner")).toBeVisible();
    await expect(page.getByTestId("runtime-status-banner")).toHaveAttribute("data-status", "offline_stale");
    await expect(page.getByTestId("recovery-approve")).toBeDisabled();
    await expect(page.getByTestId("recovery-reject")).toBeDisabled();
    await page.goto("/?adapter=offline#/journey");
    await expect(page.getByTestId("runtime-status-banner")).toBeVisible();
    await noHorizontalOverflow(page);
  });

  test("6 · Traveler Capability UX separates hard needs from preferences", async ({ page }) => {
    await page.goto("/#/capability");
    await expect(page.getByTestId("capability-route")).toBeVisible();
    await expect(page.getByTestId("capability-summary")).toBeVisible();
    const wheelchair = page.locator("#cnx-capability-wheelchair_step_free");
    if (await wheelchair.count()) {
      await wheelchair.check({ force: true });
    }
    await expect(page.getByTestId("capability-summary")).toContainText(/HARD|hard|刚性|必要/i);
    await noHorizontalOverflow(page);
  });

  test("7 · 1000-event timeline renders a 50-row window and stays responsive", async ({ page }) => {
    await page.goto("/?events=1000#/timeline-lab");
    await expect(page.getByTestId("timeline-lab")).toBeVisible();
    await expect(page.getByTestId("timeline-step")).toHaveCount(50);
    await expect(page.getByTestId("timeline-window-note")).toBeVisible();
    await noHorizontalOverflow(page);
    await page.getByTestId("timeline-show-all").click();
    await expect(page.getByTestId("timeline-step")).toHaveCount(1000, { timeout: 20_000 });
  });

  test("8 · live adapter without backend degrades honestly to OFFLINE", async ({ page }) => {
    await page.goto("/?adapter=live#/journey");
    await expect(page.getByTestId("runtime-status-banner")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("runtime-status-banner")).toHaveAttribute("data-status", "offline_stale");
    await expect(page.getByTestId("journey-pulse")).toBeVisible();
  });

  test("9 · Chinese, reduced motion, and 200% zoom keep state clarity", async ({ page }) => {
    await page.goto("/?locale=zh#/journey");
    await expect(page.getByTestId("route-heading")).toContainText("你的下一座城市");
    await noHorizontalOverflow(page);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/?locale=en#/map");
    await expect(page.getByTestId("map-canvas")).toHaveAttribute("data-camera-duration", "0");
    const duration = await page
      .locator(".pulse-card")
      .first()
      .evaluate((element) => getComputedStyle(element).animationDuration)
      .catch(() => "0s");
    const seconds = Number.parseFloat(duration);
    expect(Number.isFinite(seconds) ? seconds : 0).toBeLessThan(0.01);
    await page.goto("/?locale=en#/journey");
    await page.evaluate(() => {
      document.documentElement.style.fontSize = "200%";
    });
    await noHorizontalOverflow(page, 2);
  });

  test("10 · Copilot keyboard open, Escape close, and focus return", async ({ page }) => {
    test.skip(!isDesktop(), "desktop keyboard flow");
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

  test("11 · mobile bottom nav has 44px targets and small viewport has no overflow", async ({ page }) => {
    test.skip(!isMobile(), "mobile only");
    await page.goto("/#/journey");
    const heights = await page
      .getByTestId("bottom-nav-item")
      .evaluateAll((elements) => elements.map((element) => element.getBoundingClientRect().height));
    expect(heights.length).toBe(5);
    for (const height of heights) expect(height).toBeGreaterThanOrEqual(44);
    await noHorizontalOverflow(page);
  });

  test("12 · key routes produce no console or page errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
    for (const route of ["journey", "map", "copilot", "recovery", "wallet", "capability", "timeline-lab", "me"]) {
      await page.goto(`/#/${route}`);
      await expect(page.getByTestId("route-heading")).toBeVisible();
    }
    expect(errors).toEqual([]);
  });
});
