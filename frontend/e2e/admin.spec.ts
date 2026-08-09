import { expect, test } from "@playwright/test";

// Sem ADMIN_PASSWORD configurada no ambiente de teste, o admin deve ficar
// inacessível por padrão — nunca aberto sem senha.
test("admin fica inacessível sem ADMIN_PASSWORD configurada", async ({ page }) => {
  const response = await page.goto("/admin");
  expect(response?.status()).toBe(503);
});

test("transparência é pública e não exige login", async ({ page }) => {
  const response = await page.goto("/transparencia");
  expect(response?.status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Transparência" })).toBeVisible();
});
