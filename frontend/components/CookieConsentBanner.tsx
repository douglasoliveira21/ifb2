"use client";

import Link from "next/link";
import { ConsentValue, setStoredConsent, useConsent } from "@/lib/consent";

export default function CookieConsentBanner() {
  const consent = useConsent();

  if (consent !== null) return null;

  function handle(value: ConsentValue) {
    setStoredConsent(value);
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-ink bg-paper">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <p className="text-sm text-gray-500 leading-relaxed max-w-2xl">
          Usamos cookies do Google Analytics só para entender, de forma agregada, quais páginas
          são mais acessadas — nunca para publicidade. Eles só são carregados se você aceitar.
          Detalhes em{" "}
          <Link href="/privacidade" className="underline underline-offset-2 hover:text-ink">
            /privacidade
          </Link>
          .
        </p>
        <div className="flex gap-3 shrink-0">
          <button
            type="button"
            onClick={() => handle("rejected")}
            className="text-sm font-medium px-4 py-2 border border-ink hover:bg-gray-50 transition"
          >
            Recusar
          </button>
          <button
            type="button"
            onClick={() => handle("accepted")}
            className="bg-yellow text-ink text-sm font-semibold px-4 py-2 hover:brightness-95 transition"
          >
            Aceitar
          </button>
        </div>
      </div>
    </div>
  );
}
