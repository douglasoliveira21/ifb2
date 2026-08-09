import { getAdminIndicators } from "@/lib/admin-api";
import { toggleIndicatorAction } from "@/app/admin/actions";

export default async function AdminIndicadoresPage() {
  const indicators = await getAdminIndicators();

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Indicadores</h1>
      <p className="mt-2 text-sm text-gray-500">
        Desabilitar um indicador o remove imediatamente de todas as páginas públicas — os dados
        continuam no banco, só deixam de ser exibidos.
      </p>

      <div className="mt-6 bg-paper border border-gray-200 divide-y divide-gray-200">
        {indicators.map((indicator) => (
          <div key={indicator.slug} className="px-4 py-3 flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-sm">{indicator.name}</p>
              <p className="text-xs text-gray-500">
                {indicator.slug} · {indicator.source_name}
              </p>
            </div>
            <form action={toggleIndicatorAction}>
              <input type="hidden" name="slug" value={indicator.slug} />
              <input type="hidden" name="enabled" value={(!indicator.enabled).toString()} />
              <button
                type="submit"
                className={`text-xs font-semibold px-3 py-1.5 border ${
                  indicator.enabled
                    ? "border-ink text-ink hover:bg-gray-100"
                    : "border-gray-300 text-gray-400 hover:bg-gray-100"
                }`}
              >
                {indicator.enabled ? "Habilitado — desabilitar" : "Desabilitado — habilitar"}
              </button>
            </form>
          </div>
        ))}
      </div>
    </div>
  );
}
