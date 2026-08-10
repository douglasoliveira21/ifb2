"use server";

import { revalidatePath } from "next/cache";
import {
  createAdminCorrection,
  createAdminVerifiedClaim,
  toggleAdminIndicator,
  triggerAdminSync,
  updateAdminVerifiedClaim,
  VerifiedClaimPayload,
} from "@/lib/admin-api";

export async function toggleIndicatorAction(formData: FormData): Promise<void> {
  const slug = String(formData.get("slug"));
  const enabled = formData.get("enabled") === "true";
  await toggleAdminIndicator(slug, enabled);
  revalidatePath("/admin/indicadores");
  revalidatePath("/admin");
}

export async function triggerSyncAction(): Promise<void> {
  await triggerAdminSync();
  revalidatePath("/admin/sincronizacoes");
  revalidatePath("/admin");
}

export async function createCorrectionAction(formData: FormData): Promise<void> {
  const indicatorValueId = String(formData.get("indicator_value_id"));
  const newValue = Number(formData.get("new_value"));
  const reason = String(formData.get("reason"));
  const slug = String(formData.get("slug"));

  await createAdminCorrection({ indicator_value_id: indicatorValueId, new_value: newValue, reason });

  revalidatePath("/admin/correcoes");
  revalidatePath(`/admin/correcoes?slug=${slug}`);
}

function claimPayloadFromForm(formData: FormData): VerifiedClaimPayload {
  const nullableString = (name: string): string | null => {
    const value = String(formData.get(name) ?? "").trim();
    return value.length > 0 ? value : null;
  };

  return {
    quote: String(formData.get("quote") ?? "").trim(),
    speaker_name: String(formData.get("speaker_name") ?? "").trim(),
    speaker_role: nullableString("speaker_role"),
    claim_date: nullableString("claim_date"),
    source_url: nullableString("source_url"),
    indicator_slug: nullableString("indicator_slug"),
    verdict: String(formData.get("verdict") ?? ""),
    explanation: String(formData.get("explanation") ?? "").trim(),
  };
}

export async function createVerifiedClaimAction(formData: FormData): Promise<void> {
  await createAdminVerifiedClaim(claimPayloadFromForm(formData));
  revalidatePath("/admin/frases-verificadas");
  revalidatePath("/frases-verificadas");
}

export async function updateVerifiedClaimAction(formData: FormData): Promise<void> {
  const id = String(formData.get("id"));
  await updateAdminVerifiedClaim(id, claimPayloadFromForm(formData));
  revalidatePath("/admin/frases-verificadas");
  revalidatePath("/frases-verificadas");
}
