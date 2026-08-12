export type Classification =
  | "MELHOROU"
  | "PIOROU"
  | "ESTAVEL"
  | "INCONCLUSIVO"
  | "SEM_DADOS";

export type Polarity = "higher_is_better" | "lower_is_better" | "neutral";

export interface IndicatorSummary {
  indicator_id: string;
  slug: string;
  name: string;
  category: string;
  unit: string;
  polarity: Polarity;
  location_id: string;
  first_date: string | null;
  last_date: string | null;
  first_value: number | null;
  last_value: number | null;
  change_absolute: number | null;
  classification: Classification;
}

export interface IndicatorValuePoint {
  reference_date: string;
  value: number;
}

export interface IndicatorDetail {
  slug: string;
  name: string;
  category: string;
  unit: string;
  polarity: Polarity;
  description_what: string | null;
  description_how: string | null;
  update_frequency: string | null;
  source_name: string;
  source_url: string;
  methodology: string | null;
  summary: IndicatorSummary | null;
  min_value: number | null;
  max_value: number | null;
  avg_value: number | null;
  history: IndicatorValuePoint[];
}

export interface GovernmentPeriod {
  id: string;
  level: string;
  holder_name: string;
  location_code: string;
  start_date: string;
  end_date: string | null;
}

export interface StateSummary {
  code: string;
  name: string;
  indicators_available: number;
  melhoraram: number;
  pioraram: number;
  last_updated: string | null;
}

export interface StateDetail {
  code: string;
  name: string;
  indicators: IndicatorSummary[];
}

export interface MunicipioSummary {
  code: string;
  name: string;
  uf: string;
  indicators_available: number;
  melhoraram: number;
  pioraram: number;
  last_updated: string | null;
}

export interface MunicipioDetail {
  code: string;
  name: string;
  uf: string;
  indicators: IndicatorSummary[];
}

export interface CompareIndicator {
  slug: string;
  name: string;
  category: string;
  unit: string;
  polarity: Polarity;
  history: IndicatorValuePoint[];
}

export interface RankingListItem {
  slug: string;
  indicator_name: string;
  category: string;
  unit: string;
  polarity: Polarity;
  states_count: number;
  last_updated: string | null;
}

export interface RankingEntry {
  rank: number;
  state_code: string;
  state_name: string;
  first_value: number;
  last_value: number;
  change_absolute: number;
  classification: Classification;
  first_date: string;
  last_date: string;
}

export interface RankingDetail {
  slug: string;
  indicator_name: string;
  category: string;
  unit: string;
  polarity: Polarity;
  entries: RankingEntry[];
}

export interface AdminIndicator {
  slug: string;
  name: string;
  category: string;
  unit: string;
  source_name: string;
  enabled: boolean;
  methodology: string | null;
  methodology_version: number | null;
}

export interface AdminSource {
  name: string;
  url: string;
  description: string | null;
  indicators_count: number;
}

export interface AdminSyncRun {
  id: string;
  source_name: string;
  started_at: string;
  finished_at: string | null;
  status: "success" | "partial" | "error";
  records_processed: number;
  error_message: string | null;
}

export interface AdminIndicatorValue {
  id: string;
  location_code: string;
  reference_date: string;
  value: number;
  is_revised: boolean;
}

export interface Correction {
  id: string;
  indicator_slug: string;
  location_code: string;
  reference_date: string;
  previous_value: number;
  new_value: number;
  reason: string;
  changed_by: string;
  changed_at: string;
}

export type ClaimVerdict =
  | "CONFIRMADO"
  | "PARCIALMENTE_CONFIRMADO"
  | "DISTORCIDO"
  | "FALSO"
  | "INCONCLUSIVO";

export type ClaimStatus = "DRAFT" | "PUBLISHED";
export type ClaimOrigin = "MANUAL" | "AI_SCAN";

export interface VerifiedClaim {
  id: string;
  quote: string;
  speaker_name: string;
  speaker_role: string | null;
  claim_date: string | null;
  source_url: string | null;
  indicator_slug: string | null;
  verdict: ClaimVerdict;
  explanation: string;
  status: ClaimStatus;
  origin: ClaimOrigin;
  created_at: string;
}

export interface TransparencySource {
  name: string;
  url: string;
  description: string | null;
}

export interface TransparencySync {
  source_name: string;
  status: string;
  finished_at: string | null;
  records_processed: number;
}

export interface TransparencyError {
  source_name: string;
  started_at: string;
  error_message: string | null;
}

export interface TransparencyCorrection {
  indicator_slug: string;
  indicator_name: string;
  location_code: string;
  reference_date: string;
  previous_value: number;
  new_value: number;
  reason: string;
  changed_at: string;
}

export interface TransparencyMethodology {
  indicator_slug: string;
  indicator_name: string;
  version: number;
  published_at: string;
}

export interface Transparency {
  sources: TransparencySource[];
  last_syncs: TransparencySync[];
  known_errors: TransparencyError[];
  recent_corrections: TransparencyCorrection[];
  methodologies: TransparencyMethodology[];
}
