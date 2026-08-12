import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getIndicatorDetail, getMunicipioDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { CATEGORY_LABELS } from "@/lib/categories";
import { SITE_URL } from "@/lib/site";
import ClassificationBadge from "@/components/ClassificationBadge";
import HistoryChart from "@/components/HistoryChart";
import SimpleMarkdown from "@/components/SimpleMarkdown";

type Params = { uf: string; codigo: string; slug: string };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { uf, codigo, slug } = await params;
  const [{ detail }, municipio] = await Promise.all([
    getIndicatorDetail(slug, codigo),
    getMunicipioDetail(uf, codigo),
  ]);
  if (!detail || !municipio) return { title: "Não encontrado — Instituto Fiscaliza Brasil" };
  const title = `${detail.name} de ${municipio.name} (${municipio.uf}) — Dados públicos oficiais | Instituto Fiscaliza Brasil`;
  const description = `Consulte ${detail.name.toLowerCase()} de ${municipio.name} (${municipio.uf}) e a fonte oficial dos dados.`;
  return {
    title,
    description,
    alternates: { canonical: `/municipios/${uf.toLowerCase()}/${codigo}/${slug}` },
    openGraph: { title, description, type: "article" },
    twitter: { card: "summary", title, description },
  };
}

export default async function IndicadorMunicipioPage({ params }: { params: Promise<Params> }) {
  const { uf, codigo, slug } = await params;
  const [{ detail, isDemo }, municipio] = await Promise.all([
    getIndicatorDetail(slug, codigo),
    getMunicipioDetail(uf, codigo),
  ]);

  if (!detail || !municipio) notFound();

  const { summary, history } = detail;
  const lastPoint = history.at(-1);

  const datasetJsonLd = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `${detail.name} — ${municipio.name} (${municipio.uf})`,
    description: `${detail.description_what ?? detail.name} Dados específicos de ${municipio.name} (${municipio.uf}).`,
    url: `${SITE_URL}/municipios/${uf.toLowerCase()}/${codigo}/${slug}`,
    keywords: [detail.name, municipio.name, CATEGORY_LABELS[detail.category] ?? detail.category, "indicador público"],
    creator: { "@type": "Organization", name: "Instituto Fiscaliza Brasil", url: SITE_URL },
    ...(detail.source_name && {
      sourceOrganization: { "@type": "Organization", name: detail.source_name, url: detail.source_url },
    }),
    ...(lastPoint && { temporalCoverage: `${history[0]?.reference_date}/${lastPoint.reference_date}` }),
    spatialCoverage: { "@type": "AdministrativeArea", name: `${municipio.name} (${municipio.uf})` },
    variableMeasured: detail.name,
    ...(detail.unit && { unitText: detail.unit }),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetJsonLd).replace(/</g, "\\u003c") }}
      />
      {isDemo && <p className="text-xs text-gray-500 px-4 pt-2">DADOS DE DEMONSTRAÇÃO</p>}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16">
        <Link
          href={`/municipios/${uf.toLowerCase()}/${codigo}`}
          className="text-sm text-gray-500 hover:text-ink underline underline-offset-2"
        >
          ← Indicadores de {municipio.name}
        </Link>
        <p className="mt-4 text-sm font-medium text-gray-500 uppercase tracking-wide">
          {CATEGORY_LABELS[detail.category] ?? detail.category} · {municipio.name} ({municipio.uf})
        </p>
        <h1 className="mt-1 text-3xl sm:text-5xl font-extrabold tracking-tight">
          {detail.name} de {municipio.name}
        </h1>

        <div className="mt-6 flex flex-wrap items-end gap-4">
          <div>
            <p className="text-sm text-gray-500">Valor atual</p>
            <p className="stat-figure text-5xl sm:text-6xl font-bold">
              {lastPoint ? formatNumber(lastPoint.value, detail.unit) : "—"}
            </p>
          </div>
          {summary && <ClassificationBadge classification={summary.classification} />}
        </div>
        {lastPoint && (
          <p className="mt-2 text-sm text-gray-500">Referente a {formatDate(lastPoint.reference_date)}.</p>
        )}
        <p className="mt-4 text-sm text-gray-500">
          Veja também{" "}
          <Link href={`/indicadores/${slug}`} className="underline underline-offset-2 hover:text-ink">
            {detail.name} no Brasil
          </Link>{" "}
          e{" "}
          <Link href={`/estados/${uf.toLowerCase()}/${slug}`} className="underline underline-offset-2 hover:text-ink">
            em {municipio.uf}
          </Link>
          .
        </p>
      </section>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        {history.length >= 2 ? (
          <HistoryChart history={history} unit={detail.unit} governmentPeriods={[]} />
        ) : (
          <p className="text-sm text-gray-500">
            Piloto de granularidade municipal: só o ano mais recente disponível, sem série histórica ainda.
          </p>
        )}
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 grid sm:grid-cols-2 gap-10">
          <div>
            <h2 className="text-lg font-bold">O que este indicador mede?</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              {detail.description_what ?? "Descrição ainda não disponível."}
            </p>
          </div>
          <div>
            <h2 className="text-lg font-bold">Como interpretar?</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              {detail.description_how ?? "Descrição ainda não disponível."}
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-ink bg-gray-50">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 grid sm:grid-cols-3 gap-6 text-sm">
          <div>
            <p className="text-gray-500">Fonte</p>
            <a
              href={detail.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium underline underline-offset-2 hover:text-ink"
            >
              {detail.source_name}
            </a>
          </div>
          <div>
            <p className="text-gray-500">Frequência de atualização</p>
            <p className="font-medium">{detail.update_frequency ?? "—"}</p>
          </div>
          <div>
            <p className="text-gray-500">Metodologia geral do IFB</p>
            <Link href="/metodologia" className="font-medium underline underline-offset-2 hover:text-ink">
              Como calculamos e comparamos
            </Link>
          </div>
        </div>
      </section>

      {detail.methodology && (
        <section className="border-t border-ink">
          <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10">
            <SimpleMarkdown content={detail.methodology} />
          </div>
        </section>
      )}
    </>
  );
}
