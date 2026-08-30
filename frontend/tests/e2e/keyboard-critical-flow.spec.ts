import { test, expect } from "@playwright/test";

test("critical incident flow is keyboard operable", async ({ page }) => {
  await page.goto("/incidents/demo-incident");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to main content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  // Intentionally no page.mouse usage in this contract.
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
});
