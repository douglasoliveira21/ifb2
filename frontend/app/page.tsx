import { getHomeData } from "@/lib/api";
import { formatDate } from "@/lib/format";
import DemoBanner from "@/components/DemoBanner";
import PlacarBrasil from "@/components/PlacarBrasil";
import Brasil60Segundos from "@/components/Brasil60Segundos";
import OQueMudou from "@/components/OQueMudou";

export default async function Home() {
  const { indicators, updatedAt, isDemo } = await getHomeData();

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16">
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight">Placar Brasil</h1>
        <p className="mt-3 text-lg sm:text-xl text-gray-500">O Brasil pelos números.</p>
        <p className="mt-4 text-sm text-gray-500">
          {updatedAt ? `Atualizado em ${formatDate(updatedAt)}.` : "Dado ainda não disponível."}
          {" "}Fonte consolidada de bases oficiais.
        </p>
      </section>

      {indicators.length > 0 ? (
        <>
          <PlacarBrasil indicators={indicators} />
          <Brasil60Segundos indicators={indicators} />
          <OQueMudou indicators={indicators} />
        </>
      ) : (
        <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16 border-t border-ink">
          <p className="text-gray-500">Dado ainda não disponível.</p>
        </section>
      )}

      <section className="border-t border-ink bg-ink text-paper">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 text-center">
          <p className="text-lg font-semibold">Fiscalizamos resultados, não discursos.</p>
        </div>
      </section>
    </>
  );
}
