"use server";

import { revalidatePath } from "next/cache";
import { createAdminCorrection, toggleAdminIndicator, triggerAdminSync } from "@/lib/admin-api";

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
