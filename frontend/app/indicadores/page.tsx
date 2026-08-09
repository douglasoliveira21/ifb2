import Link from "next/link";
import type { Metadata } from "next";
import { getHomeData } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { CATEGORY_LABELS, CATEGORY_ORDER } from "@/lib/categories";
import ClassificationBadge from "@/components/ClassificationBadge";
import DemoBanner from "@/components/DemoBanner";
import { IndicatorSummary } from "@/lib/types";

export const metadata: Metadata = {
  title: "Indicadores — Instituto Fiscaliza Brasil",
  description: "Todos os indicadores acompanhados pelo IFB, organizados por categoria.",
};

export default async function IndicadoresPage() {
  const { indicators, isDemo } = await getHomeData();

  const byCategory = new Map<string, IndicatorSummary[]>();
  for (const indicator of indicators) {
    const list = byCategory.get(indicator.category) ?? [];
    list.push(indicator);
    byCategory.set(indicator.category, list);
  }

  const categories = CATEGORY_ORDER.filter((c) => byCategory.has(c));

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Indicadores</h1>
        <p className="mt-3 text-lg text-gray-500">
          Todos os indicadores acompanhados pelo IFB, organizados por categoria.
        </p>
      </section>

      {categories.length === 0 && (
        <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16 border-t border-ink">
          <p className="text-gray-500">Dado ainda não disponível.</p>
        </section>
      )}

      {categories.map((category) => (
        <section key={category} className="border-t border-ink">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
            <h2 className="text-xl font-bold uppercase tracking-wide">
              {CATEGORY_LABELS[category] ?? category}
            </h2>
            <ul className="mt-4 divide-y divide-gray-100">
              {byCategory.get(category)!.map((indicator) => (
                <li key={indicator.indicator_id}>
                  <Link
                    href={`/indicadores/${indicator.slug}`}
                    className="py-4 flex items-center justify-between gap-4 group"
                  >
                    <span className="min-w-0 text-base font-medium group-hover:underline underline-offset-2">
                      {indicator.name}
                    </span>
                    <span className="flex items-center gap-4 shrink-0">
                      {indicator.last_value !== null ? (
                        <span className="stat-figure text-lg font-semibold">
                          {formatNumber(indicator.last_value, indicator.unit)}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-500">Sem dados</span>
                      )}
                      <ClassificationBadge classification={indicator.classification} />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>
      ))}
    </>
  );
}
