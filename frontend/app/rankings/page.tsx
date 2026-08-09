import Link from "next/link";
import type { Metadata } from "next";
import { getRankings } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { rankingTitle } from "@/lib/ranking-title";
import DemoBanner from "@/components/DemoBanner";

export const metadata: Metadata = {
  title: "Rankings — Instituto Fiscaliza Brasil",
  description: "Rankings objetivos entre estados, indicador por indicador.",
};

export default async function RankingsPage() {
  const { rankings, isDemo } = await getRankings();

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Rankings</h1>
        <p className="mt-3 text-lg text-gray-500">
          Rankings objetivos entre estados, um indicador de cada vez.
        </p>
        <p className="mt-4 text-sm text-gray-500 max-w-2xl">
          Só entram aqui indicadores com dado disponível em pelo menos dois estados. Não existe
          ranking geral de &ldquo;melhor estado&rdquo; — cada ranking é sobre um único indicador.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          {rankings.length === 0 ? (
            <p className="text-gray-500">Dado ainda não disponível.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {rankings.map((ranking) => (
                <li key={ranking.slug}>
                  <Link
                    href={`/rankings/${ranking.slug}`}
                    className="py-4 flex items-center justify-between gap-4 group"
                  >
                    <span className="min-w-0 text-base font-medium group-hover:underline underline-offset-2">
                      {rankingTitle(ranking.indicator_name, ranking.polarity)}
                    </span>
                    <span className="text-xs text-gray-500 shrink-0 text-right">
                      {ranking.states_count} estados
                      {ranking.last_updated && <> · {formatDate(ranking.last_updated)}</>}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </>
  );
}
