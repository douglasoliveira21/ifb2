import { IndicatorSummary } from "@/lib/types";
import { formatNumber } from "@/lib/format";

export default function OQueMudou({ indicators }: { indicators: IndicatorSummary[] }) {
  const changed = indicators.filter(
    (i) => i.first_value !== null && i.last_value !== null && i.change_absolute !== 0
  );

  if (changed.length === 0) return null;

  return (
    <section className="border-t border-ink bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        <h2 className="text-2xl sm:text-3xl font-bold">O que mudou desde a última atualização?</h2>
        <p className="mt-1 text-sm text-gray-500">
          Apenas indicadores que receberam novos dados aparecem aqui.
        </p>

        <div className="mt-6 grid sm:grid-cols-2 gap-x-8 gap-y-6">
          {changed.map((indicator) => (
            <div key={indicator.indicator_id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-4 py-3 border-b border-gray-100">
              <span className="text-sm font-medium">{indicator.name}</span>
              <span className="stat-figure text-sm font-semibold">
                {formatNumber(indicator.first_value as number, indicator.unit)}
                {" → "}
                {formatNumber(indicator.last_value as number, indicator.unit)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
