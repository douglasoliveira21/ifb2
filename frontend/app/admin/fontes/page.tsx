import { getAdminSources } from "@/lib/admin-api";

export default async function AdminFontesPage() {
  const sources = await getAdminSources();

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Fontes</h1>
      <p className="mt-2 text-sm text-gray-500">
        Fontes registradas automaticamente pelo sync. Edição de metadados de fonte ainda não está
        disponível nesta versão do admin — hoje a fonte é definida no código
        (<code>app/sync/definitions.py</code>).
      </p>

      <div className="mt-6 bg-paper border border-gray-200 divide-y divide-gray-200">
        {sources.map((source) => (
          <div key={source.name} className="px-4 py-3">
            <p className="font-medium text-sm">{source.name}</p>
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-500 underline underline-offset-2 hover:text-ink"
            >
              {source.url}
            </a>
            {source.description && <p className="text-xs text-gray-500 mt-1">{source.description}</p>}
            <p className="text-xs text-gray-400 mt-1">{source.indicators_count} indicador(es)</p>
          </div>
        ))}
      </div>
    </div>
  );
}
