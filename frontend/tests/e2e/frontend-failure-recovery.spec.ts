import { expect, test } from "@playwright/test";

test.describe("frontend deterministic failure recovery", () => {
  test("recovers after transient incident API failure", async ({ page }) => {
    let calls = 0;
    await page.route("**/api/incidents/**", async (route) => {
      calls += 1;
      if (calls === 1) {
        await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: "synthetic outage" }) });
        return;
      }
      await route.continue();
    });
    await page.goto("/incidents/demo-incident");
    await expect(page.getByRole("heading", { name: "Synthetic printer queue unavailable" })).toBeVisible();
    expect(calls).toBeGreaterThanOrEqual(2);
  });

  test("offline mode disables remediation", async ({ context, page }) => {
    await page.goto("/incidents/demo-incident");
    await expect(page.getByRole("button", { name: "Request remediation" })).toBeEnabled();
    await context.setOffline(true);
    await page.evaluate(() => globalThis.dispatchEvent(new Event("offline")));
    await expect(page.getByText(/You are offline/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Request remediation" })).toBeDisabled();
    await context.setOffline(false);
  });
});
