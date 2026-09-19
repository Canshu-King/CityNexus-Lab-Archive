import { expect, test } from "@playwright/test";
import { testIds } from "../src/contracts/testIds";

test("Journey Mode uses backend truth for closure recovery", async ({ page }) => {
  await page.goto("/");

  // The integrated UI should bootstrap the deterministic backend fixture and
  // expose the resulting JourneyTwin. Do not satisfy these assertions with
  // hardcoded strings or localStorage state.
  await expect(page.getByTestId(testIds.journeyStatus)).toContainText("ACTIVE");
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");

  await page.getByTestId(testIds.eventSimulator).click();
  await page.getByTestId(testIds.eventClosureButton).click();
  await expect(page.getByTestId(testIds.replanPanel)).toBeVisible();
  await expect(page.getByTestId(testIds.replanCandidateFamilies)).toContainText(
    "F3_OPPORTUNITY_WINDOW",
  );
  await expect(page.getByTestId(testIds.replanEvidence)).toContainText("C4");

  await page.getByTestId(testIds.acceptReplan).click();
  await expect(page.getByTestId(testIds.journeyStatus)).toContainText("ACTIVE");

  // Reload must re-fetch JourneyTwin/backend state. A localStorage-only pass is
  // explicitly not acceptable for the next CityNexus gate.
  await page.reload();
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");
});
