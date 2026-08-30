import { expect, test } from "@playwright/test";

test("security headers prevent common browser trust-boundary attacks", async ({ page }) => {
  const response = await page.goto("/");
  expect(response).not.toBeNull();
  const headers = response!.headers();
  expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(headers["content-security-policy"]).toContain("require-trusted-types-for 'script'");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-frame-options"]).toBe("DENY");
});

test("javascript URL payload does not execute", async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => {
    const a = document.createElement("a");
    a.id = "attack-link";
    a.textContent = "attack";
    a.setAttribute("href", "javascript:window.__deskpilotXss = true");
    document.body.appendChild(a);
  });
  await page.locator("#attack-link").click();
  const executed = await page.evaluate(() => (window as unknown as { __deskpilotXss?: boolean }).__deskpilotXss ?? false);
  expect(executed).toBe(false);
});

test("page cannot be framed by another origin", async ({ page }) => {
  const response = await page.goto("/");
  const csp = response!.headers()["content-security-policy"] ?? "";
  expect(csp).toMatch(/frame-ancestors 'none'/);
});
