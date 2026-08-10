import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getGovernmentPeriods, getIndicatorDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { CATEGORY_LABELS } from "@/lib/categories";
import ClassificationBadge from "@/components/ClassificationBadge";
import DemoBanner from "@/components/DemoBanner";
import HistoryChart from "@/components/HistoryChart";
import SimpleMarkdown from "@/components/SimpleMarkdown";

type Params = { slug: string };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const { detail } = await getIndicatorDetail(slug);
  if (!detail) return { title: "Indicador não encontrado — Instituto Fiscaliza Brasil" };
  return {
    title: `${detail.name} — Instituto Fiscaliza Brasil`,
    description: detail.description_what ?? undefined,
  };
}

export default async function IndicadorPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const [{ detail, isDemo }, governmentPeriods] = await Promise.all([
    getIndicatorDetail(slug),
    getGovernmentPeriods(),
  ]);

  if (!detail) notFound();

  const { summary, history } = detail;
  const lastPoint = history.at(-1);

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16">
        <Link href="/indicadores" className="text-sm text-gray-500 hover:text-ink underline underline-offset-2">
          ← Todos os indicadores
        </Link>
        <p className="mt-4 text-sm font-medium text-gray-500 uppercase tracking-wide">
          {CATEGORY_LABELS[detail.category] ?? detail.category}
        </p>
        <h1 className="mt-1 text-3xl sm:text-5xl font-extrabold tracking-tight">{detail.name}</h1>

        <div className="mt-6 flex flex-wrap items-end gap-4">
          <div>
            <p className="text-sm text-gray-500">Valor atual</p>
            <p className="stat-figure text-5xl sm:text-6xl font-bold">
              {lastPoint ? formatNumber(lastPoint.value, detail.unit) : "—"}
            </p>
          </div>
          {summary && <ClassificationBadge classification={summary.classification} />}
          {summary?.last_value !== null && summary?.last_value !== undefined && (
            <a
              href={`/api/share/${slug}`}
              download
              className="border border-ink px-3 py-1.5 text-xs font-semibold hover:bg-ink hover:text-paper transition"
            >
              Baixar imagem
            </a>
          )}
        </div>
        {lastPoint && (
          <p className="mt-2 text-sm text-gray-500">Referente a {formatDate(lastPoint.reference_date)}.</p>
        )}
      </section>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        {history.length >= 2 ? (
          <HistoryChart history={history} unit={detail.unit} governmentPeriods={governmentPeriods} />
        ) : (
          <p className="text-sm text-gray-500">Dado ainda não disponível.</p>
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
            <a href={detail.source_url} target="_blank" rel="noopener noreferrer" className="font-medium underline underline-offset-2 hover:text-ink">
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
