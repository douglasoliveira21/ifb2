import Link from "next/link";
import { IndicatorSummary } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import ClassificationBadge from "@/components/ClassificationBadge";

// Curadoria editorial fixa: um indicador por grande categoria, escolhido
// por ser o mais reconhecível do assunto — não é "os que mudaram mais" nem
// "todos com dado". É o que faz a seção cumprir a promessa de "60 segundos"
// em vez de listar os ~70 indicadores do site inteiro.
const CURADOS = [
  "desemprego",
  "ipca",
  "mortalidade-infantil",
  "ideb-anos-iniciais",
  "taxa-mortes-violentas-intencionais-estadual",
  "desmatamento-amazonia-legal",
  "divida-liquida-setor-publico",
  "populacao-residente",
];

export default function Brasil60Segundos({ indicators }: { indicators: IndicatorSummary[] }) {
  const bySlug = new Map(indicators.map((i) => [i.slug, i]));
  const withData = CURADOS.map((slug) => bySlug.get(slug)).filter(
    (i): i is IndicatorSummary => i !== undefined && i.last_value !== null
  );

  if (withData.length === 0) return null;

  return (
    <section className="border-t border-ink">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        <h2 className="text-2xl sm:text-3xl font-bold">Brasil em 60 segundos</h2>
        <p className="mt-1 text-sm text-gray-500">
          Os indicadores mais essenciais, em uma leitura rápida.
        </p>

        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-8 border-t border-ink pt-6">
          {withData.map((indicator, i) => (
            <Link
              key={indicator.indicator_id}
              href={`/indicadores/${indicator.slug}`}
              className={`group block ${i % 2 === 1 ? "border-l border-gray-100 pl-6" : i % 4 !== 0 ? "md:border-l md:border-gray-100 md:pl-6" : ""}`}
            >
              <p className="text-sm text-gray-500 group-hover:text-ink transition-colors">
                {indicator.name}
              </p>
              <p className="stat-figure text-2xl sm:text-3xl font-bold mt-1">
                {formatNumber(indicator.last_value as number, indicator.unit)}
              </p>
              <div className="mt-2">
                <ClassificationBadge classification={indicator.classification} />
              </div>
            </Link>
          ))}
        </div>

        <Link
          href="/indicadores"
          className="mt-8 inline-block text-sm font-semibold underline underline-offset-2 hover:text-ink text-gray-500"
        >
          Ver todos os indicadores →
        </Link>
      </div>
    </section>
  );
}
