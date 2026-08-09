import { getAdminIndicators } from "@/lib/admin-api";
import SimpleMarkdown from "@/components/SimpleMarkdown";

export default async function AdminMetodologiasPage() {
  const indicators = await getAdminIndicators();

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Metodologias</h1>
      <p className="mt-2 text-sm text-gray-500">
        Versão vigente de cada indicador, incluindo os desabilitados. O texto vem do código-fonte
        do sync (<code>app/sync/definitions.py</code>) — para mudar, é preciso editar lá.
      </p>

      <div className="mt-6 space-y-8">
        {indicators.map((indicator) => (
          <section key={indicator.slug} className="bg-paper border border-gray-200 p-6">
            <h2 className="text-lg font-bold">
              {indicator.name}{" "}
              <span className="text-xs font-normal text-gray-500">
                (v{indicator.methodology_version ?? "—"}, {indicator.enabled ? "habilitado" : "desabilitado"})
              </span>
            </h2>
            {indicator.methodology ? (
              <div className="mt-3">
                <SimpleMarkdown content={indicator.methodology} />
              </div>
            ) : (
              <p className="mt-3 text-sm text-gray-500">Nenhuma metodologia registrada ainda.</p>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
