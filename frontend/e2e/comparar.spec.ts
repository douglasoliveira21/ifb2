import { expect, test } from "@playwright/test";
import { expectNoHorizontalOverflow } from "./utils";

test("comparar estados mostra dado ausente honestamente", async ({ page }) => {
  await page.goto("/comparar?modo=estados&uf_a=PA&uf_b=MG");
  await expect(page.locator(":visible").filter({ hasText: /^Pará$/i }).first()).toBeVisible();
  await expect(page.locator(":visible").filter({ hasText: /^Minas Gerais$/i }).first()).toBeVisible();
  await expect(page.getByText("Dado ainda não disponível").first()).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("comparar períodos mostra evolução e aviso de causalidade", async ({ page }) => {
  await page.goto("/comparar?modo=periodos&periodo_a=2019-01-01&periodo_b=2023-01-01");

  await expect(page.getByText("Taxa de desemprego")).toBeVisible();
  await expect(page.getByText(/correlação temporal não é causalidade/i)).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("comparador nunca mostra um vencedor geral", async ({ page }) => {
  await page.goto("/comparar");
  await expect(page.getByText(/nunca calcula um vencedor geral/i)).toBeVisible();
});
