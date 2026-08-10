import Link from "next/link";
import type { Metadata } from "next";
import { getMunicipios, getStates } from "@/lib/api";

type Params = { uf: string };
type SearchParams = { q?: string };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { uf } = await params;
  return { title: `Municípios de ${uf.toUpperCase()} — Instituto Fiscaliza Brasil` };
}

export default async function MunicipiosPage({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}) {
  const { uf } = await params;
  const { q } = await searchParams;
  const [municipios, { states }] = await Promise.all([getMunicipios(uf), getStates()]);
  const stateName = states.find((s) => s.code === uf.toUpperCase())?.name ?? uf.toUpperCase();

  const filtered = q
    ? municipios.filter((m) => m.name.toLowerCase().includes(q.toLowerCase()))
    : municipios;

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <Link
          href={`/estados/${uf.toLowerCase()}`}
          className="text-sm text-gray-500 hover:text-ink underline underline-offset-2"
        >
          ← {stateName}
        </Link>
        <h1 className="mt-4 text-3xl sm:text-5xl font-extrabold tracking-tight">
          Municípios — {stateName}
        </h1>
        <p className="mt-3 text-lg text-gray-500">
          Indicadores municipais piloto: transferências constitucionais recebidas e despesa com
          pessoal, ano mais recente disponível.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
          <form method="get" className="max-w-sm">
            <label className="text-sm">
              <span className="block text-gray-500 mb-1">Buscar município</span>
              <input
                type="text"
                name="q"
                defaultValue={q ?? ""}
                placeholder="Nome do município"
                className="border border-ink px-3 py-2 text-sm bg-paper w-full"
              />
            </label>
          </form>

          {municipios.length === 0 ? (
            <p className="mt-8 text-gray-500">
              Nenhum indicador municipal disponível ainda para {stateName}.
            </p>
          ) : filtered.length === 0 ? (
            <p className="mt-8 text-gray-500">Nenhum município encontrado para &ldquo;{q}&rdquo;.</p>
          ) : (
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8">
              {filtered.map((municipio) => (
                <Link
                  key={municipio.code}
                  href={`/municipios/${uf.toLowerCase()}/${municipio.code}`}
                  className="py-3 border-b border-gray-100 flex items-center justify-between gap-4 group"
                >
                  <p className="text-sm font-medium min-w-0 group-hover:underline underline-offset-2">
                    {municipio.name}
                  </p>
                  <p className="text-xs text-gray-500 shrink-0">
                    {municipio.indicators_available} indicador
                    {municipio.indicators_available > 1 ? "es" : ""}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
