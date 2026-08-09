import { getAdminCorrections, getAdminIndicators, getAdminIndicatorValues } from "@/lib/admin-api";
import { formatDate, formatNumber } from "@/lib/format";
import { createCorrectionAction } from "@/app/admin/actions";

type SearchParams = { slug?: string };

export default async function AdminCorrecoesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const { slug } = await searchParams;
  const [indicators, corrections] = await Promise.all([getAdminIndicators(), getAdminCorrections()]);
  const values = slug ? await getAdminIndicatorValues(slug) : [];
  const indicator = indicators.find((i) => i.slug === slug);

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Correções</h1>
      <p className="mt-2 text-sm text-gray-500 max-w-2xl">
        Toda correção manual fica registrada com motivo, valor anterior e valor novo — nunca
        sobrescreve um valor oficial em silêncio.
      </p>

      <form method="get" className="mt-6 flex flex-wrap items-end gap-4">
        <label className="text-sm">
          <span className="block text-gray-500 mb-1">Indicador</span>
          <select
            name="slug"
            defaultValue={slug ?? ""}
            className="border border-ink px-3 py-2 text-sm bg-paper min-w-[240px]"
          >
            <option value="" disabled>
              Selecione
            </option>
            {indicators.map((i) => (
              <option key={i.slug} value={i.slug}>
                {i.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="bg-yellow text-ink text-sm font-semibold px-4 py-2">
          Carregar valores
        </button>
      </form>

      {indicator && (
        <section className="mt-8">
          <h2 className="text-lg font-bold">{indicator.name}</h2>
          {values.length === 0 ? (
            <p className="mt-2 text-sm text-gray-500">Nenhum valor encontrado para este indicador.</p>
          ) : (
            <form action={createCorrectionAction} className="mt-4 space-y-4">
              <input type="hidden" name="slug" value={slug} />
              <label className="block text-sm">
                <span className="block text-gray-500 mb-1">Valor a corrigir</span>
                <select
                  name="indicator_value_id"
                  required
                  className="border border-ink px-3 py-2 text-sm bg-paper w-full sm:w-auto sm:min-w-[360px]"
                >
                  {values.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.location_code} · {formatDate(v.reference_date)} · valor atual: {formatNumber(v.value, indicator.unit)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm max-w-xs">
                <span className="block text-gray-500 mb-1">Novo valor</span>
                <input
                  type="number"
                  step="any"
                  name="new_value"
                  required
                  className="border border-ink px-3 py-2 text-sm bg-paper w-full"
                />
              </label>
              <label className="block text-sm max-w-xl">
                <span className="block text-gray-500 mb-1">Motivo da correção (obrigatório)</span>
                <textarea
                  name="reason"
                  required
                  rows={3}
                  className="border border-ink px-3 py-2 text-sm bg-paper w-full"
                />
              </label>
              <button type="submit" className="bg-yellow text-ink text-sm font-semibold px-4 py-2">
                Registrar correção
              </button>
            </form>
          )}
        </section>
      )}

      <section className="mt-10">
        <h2 className="text-lg font-bold">Correções registradas</h2>
        {corrections.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">Nenhuma correção manual registrada ainda.</p>
        ) : (
          <ul className="mt-2 divide-y divide-gray-200 bg-paper border border-gray-200">
            {corrections.map((c) => (
              <li key={c.id} className="px-4 py-3 text-sm">
                <p className="font-medium">
                  {c.indicator_slug} · {c.location_code} · {formatDate(c.reference_date)}
                </p>
                <p className="text-gray-500 mt-0.5">
                  {c.previous_value} → {c.new_value} — {c.reason}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {c.changed_by} em {formatDate(c.changed_at.slice(0, 10))}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
