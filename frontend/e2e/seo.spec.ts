import { expect, test } from "@playwright/test";

test("sitemap.xml responde e contém as páginas de indicador", async ({ request }) => {
  const response = await request.get("/sitemap.xml");
  expect(response.ok()).toBeTruthy();
  const body = await response.text();
  expect(body).toContain("/indicadores/desemprego");
  expect(body).toContain("/estados/");
});

test("robots.txt aponta para o sitemap e bloqueia /admin", async ({ request }) => {
  const response = await request.get("/robots.txt");
  expect(response.ok()).toBeTruthy();
  const body = await response.text();
  expect(body).toContain("sitemap.xml");
  expect(body.toLowerCase()).toContain("disallow: /admin");
});

test("metodologia e fontes carregam (antes eram links quebrados)", async ({ page }) => {
  await page.goto("/metodologia");
  await expect(page.getByRole("heading", { name: "Metodologia" })).toBeVisible();

  await page.goto("/fontes");
  await expect(page.getByRole("heading", { name: "Fontes" })).toBeVisible();
});
