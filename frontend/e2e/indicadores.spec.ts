import { expect, test } from "@playwright/test";
import { expectNoHorizontalOverflow } from "./utils";

test("lista de indicadores mostra categorias e valores", async ({ page }) => {
  await page.goto("/indicadores");
  await expect(page.getByRole("heading", { name: "Indicadores" })).toBeVisible();
  await expect(page.getByText("ECONOMIA")).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("página de indicador mostra gráfico, estatísticas e metodologia", async ({ page }) => {
  await page.goto("/indicadores/desemprego");

  await expect(page.getByRole("heading", { name: /desemprego/i })).toBeVisible();
  await expect(page.getByText("Valor atual").first()).toBeVisible();
  await expect(page.getByText("O que este indicador mede?")).toBeVisible();
  await expect(page.getByText("Como interpretar?")).toBeVisible();
  await expect(page.getByText("Fonte", { exact: true })).toBeVisible();

  // gráfico é um <svg role="img"> com aria-label
  await expect(page.locator('svg[role="img"]')).toBeVisible();

  await expectNoHorizontalOverflow(page);
});

test("indicador inexistente mostra 404 com a identidade do IFB", async ({ page }) => {
  const response = await page.goto("/indicadores/nao-existe-xyz");
  expect(response?.status()).toBe(404);
  await expect(page.getByText("Página não encontrada")).toBeVisible();
  await expect(page.getByRole("link", { name: "Voltar para a Home" })).toBeVisible();
});
