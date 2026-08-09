import { IndicatorSummary } from "@/lib/types";

function count(indicators: IndicatorSummary[], classification: string) {
  return indicators.filter((i) => i.classification === classification).length;
}

export default function PlacarBrasil({ indicators }: { indicators: IndicatorSummary[] }) {
  const stats = [
    { value: count(indicators, "MELHOROU"), label: "Indicadores\nmelhoraram" },
    { value: count(indicators, "PIOROU"), label: "Indicadores\npioraram" },
    { value: count(indicators, "ESTAVEL"), label: "Permaneceram\nestáveis" },
    {
      value: count(indicators, "SEM_DADOS") + count(indicators, "INCONCLUSIVO"),
      label: "Aguardam\natualização",
    },
  ];

  return (
    <section className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
      <p className="text-sm font-medium text-gray-500">Desde o início do período selecionado</p>
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-8 border-t border-ink pt-6">
        {stats.map((stat, i) => (
          <div key={stat.label} className={i > 0 ? "md:border-l md:border-gray-100 md:pl-6" : ""}>
            <p className="stat-figure text-5xl sm:text-6xl font-bold">{stat.value}</p>
            <p className="mt-2 text-sm text-gray-500 whitespace-pre-line">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
