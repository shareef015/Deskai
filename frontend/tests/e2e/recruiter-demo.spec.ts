import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";


test("recruiter demo completes printer flow and resets", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByRole("heading", { name: "DeskPilot AI — End-to-End Service Desk Demo" })).toBeVisible();
  await expect(page.getByText("How can I help you today?", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Run certified scenario" }).click();
  await expect(page.getByTestId("demo-terminal-state")).toHaveText("Closed");
  await expect(page.getByText("Human approval before mutating tools")).toBeVisible();

  await page.getByRole("button", { name: "Reset demo" }).click();
  await expect(page.getByTestId("demo-terminal-state")).toHaveText("Ready");
  await expect(page.getByTestId("demo-reset-count")).toHaveText("Reset count: 1");
});


test("verification failure returns to diagnosis without false closure", async ({ page }) => {
  await page.goto("/demo");
  await page.getByLabel("Scenario").selectOption("DEMO-VERIFY-FAIL");
  await page.getByRole("button", { name: "Run certified scenario" }).click();
  await expect(page.getByTestId("demo-terminal-state")).toHaveText("Diagnosing");
  await expect(page.getByText(/was not falsely closed/i)).toBeVisible();
});


test("cross-tenant demo is denied", async ({ page }) => {
  await page.goto("/demo");
  await page.getByLabel("Scenario").selectOption("DEMO-CROSS-TENANT");
  await page.getByRole("button", { name: "Run certified scenario" }).click();
  await expect(page.getByTestId("demo-terminal-state")).toHaveText("Denied");
  await expect(page.getByRole("alert")).toContainText("Cross-tenant request denied");
});


test("recruiter demo has no automatically detectable accessibility violations", async ({ page }) => {
  await page.goto("/demo");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
