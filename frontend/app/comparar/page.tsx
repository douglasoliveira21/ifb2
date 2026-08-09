import Link from "next/link";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { getCompareIndicators, getGovernmentPeriods, getStateDetail, getStates } from "@/lib/api";
import { formatDate } from "@/lib/format";
import CompareEstadosTable from "@/components/CompareEstadosTable";
import ComparePeriodosTable from "@/components/ComparePeriodosTable";
import DemoBanner from "@/components/DemoBanner";

export const metadata: Metadata = {
  title: "Comparar — Instituto Fiscaliza Brasil",
  description: "Compare estados ou períodos, indicador por indicador — sem vencedor geral.",
};

type SearchParams = {
  modo?: string;
  uf_a?: string;
  uf_b?: string;
  periodo_a?: string;
  periodo_b?: string;
};

export default async function CompararPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const { modo = "estados", uf_a, uf_b, periodo_a, periodo_b } = await searchParams;

  let table: ReactNode = null;
  let isDemo = false;
  let picker: ReactNode = null;

  if (modo === "periodos") {
    const [{ indicators, isDemo: indicatorsIsDemo }, periods] = await Promise.all([
      getCompareIndicators(),
      getGovernmentPeriods(),
    ]);
    isDemo = indicatorsIsDemo;

    picker = (
      <form method="get" className="flex flex-wrap items-end gap-4">
        <input type="hidden" name="modo" value="periodos" />
        <label className="text-sm">
          <span className="block text-gray-500 mb-1">Período A</span>
          <select
            name="periodo_a"
            defaultValue={periodo_a ?? ""}
            className="border border-ink px-3 py-2 text-sm bg-paper max-w-[220px]"
          >
            <option value="" disabled>
              Selecione
            </option>
            {periods.map((period) => (
              <option key={period.start_date} value={period.start_date}>
                {period.holder_name} ({formatDate(period.start_date)})
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="block text-gray-500 mb-1">Período B</span>
          <select
            name="periodo_b"
            defaultValue={periodo_b ?? ""}
            className="border border-ink px-3 py-2 text-sm bg-paper max-w-[220px]"
          >
            <option value="" disabled>
              Selecione
            </option>
            {periods.map((period) => (
              <option key={period.start_date} value={period.start_date}>
                {period.holder_name} ({formatDate(period.start_date)})
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="bg-yellow text-ink text-sm font-semibold px-4 py-2">
          Comparar
        </button>
      </form>
    );

    if (periodo_a && periodo_b) {
      const periodA = periods.find((p) => p.start_date === periodo_a);
      const periodB = periods.find((p) => p.start_date === periodo_b);
      if (periodA && periodB && indicators.length > 0) {
        table = <ComparePeriodosTable indicators={indicators} periodA={periodA} periodB={periodB} />;
      } else if (indicators.length === 0) {
        table = <p className="text-gray-500">Dado ainda não disponível.</p>;
      } else {
        table = <p className="text-gray-500">Período não encontrado.</p>;
      }
    }
  } else {
    const { states, isDemo: statesIsDemo } = await getStates();
    isDemo = statesIsDemo;

    picker = (
      <form method="get" className="flex flex-wrap items-end gap-4">
        <input type="hidden" name="modo" value="estados" />
        <label className="text-sm">
          <span className="block text-gray-500 mb-1">Estado A</span>
          <select
            name="uf_a"
            defaultValue={uf_a ?? ""}
            className="border border-ink px-3 py-2 text-sm bg-paper"
          >
            <option value="" disabled>
              Selecione
            </option>
            {states.map((state) => (
              <option key={state.code} value={state.code}>
                {state.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="block text-gray-500 mb-1">Estado B</span>
          <select
            name="uf_b"
            defaultValue={uf_b ?? ""}
            className="border border-ink px-3 py-2 text-sm bg-paper"
          >
            <option value="" disabled>
              Selecione
            </option>
            {states.map((state) => (
              <option key={state.code} value={state.code}>
                {state.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="bg-yellow text-ink text-sm font-semibold px-4 py-2">
          Comparar
        </button>
      </form>
    );

    if (uf_a && uf_b) {
      const [resultA, resultB] = await Promise.all([getStateDetail(uf_a), getStateDetail(uf_b)]);
      isDemo = isDemo || resultA.isDemo || resultB.isDemo;
      if (resultA.detail && resultB.detail) {
        table = <CompareEstadosTable a={resultA.detail} b={resultB.detail} />;
      } else {
        table = <p className="text-gray-500">Estado não encontrado.</p>;
      }
    }
  }

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Comparar</h1>
        <p className="mt-3 text-lg text-gray-500">
          Compare estados ou períodos, indicador por indicador.
        </p>
        <p className="mt-4 text-sm text-gray-500 max-w-2xl">
          O IFB nunca calcula um vencedor geral: cada indicador é mostrado separadamente, para que
          a comparação não esconda diferenças entre áreas.
        </p>
      </section>

      <nav className="border-t border-b border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 flex gap-6 text-sm font-medium">
          <Link
            href="/comparar?modo=estados"
            className={`py-3 border-b-2 ${modo === "estados" ? "border-yellow" : "border-transparent text-gray-500"}`}
          >
            Estado × Estado
          </Link>
          <Link
            href="/comparar?modo=periodos"
            className={`py-3 border-b-2 ${modo === "periodos" ? "border-yellow" : "border-transparent text-gray-500"}`}
          >
            Período × Período
          </Link>
        </div>
      </nav>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
        {picker}
        <div className="mt-8">
          {table ?? (
            <p className="text-gray-500">
              Escolha {modo === "periodos" ? "dois períodos" : "dois estados"} para comparar.
            </p>
          )}
        </div>
      </section>
    </>
  );
}
