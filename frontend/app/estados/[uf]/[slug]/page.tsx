import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getGovernmentPeriods, getIndicatorDetail, getStateDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { CATEGORY_LABELS } from "@/lib/categories";
import { SITE_URL } from "@/lib/site";
import ClassificationBadge from "@/components/ClassificationBadge";
import DemoBanner from "@/components/DemoBanner";
import HistoryChart from "@/components/HistoryChart";
import SimpleMarkdown from "@/components/SimpleMarkdown";

type Params = { uf: string; slug: string };

// Gera uma frase de contexto específica do estado a partir dos dados reais
// (não é texto-molde com o nome trocado) — evita que a mesma prosa genérica
// se repita nas ~1.200 páginas de indicador × estado, o que pesa contra o
// site em rankings de busca (conteúdo quase duplicado em escala).
function buildContextSentence(
  stateName: string,
  unit: string,
  first: { reference_date: string; value: number } | undefined,
  last: { reference_date: string; value: number } | undefined
): string | null {
  if (!first || !last || first.reference_date === last.reference_date || first.value === 0) return null;
  const deltaPct = ((last.value - first.value) / Math.abs(first.value)) * 100;
  const direction = deltaPct > 0.5 ? "subiu" : deltaPct < -0.5 ? "caiu" : "se manteve estável";
  const magnitude = Math.abs(deltaPct) >= 1 ? ` (${Math.abs(deltaPct).toFixed(1).replace(".", ",")}%)` : "";
  return `Em ${stateName}, o valor foi de ${formatNumber(first.value, unit)} em ${formatDate(first.reference_date)} para ${formatNumber(last.value, unit)} em ${formatDate(last.reference_date)} — ${direction}${magnitude} no período.`;
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { uf, slug } = await params;
  const [{ detail }, { detail: state }] = await Promise.all([getIndicatorDetail(slug, uf), getStateDetail(uf)]);
  if (!detail || !state) return { title: "Não encontrado — Instituto Fiscaliza Brasil" };
  const year = detail.summary?.last_date?.slice(0, 4);
  const title = `${detail.name} em ${state.name}${year ? ` (${year})` : ""} — Instituto Fiscaliza Brasil`;
  const value =
    detail.summary?.last_value !== null && detail.summary?.last_value !== undefined
      ? formatNumber(detail.summary.last_value, detail.unit)
      : null;
  const description = value
    ? `${detail.name} em ${state.name}: ${value}${year ? ` (${year})` : ""}. Histórico completo e fonte oficial dos dados.`
    : `Consulte ${detail.name.toLowerCase()} de ${state.name}, sua evolução histórica e a fonte oficial dos dados.`;
  return {
    title,
    description,
    alternates: { canonical: `/estados/${uf.toLowerCase()}/${slug}` },
    openGraph: { title, description, type: "article" },
    twitter: { card: "summary", title, description },
  };
}

export default async function IndicadorEstadoPage({ params }: { params: Promise<Params> }) {
  const { uf, slug } = await params;
  const [{ detail, isDemo }, { detail: state }, governmentPeriods] = await Promise.all([
    getIndicatorDetail(slug, uf),
    getStateDetail(uf),
    getGovernmentPeriods(uf),
  ]);

  if (!detail || !state) notFound();

  const { summary, history } = detail;
  const lastPoint = history.at(-1);
  const contextSentence = buildContextSentence(state.name, detail.unit, history[0], lastPoint);

  const datasetJsonLd = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `${detail.name} — ${state.name}`,
    description: contextSentence ?? `${detail.description_what ?? detail.name} Dados específicos de ${state.name}.`,
    url: `${SITE_URL}/estados/${uf.toLowerCase()}/${slug}`,
    keywords: [detail.name, state.name, CATEGORY_LABELS[detail.category] ?? detail.category, "indicador público"],
    creator: { "@type": "Organization", name: "Instituto Fiscaliza Brasil", url: SITE_URL },
    ...(detail.source_name && {
      sourceOrganization: { "@type": "Organization", name: detail.source_name, url: detail.source_url },
    }),
    ...(lastPoint && { temporalCoverage: `${history[0]?.reference_date}/${lastPoint.reference_date}` }),
    spatialCoverage: { "@type": "AdministrativeArea", name: state.name },
    variableMeasured: detail.name,
    ...(detail.unit && { unitText: detail.unit }),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetJsonLd).replace(/</g, "\\u003c") }}
      />
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16">
        <Link
          href={`/estados/${uf.toLowerCase()}`}
          className="text-sm text-gray-500 hover:text-ink underline underline-offset-2"
        >
          ← Indicadores de {state.name}
        </Link>
        <p className="mt-4 text-sm font-medium text-gray-500 uppercase tracking-wide">
          {CATEGORY_LABELS[detail.category] ?? detail.category} · {state.name}
        </p>
        <h1 className="mt-1 text-3xl sm:text-5xl font-extrabold tracking-tight">
          {detail.name} de {state.name}
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
        {contextSentence && <p className="mt-4 text-base leading-relaxed">{contextSentence}</p>}
        <p className="mt-4 text-sm text-gray-500">
          Veja também{" "}
          <Link href={`/indicadores/${slug}`} className="underline underline-offset-2 hover:text-ink">
            {detail.name} no Brasil
          </Link>
          .
        </p>
      </section>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        {history.length >= 2 ? (
          <HistoryChart history={history} unit={detail.unit} governmentPeriods={governmentPeriods} />
        ) : (
          <p className="text-sm text-gray-500">Dado ainda não disponível para {state.name}.</p>
        )}
      </section>

      {history.length > 0 && (
        <section className="border-t border-ink bg-gray-50">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8 grid grid-cols-2 sm:grid-cols-5 gap-6">
            <Stat label="Valor inicial" value={history[0].value} unit={detail.unit} />
            <Stat label="Valor atual" value={lastPoint?.value ?? null} unit={detail.unit} />
            <Stat label="Menor valor" value={detail.min_value} unit={detail.unit} />
            <Stat label="Maior valor" value={detail.max_value} unit={detail.unit} />
            <Stat label="Média" value={detail.avg_value} unit={detail.unit} />
          </div>
        </section>
      )}

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

function Stat({ label, value, unit }: { label: string; value: number | null; unit: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="stat-figure text-xl font-bold mt-1">{value !== null ? formatNumber(value, unit) : "—"}</p>
    </div>
  );
}
