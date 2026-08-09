/**
 * DADOS DE DEMONSTRAÇÃO — uso exclusivo em desenvolvimento local.
 *
 * Este arquivo NUNCA deve ser usado em produção. `getHomeData()` (lib/api.ts)
 * só recorre a ele quando `NODE_ENV === "development"` e a API backend não
 * responde. Cada indicador aqui carrega o sufixo "(DEMO)" no nome para que
 * fique visível em qualquer tela, e a Home exibe um aviso explícito quando
 * estes dados estão em uso.
 */
import { classify } from "./classify";
import {
  CompareIndicator,
  GovernmentPeriod,
  IndicatorDetail,
  IndicatorSummary,
  IndicatorValuePoint,
  Polarity,
  RankingDetail,
  RankingEntry,
  RankingListItem,
  StateDetail,
  StateSummary,
  Transparency,
} from "./types";

export const DEMO_UPDATED_AT = "2026-08-01";

export const DEMO_GOVERNMENT_PERIODS: GovernmentPeriod[] = [
  { level: "federal", holder_name: "Fernando Henrique Cardoso", start_date: "1995-01-01", end_date: "1999-01-01" },
  { level: "federal", holder_name: "Fernando Henrique Cardoso", start_date: "1999-01-01", end_date: "2003-01-01" },
  { level: "federal", holder_name: "Luiz Inácio Lula da Silva", start_date: "2003-01-01", end_date: "2007-01-01" },
  { level: "federal", holder_name: "Luiz Inácio Lula da Silva", start_date: "2007-01-01", end_date: "2011-01-01" },
  { level: "federal", holder_name: "Dilma Rousseff", start_date: "2011-01-01", end_date: "2015-01-01" },
  { level: "federal", holder_name: "Dilma Rousseff", start_date: "2015-01-01", end_date: "2016-08-31" },
  { level: "federal", holder_name: "Michel Temer", start_date: "2016-08-31", end_date: "2019-01-01" },
  { level: "federal", holder_name: "Jair Bolsonaro", start_date: "2019-01-01", end_date: "2023-01-01" },
  { level: "federal", holder_name: "Luiz Inácio Lula da Silva", start_date: "2023-01-01", end_date: null },
];

function monthlyDemoSeries(
  startYear: number,
  startMonth: number,
  endYear: number,
  endMonth: number,
  base: number,
  trendPerYear: number,
  amplitude: number
): IndicatorValuePoint[] {
  const points: IndicatorValuePoint[] = [];
  let year = startYear;
  let month = startMonth;
  let i = 0;
  while (year < endYear || (year === endYear && month <= endMonth)) {
    const yearsElapsed = i / 12;
    const value = base + trendPerYear * yearsElapsed + amplitude * Math.sin(i / 6);
    points.push({
      reference_date: `${year}-${String(month).padStart(2, "0")}-01`,
      value: Math.round(value * 100) / 100,
    });
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
    i += 1;
  }
  return points;
}

const DEMO_METHODOLOGY_TEXT =
  "# Metodologia (DEMO)\n\nEste texto e os valores deste indicador são fictícios, gerados apenas " +
  "para desenvolvimento local do IFB.";

const DEMO_HISTORY: Record<string, IndicatorValuePoint[]> = {
  desemprego: monthlyDemoSeries(2015, 1, 2026, 7, 11.0, -0.4, 1.5),
  ipca: monthlyDemoSeries(2015, 1, 2026, 7, 6.5, -0.15, 2.0),
  selic: monthlyDemoSeries(2015, 1, 2026, 7, 12.0, -0.1, 3.0),
};


// Resumo (usado na Home e na lista de indicadores) derivado da MESMA série
// usada na página de detalhe, para os três indicadores com histórico
// completo — evita o card mostrar um valor e o gráfico mostrar outro.
function summaryFromHistory(
  id: string,
  slug: string,
  name: string,
  category: string,
  unit: string,
  polarity: Polarity
): IndicatorSummary {
  const history = DEMO_HISTORY[slug];
  const first = history[0];
  const last = history[history.length - 1];
  return {
    indicator_id: id,
    slug,
    name,
    category,
    unit,
    polarity,
    location_id: "demo-br",
    first_date: first.reference_date,
    last_date: last.reference_date,
    first_value: first.value,
    last_value: last.value,
    change_absolute: Math.round((last.value - first.value) * 100) / 100,
    classification: classify(polarity, first.value, last.value),
  };
}

export function getDemoIndicatorDetail(slug: string): IndicatorDetail | null {
  const summary = DEMO_INDICATORS.find((i) => i.slug === slug);
  if (!summary) return null;

  const history =
    DEMO_HISTORY[slug] ??
    (summary.first_value !== null && summary.last_value !== null
      ? [
          { reference_date: summary.first_date as string, value: summary.first_value },
          { reference_date: summary.last_date as string, value: summary.last_value },
        ]
      : []);

  const values = history.map((p) => p.value);

  return {
    slug: summary.slug,
    name: summary.name,
    category: summary.category,
    unit: summary.unit,
    polarity: summary.polarity,
    description_what: "Indicador de demonstração — não é dado oficial.",
    description_how: "Uso exclusivo para desenvolvimento local.",
    update_frequency: "mensal",
    source_name: "[DEMO] Fonte de demonstração",
    source_url: "https://example.org/demo",
    methodology: DEMO_METHODOLOGY_TEXT,
    summary,
    min_value: values.length ? Math.min(...values) : null,
    max_value: values.length ? Math.max(...values) : null,
    avg_value: values.length ? values.reduce((a, b) => a + b, 0) / values.length : null,
    history,
  };
}

export const DEMO_INDICATORS: IndicatorSummary[] = [
  summaryFromHistory(
    "demo-desemprego", "desemprego", "Taxa de desemprego (DEMO)",
    "EMPREGO_RENDA", "%", "lower_is_better"
  ),
  summaryFromHistory(
    "demo-ipca", "ipca", "IPCA — inflação 12 meses (DEMO)",
    "ECONOMIA", "%", "lower_is_better"
  ),
  summaryFromHistory(
    "demo-selic", "selic", "Taxa Selic (DEMO)",
    "ECONOMIA", "%", "neutral"
  ),
  {
    indicator_id: "demo-pib-per-capita",
    slug: "pib-per-capita",
    name: "PIB per capita (DEMO)",
    category: "ECONOMIA",
    unit: "R$",
    polarity: "higher_is_better",
    location_id: "demo-br",
    first_date: "2023-01-01",
    last_date: "2026-01-01",
    first_value: 39000,
    last_value: 42500,
    change_absolute: 3500,
    classification: "MELHOROU",
  },
  {
    indicator_id: "demo-divida-pib",
    slug: "divida-pib",
    name: "Dívida/PIB (DEMO)",
    category: "CONTAS_PUBLICAS",
    unit: "%",
    polarity: "lower_is_better",
    location_id: "demo-br",
    first_date: "2023-01-01",
    last_date: "2026-06-01",
    first_value: 74.4,
    last_value: 78.1,
    change_absolute: 3.7,
    classification: "PIOROU",
  },
  {
    indicator_id: "demo-mortalidade-infantil",
    slug: "mortalidade-infantil",
    name: "Mortalidade infantil (DEMO)",
    category: "SAUDE",
    unit: "por mil nascidos vivos",
    polarity: "lower_is_better",
    location_id: "demo-br",
    first_date: "2023-01-01",
    last_date: "2025-01-01",
    first_value: 12.4,
    last_value: 11.9,
    change_absolute: -0.5,
    classification: "MELHOROU",
  },
  {
    indicator_id: "demo-ideb",
    slug: "ideb",
    name: "IDEB (DEMO)",
    category: "EDUCACAO",
    unit: "pontos",
    polarity: "higher_is_better",
    location_id: "demo-br",
    first_date: "2023-01-01",
    last_date: "2025-01-01",
    first_value: 5.8,
    last_value: 5.8,
    change_absolute: 0,
    classification: "ESTAVEL",
  },
  {
    indicator_id: "demo-homicidios",
    slug: "homicidios",
    name: "Homicídios por 100 mil (DEMO)",
    category: "SEGURANCA",
    unit: "por 100 mil habitantes",
    polarity: "lower_is_better",
    location_id: "demo-br",
    first_date: "2023-01-01",
    last_date: "2025-01-01",
    first_value: 21.2,
    last_value: 21.2,
    change_absolute: 0,
    classification: "ESTAVEL",
  },
  {
    indicator_id: "demo-desmatamento",
    slug: "desmatamento",
    name: "Desmatamento — Amazônia (DEMO)",
    category: "MEIO_AMBIENTE",
    unit: "km²/ano",
    polarity: "lower_is_better",
    location_id: "demo-br",
    first_date: "2023-01-01",
    last_date: null,
    first_value: 9500,
    last_value: null,
    change_absolute: null,
    classification: "SEM_DADOS",
  },
];

const STATE_NAMES: [string, string][] = [
  ["AC", "Acre"], ["AL", "Alagoas"], ["AP", "Amapá"], ["AM", "Amazonas"],
  ["BA", "Bahia"], ["CE", "Ceará"], ["DF", "Distrito Federal"], ["ES", "Espírito Santo"],
  ["GO", "Goiás"], ["MA", "Maranhão"], ["MT", "Mato Grosso"], ["MS", "Mato Grosso do Sul"],
  ["MG", "Minas Gerais"], ["PA", "Pará"], ["PB", "Paraíba"], ["PR", "Paraná"],
  ["PE", "Pernambuco"], ["PI", "Piauí"], ["RJ", "Rio de Janeiro"], ["RN", "Rio Grande do Norte"],
  ["RS", "Rio Grande do Sul"], ["RO", "Rondônia"], ["RR", "Roraima"], ["SC", "Santa Catarina"],
  ["SP", "São Paulo"], ["SE", "Sergipe"], ["TO", "Tocantins"],
];

// Só alguns estados têm indicador demo — os demais mostram "sem dados",
// exatamente como aconteceria em produção com dados reais incompletos.
const DEMO_STATE_INDICATORS: Record<string, IndicatorSummary> = {
  AM: {
    indicator_id: "demo-state-am-desmatamento", slug: "desmatamento-demo",
    name: "Desmatamento (DEMO)", category: "MEIO_AMBIENTE", unit: "km²/ano",
    polarity: "lower_is_better", location_id: "demo-am",
    first_date: "2022-01-01", last_date: "2024-01-01",
    first_value: 1120, last_value: 850, change_absolute: -270, classification: "MELHOROU",
  },
  PA: {
    indicator_id: "demo-state-pa-desmatamento", slug: "desmatamento-demo",
    name: "Desmatamento (DEMO)", category: "MEIO_AMBIENTE", unit: "km²/ano",
    polarity: "lower_is_better", location_id: "demo-pa",
    first_date: "2022-01-01", last_date: "2024-01-01",
    first_value: 2400, last_value: 1600, change_absolute: -800, classification: "MELHOROU",
  },
  MT: {
    indicator_id: "demo-state-mt-desmatamento", slug: "desmatamento-demo",
    name: "Desmatamento (DEMO)", category: "MEIO_AMBIENTE", unit: "km²/ano",
    polarity: "lower_is_better", location_id: "demo-mt",
    first_date: "2022-01-01", last_date: "2024-01-01",
    first_value: 1300, last_value: 900, change_absolute: -400, classification: "MELHOROU",
  },
};

export const DEMO_STATES: StateSummary[] = STATE_NAMES.map(([code, name]) => {
  const indicator = DEMO_STATE_INDICATORS[code];
  return {
    code,
    name,
    indicators_available: indicator ? 1 : 0,
    melhoraram: indicator?.classification === "MELHOROU" ? 1 : 0,
    pioraram: indicator?.classification === "PIOROU" ? 1 : 0,
    last_updated: indicator?.last_date ?? null,
  };
});

export function getDemoStateDetail(code: string): StateDetail | null {
  const state = STATE_NAMES.find(([c]) => c === code.toUpperCase());
  if (!state) return null;
  const [uf, name] = state;
  const indicator = DEMO_STATE_INDICATORS[uf];
  return { code: uf, name, indicators: indicator ? [indicator] : [] };
}

// Histórico completo, usado pelo comparador de períodos. Só os três
// indicadores com série mensal gerada (DEMO_HISTORY) entram aqui — os
// demais indicadores demo têm só 2 pontos e não fazem sentido num
// comparador de períodos.
export const DEMO_COMPARE_INDICATORS: CompareIndicator[] = ["desemprego", "ipca", "selic"].map((slug) => {
  const indicator = DEMO_INDICATORS.find((i) => i.slug === slug)!;
  return {
    slug: indicator.slug,
    name: indicator.name,
    category: indicator.category,
    unit: indicator.unit,
    polarity: indicator.polarity,
    history: DEMO_HISTORY[slug],
  };
});

// Ranking demo: os únicos 3 estados com o indicador demo de desmatamento.
// Ordenado por variação (lower_is_better -> mais negativo primeiro).
const DEMO_RANKING_ENTRIES: RankingEntry[] = (["PA", "MT", "AM"] as const)
  .map((uf) => {
    const indicator = DEMO_STATE_INDICATORS[uf];
    const stateName = STATE_NAMES.find(([code]) => code === uf)![1];
    return {
      rank: 0,
      state_code: uf,
      state_name: stateName,
      first_value: indicator.first_value as number,
      last_value: indicator.last_value as number,
      change_absolute: indicator.change_absolute as number,
      classification: indicator.classification,
      first_date: indicator.first_date as string,
      last_date: indicator.last_date as string,
    };
  })
  .sort((a, b) => a.change_absolute - b.change_absolute)
  .map((entry, i) => ({ ...entry, rank: i + 1 }));

export const DEMO_RANKINGS: RankingListItem[] = [
  {
    slug: "desmatamento-demo",
    indicator_name: "Desmatamento (DEMO)",
    category: "MEIO_AMBIENTE",
    unit: "km²/ano",
    polarity: "lower_is_better",
    states_count: DEMO_RANKING_ENTRIES.length,
    last_updated: "2024-01-01",
  },
];

export function getDemoRankingDetail(slug: string): RankingDetail | null {
  if (slug !== "desmatamento-demo") return null;
  return {
    slug,
    indicator_name: "Desmatamento (DEMO)",
    category: "MEIO_AMBIENTE",
    unit: "km²/ano",
    polarity: "lower_is_better",
    entries: DEMO_RANKING_ENTRIES,
  };
}

export const DEMO_TRANSPARENCY: Transparency = {
  sources: [
    { name: "[DEMO] Fonte de demonstração", url: "https://example.org/demo", description: "Dados fictícios." },
  ],
  last_syncs: [
    { source_name: "[DEMO] Fonte de demonstração", status: "success", finished_at: "2026-08-01T04:00:00Z", records_processed: 12 },
  ],
  known_errors: [],
  recent_corrections: [],
  methodologies: [
    { indicator_slug: "desemprego", indicator_name: "Taxa de desemprego (DEMO)", version: 1, published_at: "2026-01-01T00:00:00Z" },
  ],
};
