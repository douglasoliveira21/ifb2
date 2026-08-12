import {
  DEMO_COMPARE_INDICATORS,
  DEMO_GOVERNMENT_PERIODS,
  DEMO_INDICATORS,
  DEMO_RANKINGS,
  DEMO_STATES,
  DEMO_TRANSPARENCY,
  DEMO_UPDATED_AT,
  getDemoIndicatorDetail,
  getDemoRankingDetail,
  getDemoStateDetail,
} from "./demo-data";
import {
  CompareIndicator,
  GovernmentPeriod,
  IndicatorDetail,
  IndicatorSummary,
  MunicipioDetail,
  MunicipioSummary,
  RankingDetail,
  RankingListItem,
  StateDetail,
  StateSummary,
  Transparency,
  VerifiedClaim,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const isDev = process.env.NODE_ENV === "development";

export interface HomeData {
  indicators: IndicatorSummary[];
  updatedAt: string | null;
  isDemo: boolean;
}

export async function getHomeData(): Promise<HomeData> {
  try {
    const indicators = await getIndicators();
    const updatedAt = indicators
      .map((i) => i.last_date)
      .filter((d): d is string => Boolean(d))
      .sort()
      .at(-1) ?? null;
    return { indicators, updatedAt, isDemo: false };
  } catch {
    if (isDev) {
      return { indicators: DEMO_INDICATORS, updatedAt: DEMO_UPDATED_AT, isDemo: true };
    }
    return { indicators: [], updatedAt: null, isDemo: false };
  }
}

export async function getIndicators(): Promise<IndicatorSummary[]> {
  const res = await fetch(`${API_URL}/api/indicators`, { next: { revalidate: 3600 } });
  if (!res.ok) throw new Error(`API respondeu ${res.status}`);
  return res.json();
}

export interface IndicatorDetailResult {
  detail: IndicatorDetail | null;
  isDemo: boolean;
}

export async function getIndicatorDetail(slug: string, locationCode?: string): Promise<IndicatorDetailResult> {
  try {
    const url = locationCode
      ? `${API_URL}/api/indicators/${slug}?location=${locationCode}`
      : `${API_URL}/api/indicators/${slug}`;
    const res = await fetch(url, { next: { revalidate: 3600 } });
    if (res.status === 404) return { detail: null, isDemo: false };
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return { detail: await res.json(), isDemo: false };
  } catch {
    if (isDev) {
      return { detail: getDemoIndicatorDetail(slug), isDemo: true };
    }
    return { detail: null, isDemo: false };
  }
}

export async function getGovernmentPeriods(locationCode: string = "BR"): Promise<GovernmentPeriod[]> {
  try {
    const res = await fetch(`${API_URL}/api/government-periods?location=${locationCode}`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return res.json();
  } catch {
    if (isDev) return DEMO_GOVERNMENT_PERIODS.filter((p) => p.location_code === locationCode.toUpperCase());
    return [];
  }
}

export interface StatesResult {
  states: StateSummary[];
  isDemo: boolean;
}

export async function getStates(): Promise<StatesResult> {
  try {
    const res = await fetch(`${API_URL}/api/states`, { next: { revalidate: 3600 } });
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return { states: await res.json(), isDemo: false };
  } catch {
    if (isDev) return { states: DEMO_STATES, isDemo: true };
    return { states: [], isDemo: false };
  }
}

export interface StateDetailResult {
  detail: StateDetail | null;
  isDemo: boolean;
}

export async function getStateDetail(uf: string): Promise<StateDetailResult> {
  try {
    const res = await fetch(`${API_URL}/api/states/${uf}`, { next: { revalidate: 3600 } });
    if (res.status === 404) return { detail: null, isDemo: false };
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return { detail: await res.json(), isDemo: false };
  } catch {
    if (isDev) return { detail: getDemoStateDetail(uf), isDemo: true };
    return { detail: null, isDemo: false };
  }
}

export async function getMunicipios(uf: string): Promise<MunicipioSummary[]> {
  try {
    const res = await fetch(`${API_URL}/api/municipios/${uf}`, { next: { revalidate: 3600 } });
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return res.json();
  } catch {
    return [];
  }
}

export async function getMunicipioDetail(uf: string, codigo: string): Promise<MunicipioDetail | null> {
  try {
    const res = await fetch(`${API_URL}/api/municipios/${uf}/${codigo}`, { next: { revalidate: 3600 } });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return res.json();
  } catch {
    return null;
  }
}

export interface CompareIndicatorsResult {
  indicators: CompareIndicator[];
  isDemo: boolean;
}

export async function getCompareIndicators(locationCode: string = "BR"): Promise<CompareIndicatorsResult> {
  try {
    const res = await fetch(`${API_URL}/api/compare/indicators?location=${locationCode}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return { indicators: await res.json(), isDemo: false };
  } catch {
    if (isDev) return { indicators: DEMO_COMPARE_INDICATORS, isDemo: true };
    return { indicators: [], isDemo: false };
  }
}

export interface RankingsResult {
  rankings: RankingListItem[];
  isDemo: boolean;
}

export async function getRankings(): Promise<RankingsResult> {
  try {
    const res = await fetch(`${API_URL}/api/rankings`, { next: { revalidate: 3600 } });
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return { rankings: await res.json(), isDemo: false };
  } catch {
    if (isDev) return { rankings: DEMO_RANKINGS, isDemo: true };
    return { rankings: [], isDemo: false };
  }
}

export interface RankingDetailResult {
  detail: RankingDetail | null;
  isDemo: boolean;
}

export async function getRankingDetail(slug: string): Promise<RankingDetailResult> {
  try {
    const res = await fetch(`${API_URL}/api/rankings/${slug}`, { next: { revalidate: 3600 } });
    if (res.status === 404) return { detail: null, isDemo: false };
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return { detail: await res.json(), isDemo: false };
  } catch {
    if (isDev) return { detail: getDemoRankingDetail(slug), isDemo: true };
    return { detail: null, isDemo: false };
  }
}

export interface TransparencyResult {
  transparency: Transparency | null;
  isDemo: boolean;
}

export async function getTransparency(): Promise<TransparencyResult> {
  try {
    const res = await fetch(`${API_URL}/api/transparency`, { next: { revalidate: 600 } });
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return { transparency: await res.json(), isDemo: false };
  } catch {
    if (isDev) return { transparency: DEMO_TRANSPARENCY, isDemo: true };
    return { transparency: null, isDemo: false };
  }
}

export async function getVerifiedClaims(): Promise<VerifiedClaim[]> {
  try {
    const res = await fetch(`${API_URL}/api/verified-claims`, { next: { revalidate: 600 } });
    if (!res.ok) throw new Error(`API respondeu ${res.status}`);
    return res.json();
  } catch {
    return [];
  }
}
