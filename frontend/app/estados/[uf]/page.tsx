import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getStateDetail } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import ClassificationBadge from "@/components/ClassificationBadge";
import DemoBanner from "@/components/DemoBanner";

type Params = { uf: string };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { uf } = await params;
  const { detail } = await getStateDetail(uf);
  if (!detail) return { title: "Estado não encontrado — Instituto Fiscaliza Brasil" };
  const title = `Indicadores de ${detail.name} — Dados públicos oficiais | Instituto Fiscaliza Brasil`;
  const description = `Consulte os indicadores públicos oficiais de ${detail.name}: economia, saúde, educação, segurança e mais, indicador por indicador.`;
  return {
    title,
    description,
    alternates: { canonical: `/estados/${uf.toLowerCase()}` },
    openGraph: { title, description },
    twitter: { card: "summary", title, description },
  };
}

export default async function EstadoPage({ params }: { params: Promise<Params> }) {
  const { uf } = await params;
  const { detail, isDemo } = await getStateDetail(uf);

  if (!detail) notFound();

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16">
        <Link href="/estados" className="text-sm text-gray-500 hover:text-ink underline underline-offset-2">
          ← Todos os estados
        </Link>
        <p className="mt-4 text-sm font-medium text-gray-500 uppercase tracking-wide">{detail.code}</p>
        <h1 className="mt-1 text-3xl sm:text-5xl font-extrabold tracking-tight">{detail.name}</h1>
        <p className="mt-3 text-lg text-gray-500">Placar de {detail.name}</p>
        <Link
          href={`/municipios/${detail.code.toLowerCase()}`}
          className="mt-2 inline-block text-sm underline underline-offset-2 hover:text-ink"
        >
          Ver municípios deste estado →
        </Link>
      </section>

      <section className="border-t border-ink mt-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          {detail.indicators.length === 0 ? (
            <p className="text-gray-500">Dado ainda não disponível para este estado.</p>
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
                      href={`/estados/${uf.toLowerCase()}/${indicator.slug}`}
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
            Nem todo indicador nacional tem série própria por estado ainda — a lista acima mostra
            apenas os indicadores com dado disponível para {detail.name}.
          </p>
        </div>
      </section>
    </>
  );
}
