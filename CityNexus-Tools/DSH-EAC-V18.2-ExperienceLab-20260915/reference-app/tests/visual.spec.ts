import { expect, test } from "@playwright/test";

const SHOTS = "../evidence/screenshots";

test.describe("V18.2 visual acceptance evidence", () => {
  test("desktop evidence set", async ({ page }) => {
    test.skip(test.info().project.name !== "desktop-chromium", "desktop evidence only");
    await page.goto("/#/journey");
    await expect(page.getByTestId("journey-pulse")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-desktop-journey.png` });

    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    for (let index = 0; index < 14; index += 1) await page.getByTestId("timeline-next").click();
    await expect(page.getByTestId("approval-panel")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-desktop-copilot-approval.png` });

    await page.goto("/#/recovery");
    await expect(page.getByTestId("recovery-diff")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-desktop-recovery.png` });

    await page.goto("/#/map");
    await expect(page.getByTestId("map-canvas")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-desktop-map.png` });

    await page.goto("/?locale=zh#/journey");
    await expect(page.getByTestId("route-heading")).toContainText("你的下一座城市");
    await page.screenshot({ path: `${SHOTS}/v18.2-desktop-zh-journey.png` });

    await page.goto("/?runtime=hermes_unavailable#/journey");
    await expect(page.getByTestId("runtime-status-banner")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-desktop-hermes-unavailable.png` });

    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/?locale=en#/journey");
    await expect(page.locator("html")).toHaveAttribute("data-reduced-motion", "true");
    await page.screenshot({ path: `${SHOTS}/v18.2-desktop-reduced-motion.png` });
  });

  test("mobile evidence set", async ({ page }) => {
    test.skip(test.info().project.name !== "mobile-chromium", "mobile evidence only");
    await page.goto("/#/journey");
    await expect(page.getByTestId("journey-pulse")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-mobile-journey.png` });

    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("timeline-expand")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-mobile-copilot-current-step.png` });
    await page.getByTestId("timeline-expand").click({ force: true });
    await page.getByTestId("timeline-next").click();
    await page.getByTestId("timeline-next").click();
    await page.screenshot({ path: `${SHOTS}/v18.2-mobile-copilot-expanded.png` });

    await page.goto("/#/recovery");
    await expect(page.getByTestId("recovery-diff")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/v18.2-mobile-recovery.png` });

    await page.goto("/#/map");
    for (const state of ["24", "55", "90"]) {
      await page.getByTestId(`sheet-${state}`).click();
      await page.waitForTimeout(350);
      await page.screenshot({ path: `${SHOTS}/v18.2-mobile-map-${state}.png` });
    }

    await page.goto("/?locale=zh#/journey");
    await expect(page.getByTestId("route-heading")).toContainText("你的下一座城市");
    await page.screenshot({ path: `${SHOTS}/v18.2-mobile-zh-journey.png` });
  });
});
