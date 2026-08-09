import { expect, test } from "@playwright/test";
import { expectNoHorizontalOverflow } from "./utils";

test("lista de estados mostra os 27 estados", async ({ page }) => {
  await page.goto("/estados");
  await expect(page.getByRole("heading", { name: "Estados" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Minas Gerais/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /São Paulo/ })).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("estado sem dado mostra aviso honesto, não valor inventado", async ({ page }) => {
  await page.goto("/estados/mg");
  await expect(page.getByRole("heading", { name: "Minas Gerais" })).toBeVisible();
  await expect(page.getByText("Dado ainda não disponível para este estado.")).toBeVisible();
});

test("estado com dado (Pará) mostra o indicador disponível", async ({ page }) => {
  await page.goto("/estados/pa");
  await expect(page.getByRole("heading", { name: "Pará" })).toBeVisible();
  await expect(page.getByText(/Desmatamento/)).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("UF inválida retorna 404", async ({ page }) => {
  const response = await page.goto("/estados/xx");
  expect(response?.status()).toBe(404);
});
