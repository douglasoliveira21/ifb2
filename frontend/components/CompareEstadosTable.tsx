import { IndicatorSummary, StateDetail } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import ClassificationBadge from "@/components/ClassificationBadge";

function findIndicator(indicators: IndicatorSummary[], slug: string): IndicatorSummary | undefined {
  return indicators.find((i) => i.slug === slug);
}

export default function CompareEstadosTable({ a, b }: { a: StateDetail; b: StateDetail }) {
  const slugs = Array.from(
    new Set([...a.indicators.map((i) => i.slug), ...b.indicators.map((i) => i.slug)])
  );

  if (slugs.length === 0) {
    return (
      <p className="text-gray-500">
        Nenhum dos dois estados tem indicador disponível ainda.
      </p>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      <div className="hidden sm:grid grid-cols-2 gap-4 pb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
        <span>{a.name}</span>
        <span className="sm:text-right">{b.name}</span>
      </div>

      {slugs.map((slug) => {
        const indicatorA = findIndicator(a.indicators, slug);
        const indicatorB = findIndicator(b.indicators, slug);
        const name = (indicatorA ?? indicatorB)!.name;
        const unit = (indicatorA ?? indicatorB)!.unit;

        return (
          <div key={slug} className="py-4">
            <p className="text-sm font-medium mb-2">{name}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-start">
              <div>
                <p className="sm:hidden text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                  {a.name}
                </p>
                {indicatorA && indicatorA.last_value !== null ? (
                  <>
                    <p className="stat-figure text-xl font-bold">
                      {formatNumber(indicatorA.last_value, unit)}
                    </p>
                    <ClassificationBadge classification={indicatorA.classification} />
                  </>
                ) : (
                  <p className="text-sm text-gray-500">Dado ainda não disponível</p>
                )}
              </div>
              <div className="sm:text-right">
                <p className="sm:hidden text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                  {b.name}
                </p>
                {indicatorB && indicatorB.last_value !== null ? (
                  <>
                    <p className="stat-figure text-xl font-bold">
                      {formatNumber(indicatorB.last_value, unit)}
                    </p>
                    <div className="sm:flex sm:justify-end">
                      <ClassificationBadge classification={indicatorB.classification} />
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-gray-500">Dado ainda não disponível</p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
