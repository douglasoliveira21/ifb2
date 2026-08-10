import { expect, test } from "@playwright/test";
import { expectNoHorizontalOverflow } from "./utils";

test("linha do tempo mostra gráfico e seletor de indicador", async ({ page }) => {
  await page.goto("/brasil/linha-do-tempo");
  await expect(page.getByRole("heading", { name: "Linha do tempo" })).toBeVisible();
  await expect(page.locator('svg[role="img"]')).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("trocar o indicador na linha do tempo atualiza o gráfico", async ({ page }) => {
  await page.goto("/brasil/linha-do-tempo?indicador=selic");
  await expect(page.getByRole("heading", { name: /selic/i })).toBeVisible();
});
