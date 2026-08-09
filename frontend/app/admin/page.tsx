import Link from "next/link";
import { getAdminIndicators, getAdminSyncRuns } from "@/lib/admin-api";
import { formatDate } from "@/lib/format";

export default async function AdminDashboard() {
  const [indicators, syncRuns] = await Promise.all([getAdminIndicators(), getAdminSyncRuns()]);

  const enabledCount = indicators.filter((i) => i.enabled).length;
  const lastErrors = syncRuns.filter((r) => r.status === "error").slice(0, 5);
  const lastRuns = syncRuns.slice(0, 5);

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Painel</h1>

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Stat label="Indicadores habilitados" value={`${enabledCount}/${indicators.length}`} />
        <Stat label="Sincronizações registradas" value={String(syncRuns.length)} />
        <Stat label="Erros recentes" value={String(lastErrors.length)} />
      </div>

      {lastErrors.length > 0 && (
        <section className="mt-8">
          <h2 className="text-lg font-bold text-negative">Erros recentes</h2>
          <ul className="mt-2 divide-y divide-gray-200 bg-paper border border-gray-200">
            {lastErrors.map((run) => (
              <li key={run.id} className="px-4 py-3 text-sm">
                <span className="font-medium">{run.source_name}</span> — {formatDate(run.started_at.slice(0, 10))}
                <p className="text-gray-500 mt-1">{run.error_message}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-lg font-bold">Últimas sincronizações</h2>
        <ul className="mt-2 divide-y divide-gray-200 bg-paper border border-gray-200">
          {lastRuns.map((run) => (
            <li key={run.id} className="px-4 py-3 text-sm flex justify-between">
              <span>{run.source_name}</span>
              <span className={run.status === "error" ? "text-negative" : "text-positive"}>{run.status}</span>
            </li>
          ))}
        </ul>
        <Link
          href="/admin/sincronizacoes"
          className="mt-2 inline-block text-sm underline underline-offset-2 hover:text-ink text-gray-500"
        >
          Ver todas
        </Link>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-paper border border-gray-200 p-4">
      <p className="stat-figure text-3xl font-bold">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  );
}
