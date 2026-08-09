import { Page, expect } from "@playwright/test";

export async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
}

/** Abre o menu mobile se o link de navegação não estiver visível diretamente. */
export async function clickNavLink(page: Page, name: string): Promise<void> {
  const link = page.getByRole("link", { name, exact: true }).first();
  if (!(await link.isVisible())) {
    await page.getByRole("button", { name: "Abrir menu" }).click();
  }
  await page.getByRole("link", { name, exact: true }).first().click();
}
