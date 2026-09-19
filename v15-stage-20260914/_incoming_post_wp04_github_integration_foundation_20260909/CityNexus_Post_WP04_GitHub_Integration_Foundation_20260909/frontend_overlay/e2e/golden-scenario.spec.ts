import { test, expect } from '@playwright/test';

test('CityNexus golden scenario preserves the paid locked cruise during replanning', async ({ page }) => {
  // This is a contract skeleton. Codex must align routes/testids to the actual WP08 UI.
  await page.goto('/');
  await page.getByTestId('demo-reset').click();
  await page.getByTestId('journey-one-day-nexus').click();

  await expect(page.getByTestId('commitment-river-cruise')).toBeVisible();
  await page.getByTestId('journey-start').click();
  await page.getByTestId('inject-tech-art-closure').click();
  await page.getByTestId('replan-open').click();

  await expect(page.getByTestId('replan-preserved-river-cruise')).toContainText('15:30');
  await page.getByTestId('replan-accept').click();
  await expect(page.getByTestId('active-plan-version')).toContainText('ACTIVE');
});
