import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("incident route has no serious accessibility violations", async ({ page }) => {
  await page.goto("/incidents/demo-incident");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();

  const serious = results.violations.filter(v => v.impact === "serious" || v.impact === "critical");
  expect(serious).toEqual([]);
});
