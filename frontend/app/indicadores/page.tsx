import type { Metadata } from "next";
import { getHomeData } from "@/lib/api";
import DemoBanner from "@/components/DemoBanner";
import IndicadoresList from "@/components/IndicadoresList";

export const metadata: Metadata = {
  title: "Indicadores — Instituto Fiscaliza Brasil",
  description: "Todos os indicadores acompanhados pelo IFB, organizados por categoria.",
};

export default async function IndicadoresPage() {
  const { indicators, isDemo } = await getHomeData();

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Indicadores</h1>
        <p className="mt-3 text-lg text-gray-500">
          Todos os indicadores acompanhados pelo IFB, organizados por categoria.
        </p>
      </section>

      {indicators.length === 0 ? (
        <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16 border-t border-ink">
          <p className="text-gray-500">Dado ainda não disponível.</p>
        </section>
      ) : (
        <IndicadoresList indicators={indicators} />
      )}
    </>
  );
}
