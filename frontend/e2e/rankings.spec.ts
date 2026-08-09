import { expect, test } from "@playwright/test";
import { expectNoHorizontalOverflow } from "./utils";

test("lista de rankings mostra o ranking disponível", async ({ page }) => {
  await page.goto("/rankings");
  await expect(page.getByRole("heading", { name: "Rankings" })).toBeVisible();
  await expect(page.getByText(/mais caiu/i)).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("ranking individual mostra tabela ordenada por variação", async ({ page }) => {
  await page.goto("/rankings/desmatamento-demo");
  await expect(page.getByRole("table")).toBeVisible();

  const firstDataRow = page.locator("tbody tr").first();
  await expect(firstDataRow).toContainText("Pará"); // maior queda absoluta no dado demo

  await expectNoHorizontalOverflow(page);
});

test("ranking inexistente retorna 404", async ({ page }) => {
  const response = await page.goto("/rankings/nao-existe-xyz");
  expect(response?.status()).toBe(404);
});
