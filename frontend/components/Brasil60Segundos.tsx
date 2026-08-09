import Link from "next/link";
import { IndicatorSummary } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import ClassificationBadge from "@/components/ClassificationBadge";

export default function Brasil60Segundos({ indicators }: { indicators: IndicatorSummary[] }) {
  const withData = indicators.filter((i) => i.last_value !== null);

  return (
    <section className="border-t border-ink">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        <h2 className="text-2xl sm:text-3xl font-bold">Brasil em 60 segundos</h2>
        <p className="mt-1 text-sm text-gray-500">
          Os indicadores mais essenciais, em uma leitura rápida.
        </p>

        <div className="mt-6 divide-y divide-gray-100">
          {withData.map((indicator) => (
            <div key={indicator.indicator_id} className="py-4 flex items-baseline justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm text-gray-500">{indicator.name}</p>
                <p className="stat-figure text-2xl sm:text-3xl font-bold mt-1">
                  {formatNumber(indicator.last_value as number, indicator.unit)}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <ClassificationBadge classification={indicator.classification} />
                <Link
                  href={`/indicadores/${indicator.slug}`}
                  className="text-xs text-gray-500 underline underline-offset-2 hover:text-ink"
                >
                  ver histórico
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
