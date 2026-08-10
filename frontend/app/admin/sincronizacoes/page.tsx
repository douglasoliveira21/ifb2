import { getAdminSyncRuns } from "@/lib/admin-api";
import { triggerSyncAction } from "@/app/admin/actions";

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export default async function AdminSincronizacoesPage() {
  const runs = await getAdminSyncRuns();

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-extrabold tracking-tight">Sincronizações</h1>
        <form action={triggerSyncAction}>
          <button type="submit" className="bg-yellow text-ink text-sm font-semibold px-4 py-2">
            Forçar sincronização agora
          </button>
        </form>
      </div>
      <p className="mt-2 text-sm text-gray-500">
        Dispara todos os conectores em segundo plano — com os indicadores municipais, a
        sincronização completa leva de 10 a 20 minutos. Cada fonte é isolada e grava seu próprio
        registro assim que termina, então atualize esta página periodicamente para acompanhar o
        progresso (não precisa esperar o fim para ver os primeiros resultados).
      </p>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-sm min-w-[640px] bg-paper border border-gray-200">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
              <th className="px-4 py-2">Fonte</th>
              <th className="px-4 py-2">Início</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Registros</th>
              <th className="px-4 py-2">Erro</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {runs.map((run) => (
              <tr key={run.id}>
                <td className="px-4 py-3 font-medium">{run.source_name}</td>
                <td className="px-4 py-3 text-gray-500">{formatDateTime(run.started_at)}</td>
                <td className="px-4 py-3">
                  <span
                    className={
                      run.status === "error"
                        ? "text-negative font-semibold"
                        : run.status === "partial"
                          ? "text-neutral font-semibold"
                          : "text-positive font-semibold"
                    }
                  >
                    {run.status}
                  </span>
                </td>
                <td className="px-4 py-3">{run.records_processed}</td>
                <td className="px-4 py-3 text-gray-500 max-w-xs truncate" title={run.error_message ?? ""}>
                  {run.error_message ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
