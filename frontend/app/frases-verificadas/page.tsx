import Link from "next/link";
import type { Metadata } from "next";
import { getVerifiedClaims } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Frases Verificadas — Instituto Fiscaliza Brasil",
  description: "Citações de campanha e discurso, checadas contra indicadores públicos reais.",
};

const VERDICT_LABELS: Record<string, string> = {
  CONFIRMADO: "Confirmado",
  PARCIALMENTE_CONFIRMADO: "Parcialmente confirmado",
  DISTORCIDO: "Distorcido",
  FALSO: "Falso",
  INCONCLUSIVO: "Inconclusivo",
};

const VERDICT_COLOR: Record<string, string> = {
  CONFIRMADO: "text-positive",
  PARCIALMENTE_CONFIRMADO: "text-neutral",
  DISTORCIDO: "text-negative",
  FALSO: "text-negative",
  INCONCLUSIVO: "text-neutral",
};

export default async function FrasesVerificadasPage() {
  const claims = await getVerifiedClaims();

  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Frases Verificadas</h1>
        <p className="mt-3 text-lg text-gray-500">
          Citações de campanha e discurso, checadas indicador por indicador contra dado oficial.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10">
          {claims.length === 0 ? (
            <p className="text-gray-500">Nenhuma frase verificada publicada ainda.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {claims.map((claim) => (
                <li key={claim.id} className="py-8 first:pt-0">
                  <p className="text-xl font-medium leading-snug">&ldquo;{claim.quote}&rdquo;</p>
                  <p className="mt-2 text-sm text-gray-500">
                    {claim.speaker_name}
                    {claim.speaker_role ? `, ${claim.speaker_role}` : ""}
                    {claim.claim_date ? ` — ${formatDate(claim.claim_date)}` : ""}
                    {claim.source_url && (
                      <>
                        {" · "}
                        <a
                          href={claim.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline underline-offset-2 hover:text-ink"
                        >
                          fonte
                        </a>
                      </>
                    )}
                  </p>

                  <p className={`mt-4 text-sm font-semibold uppercase tracking-wide ${VERDICT_COLOR[claim.verdict] ?? ""}`}>
                    {VERDICT_LABELS[claim.verdict] ?? claim.verdict}
                  </p>
                  <p className="mt-1 text-sm text-gray-500 leading-relaxed">{claim.explanation}</p>

                  {claim.indicator_slug && (
                    <Link
                      href={`/indicadores/${claim.indicator_slug}`}
                      className="mt-2 inline-block text-sm underline underline-offset-2 hover:text-ink"
                    >
                      Ver indicador completo →
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </>
  );
}
