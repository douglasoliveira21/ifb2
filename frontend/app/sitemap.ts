import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";
import { getGovernmentPeriods, getHomeData, getMunicipios, getRankings, getStates } from "@/lib/api";

const STATIC_ROUTES = [
  "",
  "/indicadores",
  "/estados",
  "/comparar",
  "/rankings",
  "/metodologia",
  "/fontes",
  "/transparencia",
  "/governo",
  "/frases-verificadas",
  "/apoiar",
  "/brasil/linha-do-tempo",
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [{ indicators }, states, { rankings }, governmentPeriods] = await Promise.all([
    getHomeData(),
    getStates().then((r) => r.states),
    getRankings(),
    getGovernmentPeriods(),
  ]);

  const municipiosByState = await Promise.all(states.map((s) => getMunicipios(s.code)));

  const staticEntries: MetadataRoute.Sitemap = STATIC_ROUTES.map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: path === "" ? "daily" : "weekly",
    priority: path === "" ? 1 : 0.7,
  }));

  const indicatorEntries: MetadataRoute.Sitemap = indicators.map((i) => ({
    url: `${SITE_URL}/indicadores/${i.slug}`,
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  const stateEntries: MetadataRoute.Sitemap = states.map((s) => ({
    url: `${SITE_URL}/estados/${s.code.toLowerCase()}`,
    changeFrequency: "weekly",
    priority: 0.6,
  }));

  const municipioListEntries: MetadataRoute.Sitemap = states.map((s) => ({
    url: `${SITE_URL}/municipios/${s.code.toLowerCase()}`,
    changeFrequency: "weekly",
    priority: 0.4,
  }));

  const municipioDetailEntries: MetadataRoute.Sitemap = municipiosByState.flatMap((municipios, index) => {
    const uf = states[index].code.toLowerCase();
    return municipios.map((m) => ({
      url: `${SITE_URL}/municipios/${uf}/${m.code}`,
      changeFrequency: "weekly" as const,
      priority: 0.4,
    }));
  });

  const rankingEntries: MetadataRoute.Sitemap = rankings.map((r) => ({
    url: `${SITE_URL}/rankings/${r.slug}`,
    changeFrequency: "weekly",
    priority: 0.5,
  }));

  const governmentPeriodEntries: MetadataRoute.Sitemap = governmentPeriods.map((p) => ({
    url: `${SITE_URL}/governo/${p.location_code.toLowerCase()}/${p.id}`,
    changeFrequency: "monthly",
    priority: 0.4,
  }));

  return [
    ...staticEntries,
    ...indicatorEntries,
    ...stateEntries,
    ...municipioListEntries,
    ...municipioDetailEntries,
    ...rankingEntries,
    ...governmentPeriodEntries,
  ];
}
