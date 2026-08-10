import { classify } from "@/lib/classify";
import { formatDate, formatNumber } from "@/lib/format";
import { valuesForPeriod } from "@/lib/period-compare";
import { CompareIndicator, GovernmentPeriod } from "@/lib/types";
import ClassificationBadge from "@/components/ClassificationBadge";

export default function GovernmentPeriodTable({
  indicators,
  period,
}: {
  indicators: CompareIndicator[];
  period: GovernmentPeriod;
}) {
  const rows = indicators.map((indicator) => ({
    indicator,
    ...valuesForPeriod(indicator.history, period.start_date, period.end_date),
  }));

  const withData = rows.filter((row) => row.startValue !== null && row.endValue !== null);

  if (withData.length === 0) {
    return <p className="text-gray-500">Nenhum indicador com dado disponível neste período.</p>;
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[560px]">
          <thead>
            <tr className="border-b border-ink text-left text-xs uppercase tracking-wide text-gray-500">
              <th className="py-2 pr-4">Indicador</th>
              <th className="py-2 pr-4">Início do mandato</th>
              <th className="py-2 pr-4">Fim do mandato</th>
              <th className="py-2">Classificação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {withData.map(({ indicator, startValue, startDate, endValue, endDate }) => (
              <tr key={indicator.slug}>
                <td className="py-3 pr-4 font-medium">{indicator.name}</td>
                <td className="py-3 pr-4 stat-figure">
                  {formatNumber(startValue!, indicator.unit)}
                  <span className="block text-xs text-gray-500 font-normal">
                    {startDate && formatDate(startDate)}
                  </span>
                </td>
                <td className="py-3 pr-4 stat-figure">
                  {formatNumber(endValue!, indicator.unit)}
                  <span className="block text-xs text-gray-500 font-normal">
                    {endDate && formatDate(endDate)}
                  </span>
                </td>
                <td className="py-3">
                  <ClassificationBadge classification={classify(indicator.polarity, startValue!, endValue!)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-6 text-xs text-gray-500 max-w-2xl">
        Os indicadores mostram a evolução observada durante o período de governo. Isso não
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
