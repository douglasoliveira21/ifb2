import type { Metadata } from "next";
import { getCompareIndicators, getGovernmentPeriods } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import DemoBanner from "@/components/DemoBanner";
import HistoryChart from "@/components/HistoryChart";

export const metadata: Metadata = {
  title: "Linha do tempo do Brasil — Instituto Fiscaliza Brasil",
  description: "Como cada indicador nacional evoluiu ao longo do tempo, com os períodos de governo marcados como referência.",
};

type SearchParams = { indicador?: string };

export default async function LinhaDoTempoPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const { indicador } = await searchParams;
  const [{ indicators, isDemo }, governmentPeriods] = await Promise.all([
    getCompareIndicators(),
    getGovernmentPeriods(),
  ]);

  const sorted = [...indicators].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  const selected = sorted.find((i) => i.slug === indicador) ?? sorted[0];

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Linha do tempo</h1>
        <p className="mt-3 text-lg text-gray-500">
          Como o Brasil mudou, indicador por indicador, desde o início de cada série disponível.
        </p>
        <p className="mt-4 text-sm text-gray-500 max-w-2xl">
          Os períodos de governo aparecem apenas como referência histórica — o IFB nunca atribui
          automaticamente uma mudança de indicador a um governante. Veja a{" "}
          <a href="/metodologia" className="underline underline-offset-2 hover:text-ink">
            metodologia
          </a>
          .
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          {sorted.length === 0 ? (
            <p className="text-gray-500">Dado ainda não disponível.</p>
          ) : (
            <>
              <form method="get" className="flex flex-wrap items-end gap-4">
                <label className="text-sm">
                  <span className="block text-gray-500 mb-1">Indicador</span>
                  <select
                    name="indicador"
                    defaultValue={selected.slug}
                    className="border border-ink px-3 py-2 text-sm bg-paper min-w-[280px]"
                  >
                    {sorted.map((i) => (
                      <option key={i.slug} value={i.slug}>
                        {i.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="submit" className="bg-yellow text-ink text-sm font-semibold px-4 py-2">
                  Ver
                </button>
              </form>

              <div className="mt-8">
                <h2 className="text-2xl font-bold">{selected.name}</h2>
                {selected.history.length >= 2 ? (
                  <div className="mt-6">
                    <HistoryChart
                      history={selected.history}
                      unit={selected.unit}
                      governmentPeriods={governmentPeriods}
                    />
                  </div>
                ) : (
                  <p className="mt-4 text-gray-500">Histórico insuficiente para exibir gráfico.</p>
                )}

                {selected.history.length > 0 && (
                  <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-6">
                    <Stat
                      label={`Valor em ${formatDate(selected.history[0].reference_date)}`}
                      value={formatNumber(selected.history[0].value, selected.unit)}
                    />
                    <Stat
                      label={`Valor em ${formatDate(selected.history[selected.history.length - 1].reference_date)}`}
                      value={formatNumber(
                        selected.history[selected.history.length - 1].value,
                        selected.unit
                      )}
                    />
                    <Stat
                      label="Menor valor da série"
                      value={formatNumber(
                        Math.min(...selected.history.map((p) => p.value)),
                        selected.unit
                      )}
                    />
                    <Stat
                      label="Maior valor da série"
                      value={formatNumber(
                        Math.max(...selected.history.map((p) => p.value)),
                        selected.unit
                      )}
                    />
                  </div>
                )}

                <a
                  href={`/indicadores/${selected.slug}`}
                  className="mt-8 inline-block text-sm underline underline-offset-2 hover:text-ink text-gray-500"
                >
                  Ver a página completa deste indicador (fonte, metodologia) →
                </a>
              </div>
            </>
          )}
        </div>
      </section>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="stat-figure text-xl font-bold mt-1">{value}</p>
    </div>
  );
}
