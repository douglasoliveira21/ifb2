"use client";

import { useState } from "react";

export default function CopyPixKey({
  pixKey,
  label,
  showValue = true,
  buttonLabel = "Copiar chave",
}: {
  pixKey: string;
  label?: string;
  showValue?: boolean;
  buttonLabel?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(pixKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard indisponível (ex: contexto não seguro) — a chave já está
      // visível na tela para cópia manual, então não há fallback necessário.
    }
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
      {showValue && (
        <div>
          {label && <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</p>}
          <p className="stat-figure text-2xl font-bold mt-1">{pixKey}</p>
        </div>
      )}
      <button
        type="button"
        onClick={handleCopy}
        className="shrink-0 border border-ink px-4 py-2 text-sm font-semibold hover:bg-ink hover:text-paper transition"
      >
        {copied ? "Copiado ✓" : buttonLabel}
      </button>
    </div>
  );
}
