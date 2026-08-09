import { expect, test } from "@playwright/test";
import { clickNavLink, expectNoHorizontalOverflow } from "./utils";

test("home mostra o Placar Brasil com dados demo", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Placar Brasil" })).toBeVisible();
  await expect(page.getByText("DADOS DE DEMONSTRAÇÃO")).toBeVisible();
  await expect(page.getByText("Fiscalizamos resultados, não discursos.")).toBeVisible();

  await expectNoHorizontalOverflow(page);
});

test("home tem link para pular para o conteúdo", async ({ page }) => {
  await page.goto("/");
  const skipLink = page.getByRole("link", { name: "Pular para o conteúdo" });
  await expect(skipLink).toHaveAttribute("href", "#conteudo");
});

test("navegação principal leva às páginas certas", async ({ page }) => {
  await page.goto("/");
  await clickNavLink(page, "Indicadores");
  await expect(page).toHaveURL(/\/indicadores$/);
  await expect(page.getByRole("heading", { name: "Indicadores" })).toBeVisible();
});
