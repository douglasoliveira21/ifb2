import Link from "next/link";
import type { Metadata } from "next";
import { getGovernmentPeriods, getStates } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Ficha por Governante — Instituto Fiscaliza Brasil",
  description: "Indicadores no início e no fim de cada mandato, federal e estadual.",
};

export default async function GovernoPage({
  searchParams,
}: {
  searchParams: Promise<{ uf?: string }>;
}) {
  const { uf } = await searchParams;
  const [federalPeriods, { states }] = await Promise.all([getGovernmentPeriods("BR"), getStates()]);
  const statePeriods = uf ? await getGovernmentPeriods(uf) : [];

  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Ficha por Governante</h1>
        <p className="mt-3 text-lg text-gray-500">
          O que os indicadores mostravam no início e no fim de cada mandato.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-8">
          <h2 className="text-xl font-bold mb-4">Presidentes</h2>
          <ul className="divide-y divide-gray-100">
            {federalPeriods.map((period) => (
              <li key={period.id} className="py-3">
                <Link href={`/governo/br/${period.id}`} className="hover:underline underline-offset-2">
                  <span className="font-medium">{period.holder_name}</span>{" "}
                  <span className="text-gray-500 text-sm">
                    ({formatDate(period.start_date)} –{" "}
                    {period.end_date ? formatDate(period.end_date) : "atual"})
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-8">
          <h2 className="text-xl font-bold mb-4">Governadores</h2>
          <form method="get" className="flex flex-wrap items-end gap-4">
            <label className="text-sm">
              <span className="block text-gray-500 mb-1">Estado</span>
              <select
                name="uf"
                defaultValue={uf ?? ""}
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
              Ver
            </button>
          </form>

          <div className="mt-6">
            {!uf && <p className="text-gray-500 text-sm">Escolha um estado para ver seus governadores.</p>}
            {uf && statePeriods.length === 0 && (
              <p className="text-gray-500 text-sm">
                Nenhum governador cadastrado ainda para este estado.
              </p>
            )}
            {statePeriods.length > 0 && (
              <ul className="divide-y divide-gray-100">
                {statePeriods.map((period) => (
                  <li key={period.id} className="py-3">
                    <Link
                      href={`/governo/${uf!.toLowerCase()}/${period.id}`}
                      className="hover:underline underline-offset-2"
                    >
                      <span className="font-medium">{period.holder_name}</span>{" "}
                      <span className="text-gray-500 text-sm">
                        ({formatDate(period.start_date)} –{" "}
                        {period.end_date ? formatDate(period.end_date) : "atual"})
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
