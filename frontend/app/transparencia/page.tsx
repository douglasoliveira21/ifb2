import type { Metadata } from "next";
import Link from "next/link";
import { getTransparency } from "@/lib/api";
import { formatDate } from "@/lib/format";
import DemoBanner from "@/components/DemoBanner";

export const metadata: Metadata = {
  title: "Transparência — Instituto Fiscaliza Brasil",
  description: "Fontes, sincronizações, erros conhecidos, correções e metodologias do IFB.",
};

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export default async function TransparenciaPage() {
  const { transparency, isDemo } = await getTransparency();

  if (!transparency) {
    return (
      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
        <p className="text-gray-500">Dado ainda não disponível.</p>
      </section>
    );
  }

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Transparência</h1>
        <p className="mt-3 text-lg text-gray-500 max-w-2xl">
          O próprio IFB precisa ser auditável. Aqui estão as fontes que usamos, quando cada uma
          foi sincronizada pela última vez, erros conhecidos e toda correção manual já feita.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <h2 className="text-xl font-bold uppercase tracking-wide">Fontes</h2>
          <ul className="mt-4 divide-y divide-gray-100">
            {transparency.sources.map((s) => (
              <li key={s.name} className="py-3">
                <p className="font-medium text-sm">{s.name}</p>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-gray-500 underline underline-offset-2 hover:text-ink"
                >
                  {s.url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="border-t border-ink bg-gray-50">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <h2 className="text-xl font-bold uppercase tracking-wide">Últimas sincronizações</h2>
          <ul className="mt-4 divide-y divide-gray-200">
            {transparency.last_syncs.map((s) => (
              <li key={s.source_name} className="py-3 flex items-center justify-between gap-4">
                <span className="text-sm font-medium">{s.source_name}</span>
                <span className="text-xs text-gray-500">
                  {s.finished_at ? formatDateTime(s.finished_at) : "—"} ·{" "}
                  <span className={s.status === "error" ? "text-negative" : "text-positive"}>
                    {s.status}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {transparency.known_errors.length > 0 && (
        <section className="border-t border-ink">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
            <h2 className="text-xl font-bold uppercase tracking-wide">Erros conhecidos</h2>
            <ul className="mt-4 divide-y divide-gray-100">
              {transparency.known_errors.map((e, i) => (
                <li key={i} className="py-3">
                  <p className="text-sm font-medium">{e.source_name}</p>
                  <p className="text-xs text-gray-500">{formatDateTime(e.started_at)}</p>
                  <p className="text-xs text-gray-500 mt-1">{e.error_message}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <section className="border-t border-ink bg-gray-50">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <h2 className="text-xl font-bold uppercase tracking-wide">Correções</h2>
          {transparency.recent_corrections.length === 0 ? (
            <p className="mt-4 text-sm text-gray-500">Nenhuma correção manual registrada ainda.</p>
          ) : (
            <ul className="mt-4 divide-y divide-gray-200">
              {transparency.recent_corrections.map((c, i) => (
                <li key={i} className="py-3">
                  <p className="text-sm font-medium">
                    {c.indicator_name} — {c.location_code} — {formatDate(c.reference_date)}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {c.previous_value} → {c.new_value} — {c.reason}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <h2 className="text-xl font-bold uppercase tracking-wide">Metodologias</h2>
          <ul className="mt-4 divide-y divide-gray-100">
            {transparency.methodologies.map((m) => (
              <li key={m.indicator_slug} className="py-3 flex items-center justify-between gap-4">
                <Link
                  href={`/indicadores/${m.indicator_slug}`}
                  className="text-sm font-medium hover:underline underline-offset-2"
                >
                  {m.indicator_name}
                </Link>
                <span className="text-xs text-gray-500">
                  v{m.version} · {formatDate(m.published_at.slice(0, 10))}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
