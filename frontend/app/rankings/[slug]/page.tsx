import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getRankingDetail } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import { rankingTitle } from "@/lib/ranking-title";
import ClassificationBadge from "@/components/ClassificationBadge";
import DemoBanner from "@/components/DemoBanner";

type Params = { slug: string };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { slug } = await params;
  const { detail } = await getRankingDetail(slug);
  if (!detail) return { title: "Ranking não encontrado — Instituto Fiscaliza Brasil" };
  return { title: `${rankingTitle(detail.indicator_name, detail.polarity)} — Instituto Fiscaliza Brasil` };
}

export default async function RankingPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const { detail, isDemo } = await getRankingDetail(slug);

  if (!detail) notFound();

  const periods = detail.entries.map((e) => `${e.first_date}_${e.last_date}`);
  const samePeriodForAll = new Set(periods).size === 1;
  const first = detail.entries[0];

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16">
        <Link href="/rankings" className="text-sm text-gray-500 hover:text-ink underline underline-offset-2">
          ← Todos os rankings
        </Link>
        <h1 className="mt-4 text-3xl sm:text-5xl font-extrabold tracking-tight">
          {rankingTitle(detail.indicator_name, detail.polarity)}
        </h1>
        {samePeriodForAll && first && (
          <p className="mt-3 text-sm text-gray-500">
            Período: {formatDate(first.first_date)} a {formatDate(first.last_date)}.{" "}
            {detail.entries.length} estado{detail.entries.length > 1 ? "s" : ""} com dado disponível.
          </p>
        )}
      </section>

      <section className="border-t border-ink mt-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[560px]">
              <thead>
                <tr className="border-b border-ink text-left text-xs uppercase tracking-wide text-gray-500">
                  <th className="py-2 pr-4">#</th>
                  <th className="py-2 pr-4">Estado</th>
                  <th className="py-2 pr-4">Início</th>
                  <th className="py-2 pr-4">Fim</th>
                  <th className="py-2 pr-4">Variação</th>
                  <th className="py-2">Classificação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {detail.entries.map((entry) => (
                  <tr key={entry.state_code}>
                    <td className="py-3 pr-4 stat-figure font-bold">{entry.rank}</td>
                    <td className="py-3 pr-4 font-medium">
                      <Link
                        href={`/estados/${entry.state_code.toLowerCase()}`}
                        className="hover:underline underline-offset-2"
                      >
                        {entry.state_name}
                      </Link>
                    </td>
                    <td className="py-3 pr-4 stat-figure">{formatNumber(entry.first_value, detail.unit)}</td>
                    <td className="py-3 pr-4 stat-figure">{formatNumber(entry.last_value, detail.unit)}</td>
                    <td className="py-3 pr-4 stat-figure">
                      {entry.change_absolute > 0 ? "+" : ""}
                      {formatNumber(entry.change_absolute, detail.unit)}
                    </td>
                    <td className="py-3">
                      <ClassificationBadge classification={entry.classification} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-6 text-xs text-gray-500 max-w-2xl">
            Ranking baseado no período com dado disponível para cada estado — nem todos começam ou
            terminam exatamente na mesma data. Consulte a{" "}
            <Link href="/metodologia" className="underline underline-offset-2 hover:text-ink">
              metodologia
            </Link>{" "}
            para saber como o indicador é calculado.
          </p>
        </div>
      </section>
    </>
  );
}
