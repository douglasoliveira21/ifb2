import Link from "next/link";
import type { Metadata } from "next";
import { getStates } from "@/lib/api";
import { formatDate } from "@/lib/format";
import DemoBanner from "@/components/DemoBanner";

export const metadata: Metadata = {
  title: "Estados — Instituto Fiscaliza Brasil",
  description: "Placar dos 27 estados brasileiros, indicador por indicador.",
};

export default async function EstadosPage() {
  const { states, isDemo } = await getStates();

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Estados</h1>
        <p className="mt-3 text-lg text-gray-500">
          O placar de cada estado brasileiro, indicador por indicador.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8">
            {states.map((state) => (
              <Link
                key={state.code}
                href={`/estados/${state.code.toLowerCase()}`}
                className="py-4 border-b border-gray-100 flex items-center justify-between gap-4 group"
              >
                <div className="min-w-0">
                  <p className="text-base font-medium group-hover:underline underline-offset-2">
                    {state.name}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {state.indicators_available > 0
                      ? `${state.indicators_available} indicador${state.indicators_available > 1 ? "es" : ""} disponíve${state.indicators_available > 1 ? "is" : "l"}`
                      : "Nenhum indicador disponível ainda"}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="stat-figure text-lg font-bold">{state.code}</p>
                  {state.indicators_available > 0 && (
                    <p className="text-xs text-gray-500">
                      <span className="text-positive">{state.melhoraram} ▲</span>
                      {"  "}
                      <span className="text-negative">{state.pioraram} ▼</span>
                    </p>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {states.length > 0 && (
            <p className="mt-8 text-xs text-gray-500">
              Nem todo indicador nacional tem série por estado — quando não houver dado estadual
              disponível, a página do estado mostra isso explicitamente. Última atualização:{" "}
              {(() => {
                const last = states.map((s) => s.last_updated).filter(Boolean).sort().at(-1);
                return last ? formatDate(last) : "sem dados ainda";
              })()}
              .
            </p>
          )}
        </div>
      </section>
    </>
  );
}
