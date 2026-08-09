import { classify } from "@/lib/classify";
import { formatDate, formatNumber } from "@/lib/format";
import { valuesForPeriod } from "@/lib/period-compare";
import { CompareIndicator, GovernmentPeriod } from "@/lib/types";
import ClassificationBadge from "@/components/ClassificationBadge";

function PeriodColumn({ indicator, period }: { indicator: CompareIndicator; period: GovernmentPeriod }) {
  const { startValue, startDate, endValue, endDate } = valuesForPeriod(
    indicator.history,
    period.start_date,
    period.end_date
  );

  if (startValue === null || endValue === null) {
    return <p className="text-sm text-gray-500">Dado ainda não disponível neste período</p>;
  }

  const classification = classify(indicator.polarity, startValue, endValue);

  return (
    <div>
      <p className="stat-figure text-lg font-bold">
        {formatNumber(startValue, indicator.unit)}
        {" → "}
        {formatNumber(endValue, indicator.unit)}
      </p>
      <p className="text-xs text-gray-500 mt-0.5">
        {startDate && formatDate(startDate)} – {endDate && formatDate(endDate)}
      </p>
      <ClassificationBadge classification={classification} />
    </div>
  );
}

export default function ComparePeriodosTable({
  indicators,
  periodA,
  periodB,
}: {
  indicators: CompareIndicator[];
  periodA: GovernmentPeriod;
  periodB: GovernmentPeriod;
}) {
  return (
    <div>
      <div className="hidden sm:grid grid-cols-2 gap-4 pb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
        <span>
          {periodA.holder_name} ({formatDate(periodA.start_date)} –{" "}
          {periodA.end_date ? formatDate(periodA.end_date) : "atual"})
        </span>
        <span>
          {periodB.holder_name} ({formatDate(periodB.start_date)} –{" "}
          {periodB.end_date ? formatDate(periodB.end_date) : "atual"})
        </span>
      </div>

      <div className="divide-y divide-gray-100">
        {indicators.map((indicator) => (
          <div key={indicator.slug} className="py-4">
            <p className="text-sm font-medium mb-2">{indicator.name}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="sm:hidden text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                  {periodA.holder_name} ({formatDate(periodA.start_date)})
                </p>
                <PeriodColumn indicator={indicator} period={periodA} />
              </div>
              <div>
                <p className="sm:hidden text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                  {periodB.holder_name} ({formatDate(periodB.start_date)})
                </p>
                <PeriodColumn indicator={indicator} period={periodB} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-6 text-xs text-gray-500 max-w-2xl">
        Os indicadores mostram a evolução observada durante cada período de governo. Isso não
        significa que todas as alterações tenham sido causadas diretamente pelo governante ou por
        suas políticas — correlação temporal não é causalidade. Veja a{" "}
        <a href="/metodologia" className="underline underline-offset-2 hover:text-ink">
          metodologia
        </a>
        .
      </p>
    </div>
  );
}
