import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const screenshotDir = path.resolve(here, "..", "evidence", "screenshots");

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("capability-shadow-experience")).toBeVisible();
  await expect(page.getByTestId("shadow-source-result")).toBeVisible();
});

test("LIVE_SHADOW uses isolated backend and labels source honestly", async ({ page }) => {
  await expect(page.getByTestId("shadow-source-result")).toContainText("LIVE_SHADOW");
  await expect(page.getByTestId("twin-capability-summary")).toBeVisible();
  await expect(page.getByTestId("provider-evidence-panel")).toBeVisible();
  await expect(page.getByTestId("mobile-capability-shield")).toBeVisible();
  await expect(page.getByTestId("plan-impact-contract-gap")).toBeVisible();
  const overall = page.getByTestId("provider-overall-state");
  await expect(overall).toBeVisible();
  const state = await overall.getAttribute("data-evidence-state");
  expect(["UNVERIFIED", "NEEDS_LIVE_EVIDENCE", "CONFLICT"]).toContain(state);
  const text = await overall.innerText();
  expect(text).not.toContain("✓");
  await page.screenshot({ path: path.join(screenshotDir, "v19_1-live-shadow-desktop.png"), fullPage: true });
});

test("RECORDED_FIXTURE and OFFLINE_STALE never retain the LIVE_SHADOW label", async ({ page }) => {
  await expect(page.getByTestId("shadow-source-result")).toContainText("LIVE_SHADOW");
  await page.getByTestId("shadow-mode-RECORDED_FIXTURE").click();
  await expect(page.getByTestId("shadow-source-result")).toContainText("RECORDED_FIXTURE");
  await expect(page.getByTestId("shadow-source-result")).not.toContainText("LIVE_SHADOW");
  await expect(page.getByTestId("twin-capability-summary")).toContainText(/低步行|Low walking|步行/);

  await page.getByTestId("shadow-mode-OFFLINE_STALE").click();
  await expect(page.getByTestId("shadow-source-result")).toContainText("OFFLINE_STALE");
  await expect(page.getByTestId("shadow-source-result")).not.toContainText("LIVE_SHADOW");
  await page.screenshot({ path: path.join(screenshotDir, "v19_1-offline-stale.png"), fullPage: true });
});

test("provider evidence unknown state remains non-green and traceable", async ({ page }) => {
  const panel = page.getByTestId("provider-evidence-panel");
  await expect(panel).toContainText(/provider|Provider/);
  await expect(panel).toContainText(/需要实时证据|未核实|冲突|ACCESSIBILITY|NEEDS_LIVE_EVIDENCE|UNVERIFIED|CONFLICT/);
  const rawTags = panel.locator(".cne-provider-evidence__raw");
  await expect(rawTags.first()).toBeVisible();
  const needBadges = panel.locator('[data-evidence-state="NEEDS_LIVE_EVIDENCE"]');
  if (await needBadges.count()) {
    for (const text of await needBadges.allInnerTexts()) expect(text).not.toContain("✓");
  }
});

test("mobile 390x844 keeps capability shield action reachable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByTestId("mobile-capability-shield").scrollIntoViewIfNeeded();
  const action = page.getByTestId("mobile-shield-action");
  await expect(action).toBeVisible();
  const box = await action.boundingBox();
  expect(box).not.toBeNull();
  if (box) {
    expect(box.height).toBeGreaterThanOrEqual(44);
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(391);
  }
  await page.screenshot({ path: path.join(screenshotDir, "v19_1-mobile-390.png"), fullPage: true });
});

test("keyboard mode controls and 200% zoom shell", async ({ page }) => {
  const live = page.getByTestId("shadow-mode-LIVE_SHADOW");
  await live.focus();
  await expect(live).toHaveAttribute("aria-checked", "true");
  await page.keyboard.press("Tab");
  await page.setViewportSize({ width: 320, height: 720 });
  await expect(page.getByTestId("capability-shadow-experience")).toBeVisible();
  await page.evaluate(() => { document.body.style.zoom = "200%"; });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(4);
  await page.screenshot({ path: path.join(screenshotDir, "v19_1-320-zoom.png"), fullPage: true });
});

test("430x932, 1440x900, reduced motion, and long bilingual copy", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 932 });
  await expect(page.getByTestId("mobile-capability-shield")).toBeVisible();
  await page.screenshot({ path: path.join(screenshotDir, "v19_1-mobile-430.png"), fullPage: true });

  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.getByTestId("capability-shadow-experience")).toBeVisible();
  await page.screenshot({ path: path.join(screenshotDir, "v19_1-desktop-1440.png"), fullPage: true });

  await page.emulateMedia({ reducedMotion: "reduce" });
  const transition = await page.locator(".cne-disclosure__arrow").first().evaluate((node) => getComputedStyle(node).transitionDuration);
  expect(parseFloat(transition)).toBeLessThanOrEqual(0.001);

  await page.getByTestId("shadow-mode-RECORDED_FIXTURE").click();
  await expect(page.getByTestId("shadow-source-result")).toContainText("RECORDED_FIXTURE");
  await expect(page.getByTestId("twin-capability-summary")).toContainText(/低步行|Low walking|步行|midday|休息/i);
});

test("axe scan of shadow capability surface", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
