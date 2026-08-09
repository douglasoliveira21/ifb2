import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";
import { getHomeData, getRankings, getStates } from "@/lib/api";

const STATIC_ROUTES = [
  "",
  "/indicadores",
  "/estados",
  "/comparar",
  "/rankings",
  "/metodologia",
  "/fontes",
  "/transparencia",
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [{ indicators }, states, { rankings }] = await Promise.all([
    getHomeData(),
    getStates().then((r) => r.states),
    getRankings(),
  ]);

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

  const rankingEntries: MetadataRoute.Sitemap = rankings.map((r) => ({
    url: `${SITE_URL}/rankings/${r.slug}`,
    changeFrequency: "weekly",
    priority: 0.5,
  }));

  return [...staticEntries, ...indicatorEntries, ...stateEntries, ...rankingEntries];
}
