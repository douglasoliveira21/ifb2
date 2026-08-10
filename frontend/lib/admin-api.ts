/**
 * Cliente HTTP para /api/admin — só deve ser importado em Server
 * Components e Server Actions dentro de app/admin/**. Usa as mesmas
 * credenciais que o middleware.ts exige do navegador para autenticar a
 * chamada servidor-a-servidor com o backend (ADMIN_PASSWORD nunca é
 * exposta ao cliente).
 */
import {
  AdminIndicator,
  AdminIndicatorValue,
  AdminSource,
  AdminSyncRun,
  Correction,
  VerifiedClaim,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeader(): string {
  const username = process.env.ADMIN_USERNAME ?? "admin";
  const password = process.env.ADMIN_PASSWORD;
  if (!password) throw new Error("ADMIN_PASSWORD não configurada no servidor Next.js.");
  return "Basic " + Buffer.from(`${username}:${password}`).toString("base64");
}

async function adminFetch(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${API_URL}/api/admin${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Authorization: authHeader(),
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Admin API respondeu ${res.status}: ${detail}`);
  }
  return res;
}

export async function getAdminIndicators(): Promise<AdminIndicator[]> {
  return (await adminFetch("/indicators")).json();
}

export async function toggleAdminIndicator(slug: string, enabled: boolean): Promise<void> {
  await adminFetch(`/indicators/${slug}`, {
    method: "PATCH",
    body: JSON.stringify({ enabled }),
  });
}

export async function getAdminIndicatorValues(slug: string): Promise<AdminIndicatorValue[]> {
  return (await adminFetch(`/indicators/${slug}/values`)).json();
}

export async function getAdminSyncRuns(): Promise<AdminSyncRun[]> {
  return (await adminFetch("/sync-runs")).json();
}

export async function triggerAdminSync(): Promise<void> {
  await adminFetch("/sync", { method: "POST" });
}

export async function getAdminCorrections(): Promise<Correction[]> {
  return (await adminFetch("/corrections")).json();
}

export async function createAdminCorrection(payload: {
  indicator_value_id: string;
  new_value: number;
  reason: string;
}): Promise<void> {
  await adminFetch("/corrections", { method: "POST", body: JSON.stringify(payload) });
}

export async function getAdminSources(): Promise<AdminSource[]> {
  return (await adminFetch("/sources")).json();
}

export interface VerifiedClaimPayload {
  quote: string;
  speaker_name: string;
  speaker_role: string | null;
  claim_date: string | null;
  source_url: string | null;
  indicator_slug: string | null;
  verdict: string;
  explanation: string;
}

export async function getAdminVerifiedClaims(): Promise<VerifiedClaim[]> {
  return (await adminFetch("/verified-claims")).json();
}

export async function createAdminVerifiedClaim(payload: VerifiedClaimPayload): Promise<void> {
  await adminFetch("/verified-claims", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAdminVerifiedClaim(id: string, payload: VerifiedClaimPayload): Promise<void> {
  await adminFetch(`/verified-claims/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}
