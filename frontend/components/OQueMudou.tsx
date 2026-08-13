import { IndicatorSummary } from "@/lib/types";
import { formatNumber } from "@/lib/format";

const MAX_ITEMS = 8;

export default function OQueMudou({ indicators }: { indicators: IndicatorSummary[] }) {
  // `first_value`/`last_value` cobrem a série inteira do indicador (às
  // vezes desde os anos 2000), não "desde a última sincronização" — o IFB
  // não guarda essa data por indicador. Por isso o título e o recorte
  // (maior variação relativa, não "tudo que já mudou algum dia") precisam
  // ser honestos sobre o que este número realmente representa.
  const changed = indicators
    .filter(
      (i) =>
        i.first_value !== null && i.last_value !== null && i.change_absolute !== 0 && i.first_value !== 0
    )
    .sort((a, b) => {
      const pctA = Math.abs((a.change_absolute as number) / (a.first_value as number));
      const pctB = Math.abs((b.change_absolute as number) / (b.first_value as number));
      return pctB - pctA;
    })
    .slice(0, MAX_ITEMS);

  if (changed.length === 0) return null;

  return (
    <section className="border-t border-ink bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        <h2 className="text-2xl sm:text-3xl font-bold">Maiores variações desde o início da série</h2>
        <p className="mt-1 text-sm text-gray-500">
          Comparação entre o primeiro e o último dado disponível de cada indicador — não é
          necessariamente uma mudança recente.
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
