import { getAdminIndicators, getAdminVerifiedClaims } from "@/lib/admin-api";
import { formatDate } from "@/lib/format";
import { createVerifiedClaimAction, updateVerifiedClaimAction } from "@/app/admin/actions";

const VERDICT_LABELS: Record<string, string> = {
  CONFIRMADO: "Confirmado",
  PARCIALMENTE_CONFIRMADO: "Parcialmente confirmado",
  DISTORCIDO: "Distorcido",
  FALSO: "Falso",
  INCONCLUSIVO: "Inconclusivo",
};

type SearchParams = { edit?: string };

export default async function AdminFrasesVerificadasPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const { edit } = await searchParams;
  const [indicators, claims] = await Promise.all([getAdminIndicators(), getAdminVerifiedClaims()]);
  const editing = edit ? claims.find((c) => c.id === edit) : undefined;
  const action = editing ? updateVerifiedClaimAction : createVerifiedClaimAction;

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Frases Verificadas</h1>
      <p className="mt-2 text-sm text-gray-500 max-w-2xl">
        Cite exatamente o que a pessoa disse, com fonte verificável (vídeo, transcrição, matéria).
        A explicação deve remeter ao indicador real usado para checar a frase.
      </p>

      <form action={action} className="mt-6 space-y-4 max-w-2xl border border-ink p-6">
        <h2 className="text-lg font-bold">{editing ? "Editar frase" : "Nova frase"}</h2>
        {editing && <input type="hidden" name="id" value={editing.id} />}

        <label className="block text-sm">
          <span className="block text-gray-500 mb-1">Citação (obrigatório)</span>
          <textarea
            name="quote"
            required
            rows={3}
            defaultValue={editing?.quote}
            className="border border-ink px-3 py-2 text-sm bg-paper w-full"
          />
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="block text-sm">
            <span className="block text-gray-500 mb-1">Quem disse (obrigatório)</span>
            <input
              type="text"
              name="speaker_name"
              required
              defaultValue={editing?.speaker_name}
              className="border border-ink px-3 py-2 text-sm bg-paper w-full"
            />
          </label>
          <label className="block text-sm">
            <span className="block text-gray-500 mb-1">Cargo/função (opcional)</span>
            <input
              type="text"
              name="speaker_role"
              defaultValue={editing?.speaker_role ?? ""}
              className="border border-ink px-3 py-2 text-sm bg-paper w-full"
            />
          </label>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="block text-sm">
            <span className="block text-gray-500 mb-1">Data da fala (opcional)</span>
            <input
              type="date"
              name="claim_date"
              defaultValue={editing?.claim_date ?? ""}
              className="border border-ink px-3 py-2 text-sm bg-paper w-full"
            />
          </label>
          <label className="block text-sm">
            <span className="block text-gray-500 mb-1">Link da fonte (opcional)</span>
            <input
              type="url"
              name="source_url"
              defaultValue={editing?.source_url ?? ""}
              className="border border-ink px-3 py-2 text-sm bg-paper w-full"
            />
          </label>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="block text-sm">
            <span className="block text-gray-500 mb-1">Indicador relacionado (opcional)</span>
            <select
              name="indicator_slug"
              defaultValue={editing?.indicator_slug ?? ""}
              className="border border-ink px-3 py-2 text-sm bg-paper w-full"
            >
              <option value="">Nenhum</option>
              {indicators.map((i) => (
                <option key={i.slug} value={i.slug}>
                  {i.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="block text-gray-500 mb-1">Veredito (obrigatório)</span>
            <select
              name="verdict"
              required
              defaultValue={editing?.verdict ?? ""}
              className="border border-ink px-3 py-2 text-sm bg-paper w-full"
            >
              <option value="" disabled>
                Selecione
              </option>
              {Object.entries(VERDICT_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block text-sm">
          <span className="block text-gray-500 mb-1">
            Explicação (obrigatório — cite o indicador/número que embasa o veredito)
          </span>
          <textarea
            name="explanation"
            required
            rows={4}
            defaultValue={editing?.explanation}
            className="border border-ink px-3 py-2 text-sm bg-paper w-full"
          />
        </label>

        <button type="submit" className="bg-yellow text-ink text-sm font-semibold px-4 py-2">
          {editing ? "Salvar alterações" : "Publicar frase"}
        </button>
      </form>

      <section className="mt-10">
        <h2 className="text-lg font-bold">Frases publicadas</h2>
        {claims.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">Nenhuma frase verificada publicada ainda.</p>
        ) : (
          <ul className="mt-2 divide-y divide-gray-200 bg-paper border border-gray-200">
            {claims.map((c) => (
              <li key={c.id} className="px-4 py-3 text-sm flex items-start justify-between gap-4">
                <div>
                  <p className="font-medium">&ldquo;{c.quote}&rdquo;</p>
                  <p className="text-gray-500 mt-0.5">
                    {c.speaker_name}
                    {c.speaker_role ? ` (${c.speaker_role})` : ""}
                    {c.claim_date ? ` · ${formatDate(c.claim_date)}` : ""} —{" "}
                    {VERDICT_LABELS[c.verdict] ?? c.verdict}
                  </p>
                </div>
                <a
                  href={`/admin/frases-verificadas?edit=${c.id}`}
                  className="shrink-0 text-xs underline underline-offset-2 hover:text-ink text-gray-500"
                >
                  Editar
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
