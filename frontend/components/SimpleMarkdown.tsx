/**
 * Renderizador mínimo para o texto de metodologia (conteúdo controlado,
 * gerado pelo próprio backend do IFB — não é HTML de usuário). Suporta
 * apenas `# título`, `## subtítulo` e parágrafos, o suficiente para o
 * texto que `app/sync/definitions.py` produz. Evita puxar uma lib de
 * markdown inteira para isso.
 */
export default function SimpleMarkdown({ content }: { content: string }) {
  const blocks = content.trim().split(/\n\s*\n/);

  return (
    <div className="prose-ifb space-y-4">
      {blocks.map((block, i) => {
        if (block.startsWith("## ")) {
          return (
            <h3 key={i} className="text-lg font-bold mt-6">
              {block.slice(3)}
            </h3>
          );
        }
        if (block.startsWith("# ")) {
          return (
            <h2 key={i} className="text-xl font-bold">
              {block.slice(2)}
            </h2>
          );
        }
        return (
          <p key={i} className="text-sm text-gray-500 leading-relaxed">
            {block}
          </p>
        );
      })}
    </div>
  );
}
