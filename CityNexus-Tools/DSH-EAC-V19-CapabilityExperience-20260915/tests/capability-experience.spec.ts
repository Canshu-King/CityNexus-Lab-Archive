import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const evidenceDir = path.resolve(here, "..", "evidence", "screenshots");

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: /Traveler Capability/ })).toBeVisible();
});

test("desktop surfaces, source honesty, and unknown evidence language", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await expect(page.getByTestId("source-banner")).toContainText("RECORDED_FIXTURE");
  await expect(page.getByTestId("journey-setup-needs")).toBeVisible();
  await expect(page.getByTestId("copilot-needs-confirmation")).toBeVisible();
  await expect(page.getByTestId("capability-plan-explanation")).toBeVisible();
  await expect(page.getByTestId("recovery-capability-diff")).toBeVisible();
  await expect(page.getByTestId("twin-capability-summary")).toBeVisible();
  await expect(page.getByTestId("mobile-capability-shield")).toBeVisible();
  await expect(page.getByTestId("capability-map-overlay")).toBeVisible();
  await expect(page.getByTestId("unknown-rule")).toBeVisible();

  const unknownBadges = page.locator('[data-evidence-state="NEEDS_LIVE_EVIDENCE"]');
  await expect(unknownBadges.first()).toBeVisible();
  const unknownText = await page.locator('[data-evidence-state="NEEDS_LIVE_EVIDENCE"]').allInnerTexts();
  for (const text of unknownText) {
    expect(text).not.toContain("✓");
  }
  await page.screenshot({ path: path.join(evidenceDir, "desktop-1280.png"), fullPage: true });

  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.getByTestId("capability-plan-explanation")).toBeVisible();
  await expect(page.getByTestId("capability-map-overlay")).toBeVisible();
  await page.screenshot({ path: path.join(evidenceDir, "desktop-1440.png"), fullPage: true });
});

test("mobile 390x844 and 430x932 capability shield keeps the primary action reachable", async ({ page }) => {
  for (const viewport of [{ width: 390, height: 844 }, { width: 430, height: 932 }]) {
    await page.setViewportSize(viewport);
    await page.getByTestId("mobile-section").scrollIntoViewIfNeeded();
    const shield = page.getByTestId("mobile-capability-shield");
    await expect(shield).toBeVisible();
    const action = page.getByTestId("mobile-shield-action");
    await expect(action).toBeVisible();
    const actionBox = await action.boundingBox();
    expect(actionBox).not.toBeNull();
    if (actionBox) {
      expect(actionBox.x).toBeGreaterThanOrEqual(0);
      expect(actionBox.x + actionBox.width).toBeLessThanOrEqual(viewport.width + 1);
      expect(actionBox.height).toBeGreaterThanOrEqual(44);
    }
    const gap = page.getByTestId("mobile-evidence-gap");
    await expect(gap).toBeVisible();
    await page.screenshot({ path: path.join(evidenceDir, `mobile-${viewport.width}.png`), fullPage: true });
  }
});

test("keyboard operation: quick chips, disclosure, and scenario switching", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const chip = page.getByTestId("setup-quick-less_walking");
  await chip.focus();
  await expect(chip).toHaveAttribute("aria-checked", "true");
  await page.keyboard.press("Space");
  await expect(chip).toHaveAttribute("aria-checked", "false");
  await page.keyboard.press("Space");

  const disclosure = page.getByRole("button", { name: /更多细节|More details/ });
  await disclosure.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("setup-max-walking-leg")).toBeVisible();

  const scenarioC = page.getByTestId("scenario-C");
  await scenarioC.focus();
  await page.keyboard.press("Enter");
  await expect(scenarioC).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("带婴儿车，中午要午睡，别安排太久的户外步行。").first()).toBeVisible();
  await page.screenshot({ path: path.join(evidenceDir, "keyboard-scenario-c.png"), fullPage: true });
});

test("hard conflict and no-capability scenario remain honest", async ({ page }) => {
  await page.getByTestId("scenario-B").click();
  await expect(page.getByTestId("capability-plan-explanation")).toContainText(/known stairs conflict|已知.*楼梯冲突/i);
  await expect(page.getByTestId("capability-plan-explanation")).toContainText(/Candidate B|无障碍.*未核实|not verified/i);
  const unknownBadges = page.locator('[data-evidence-state="NEEDS_LIVE_EVIDENCE"]');
  for (const text of await unknownBadges.allInnerTexts()) expect(text).not.toContain("✓");

  await page.getByTestId("scenario-E").click();
  await expect(page.getByTestId("mobile-capability-shield")).toContainText(/尚未添加出行需求|No travel needs added yet/);
  await expect(page.getByTestId("mobile-evidence-gap")).toHaveCount(0);
  await expect(page.getByTestId("unknown-rule")).toBeVisible();
});

test("320px, 200% zoom stress, long bilingual copy and reduced motion", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 720 });
  await expect(page.getByTestId("journey-setup-needs")).toBeVisible();
  await page.getByTestId("setup-quick-wheelchair_access").scrollIntoViewIfNeeded();
  await expect(page.getByTestId("setup-quick-wheelchair_access")).toBeVisible();
  await page.screenshot({ path: path.join(evidenceDir, "mobile-320.png"), fullPage: true });

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.evaluate(() => { document.body.style.zoom = "200%"; });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(4);

  await page.getByTestId("demo-locale-toggle").click();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  await page.emulateMedia({ reducedMotion: "reduce" });
  const duration = await page.locator(".cne-disclosure__arrow").first().evaluate((node) => getComputedStyle(node).transitionDuration);
  expect(parseFloat(duration)).toBeLessThanOrEqual(0.001);
  await page.screenshot({ path: path.join(evidenceDir, "zoom-200-locale-en.png"), fullPage: true });
});

test("live adapter reports unavailable instead of silently substituting fixture data", async ({ page }) => {
  await page.getByTestId("source-live").click();
  await expect(page.getByTestId("source-banner")).toContainText("LIVE_ADAPTER");
  await page.getByTestId("source-test-live").click();
  await expect(page.getByTestId("source-banner")).toContainText(/LIVE adapter (unavailable|error)/i);
  await expect(page.getByTestId("source-banner")).not.toContainText(/falling back to RECORDED_FIXTURE/i);
});

test("axe accessibility scan of the lab", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
