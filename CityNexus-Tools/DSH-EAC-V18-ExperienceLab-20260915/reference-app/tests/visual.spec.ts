import { expect, test } from "@playwright/test";

const SHOTS = "../evidence/screenshots";

test.describe("V18 visual acceptance evidence", () => {
  test("desktop evidence set", async ({ page }) => {
    test.skip(test.info().project.name !== "desktop-chromium", "desktop evidence only");
    await page.goto("/#/today");
    await expect(page.getByTestId("journey-pulse")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/desktop-today.png` });

    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("agent-run-timeline")).toBeVisible();
    await page.getByTestId("timeline-next").click();
    await page.getByTestId("timeline-next").click();
    await page.getByTestId("timeline-next").click();
    await page.screenshot({ path: `${SHOTS}/desktop-copilot-hermes.png` });

    await page.goto("/#/recovery");
    await expect(page.getByTestId("recovery-diff")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/desktop-recovery.png` });

    await page.goto("/#/map");
    await expect(page.getByTestId("map-canvas")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/desktop-map.png` });

    await page.goto("/?locale=zh#/today");
    await expect(page.getByTestId("route-heading")).toContainText("你的下一座城市");
    await page.screenshot({ path: `${SHOTS}/desktop-zh-today.png` });

    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/?locale=en#/today");
    await expect(page.locator("html")).toHaveAttribute("data-reduced-motion", "true");
    await page.screenshot({ path: `${SHOTS}/desktop-reduced-motion.png` });
  });

  test("mobile evidence set", async ({ page }) => {
    test.skip(test.info().project.name !== "mobile-chromium", "mobile evidence only");
    await page.goto("/#/today");
    await expect(page.getByTestId("journey-pulse")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/mobile-today.png` });

    await page.goto("/#/copilot");
    await page.getByTestId("copilot-quick-hermes").click();
    await expect(page.getByTestId("agent-run-timeline")).toBeVisible();
    await page.getByTestId("timeline-next").click();
    await page.getByTestId("timeline-next").click();
    await page.screenshot({ path: `${SHOTS}/mobile-copilot-hermes.png` });

    await page.goto("/#/recovery");
    await expect(page.getByTestId("recovery-diff")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/mobile-recovery.png` });

    await page.goto("/#/map");
    await page.getByTestId("sheet-24").click();
    await page.waitForTimeout(350);
    await page.screenshot({ path: `${SHOTS}/mobile-map-sheet-24.png` });
    await page.getByTestId("sheet-90").click();
    await page.waitForTimeout(350);
    await page.screenshot({ path: `${SHOTS}/mobile-map-sheet-90.png` });

    await page.goto("/?locale=zh#/today");
    await expect(page.getByTestId("route-heading")).toContainText("你的下一座城市");
    await page.screenshot({ path: `${SHOTS}/mobile-zh-today.png` });
  });
});
