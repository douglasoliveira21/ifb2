import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getMunicipioDetail } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import ClassificationBadge from "@/components/ClassificationBadge";

type Params = { uf: string; codigo: string };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { uf, codigo } = await params;
  const detail = await getMunicipioDetail(uf, codigo);
  if (!detail) return { title: "Município não encontrado — Instituto Fiscaliza Brasil" };
  const title = `Indicadores de ${detail.name} (${detail.uf}) — Dados públicos oficiais | Instituto Fiscaliza Brasil`;
  const description = `Consulte os indicadores públicos oficiais de ${detail.name} (${detail.uf}), indicador por indicador.`;
  return {
    title,
    description,
    alternates: { canonical: `/municipios/${uf.toLowerCase()}/${codigo}` },
    openGraph: { title, description },
    twitter: { card: "summary", title, description },
  };
}

export default async function MunicipioPage({ params }: { params: Promise<Params> }) {
  const { uf, codigo } = await params;
  const detail = await getMunicipioDetail(uf, codigo);

  if (!detail) notFound();

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16">
        <Link
          href={`/municipios/${uf.toLowerCase()}`}
          className="text-sm text-gray-500 hover:text-ink underline underline-offset-2"
        >
          ← Municípios de {detail.uf}
        </Link>
        <p className="mt-4 text-sm font-medium text-gray-500 uppercase tracking-wide">{detail.uf}</p>
        <h1 className="mt-1 text-3xl sm:text-5xl font-extrabold tracking-tight">{detail.name}</h1>
        <p className="mt-3 text-lg text-gray-500">
          Indicadores municipais piloto — ano mais recente disponível, sem série histórica.
        </p>
      </section>

      <section className="border-t border-ink mt-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          {detail.indicators.length === 0 ? (
            <p className="text-gray-500">Dado ainda não disponível para este município.</p>
          ) : (
            <div className="divide-y divide-gray-100">
              {detail.indicators.map((indicator) => (
                <div key={indicator.indicator_id} className="py-4 flex items-baseline justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm text-gray-500">{indicator.name}</p>
                    <p className="stat-figure text-2xl sm:text-3xl font-bold mt-1">
                      {indicator.last_value !== null
                        ? formatNumber(indicator.last_value, indicator.unit)
                        : "—"}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <ClassificationBadge classification={indicator.classification} />
                    <Link
                      href={`/municipios/${uf.toLowerCase()}/${codigo}/${indicator.slug}`}
                      className="text-xs text-gray-500 underline underline-offset-2 hover:text-ink"
                    >
                      ver indicador
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
          <p className="mt-8 text-xs text-gray-500">
            Piloto de granularidade municipal: só transferências constitucionais e despesa com
            pessoal, um único ano (o mais recente completo) — sem série histórica ainda.
          </p>
        </div>
      </section>
    </>
  );
}
