import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const PAGES = ["/", "/indicadores", "/indicadores/desemprego", "/estados", "/comparar", "/rankings"];

for (const path of PAGES) {
  test(`${path} não tem violações de acessibilidade sérias/críticas`, async ({ page }) => {
    await page.goto(path);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    const seriousOrCritical = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical"
    );

    expect(
      seriousOrCritical,
      seriousOrCritical.map((v) => `${v.id}: ${v.help} (${v.nodes.length} elemento(s))`).join("\n")
    ).toEqual([]);
  });
}
