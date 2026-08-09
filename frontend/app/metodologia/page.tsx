import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Metodologia — Instituto Fiscaliza Brasil",
  description: "Como o IFB coleta, calcula e compara os indicadores públicos.",
};

export default function MetodologiaPage() {
  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Metodologia</h1>
        <p className="mt-3 text-lg text-gray-500">
          Como coletamos, calculamos e comparamos os indicadores.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 space-y-10">
          <div>
            <h2 className="text-xl font-bold">Como os dados são coletados</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Cada indicador vem de uma API pública oficial (Banco Central, IBGE, INPE, e
              gradualmente outras). Um conector específico busca a série completa, e o IFB nunca
              adiciona, arredonda ou preenche um valor que a fonte não publicou. Se a fonte não
              responde, a última atualização disponível continua sendo exibida, com a data clara —
              nunca um valor inventado no lugar.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Como períodos são comparados</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Ao comparar um período (ano, período de governo, ou intervalo personalizado), o IFB
              usa o valor disponível mais próximo do início e do fim do período. Isso significa
              que, se um indicador só é publicado trimestralmente, a comparação usa o trimestre
              mais próximo daquelas datas — não um valor interpolado.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Percentual vs. pontos percentuais</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Quando um indicador passa de 8% para 6%, o IFB descreve isso como uma queda de{" "}
              <strong>2 pontos percentuais</strong> — não &ldquo;queda de 2%&rdquo;, que seria uma
              queda relativa de 25%. Essa distinção é mantida em todas as páginas de indicador.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Como &ldquo;melhorou&rdquo;/&ldquo;piorou&rdquo; é determinado</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Cada indicador tem uma polaridade definida (quanto maior é melhor, quanto menor é
              melhor, ou neutro). A classificação compara o primeiro e o último valor disponíveis
              no período selecionado segundo essa polaridade. Indicadores neutros (como a Selic)
              nunca recebem rótulo de melhora ou piora — são um instrumento de política, não um
              resultado a ser julgado isoladamente. Quando não há dado suficiente, o indicador
              aparece como &ldquo;sem dados atualizados&rdquo;, nunca como neutro por omissão.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Correlação não é causalidade</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Os indicadores apresentam a evolução observada durante um determinado período —
              inclusive períodos de governo. Isso não significa que todas as alterações tenham
              sido causadas diretamente pelo governante ou por suas políticas. Fatores externos,
              defasagens de política pública e tendências de longo prazo também afetam os números.
              O IFB nunca atribui automaticamente um resultado a uma pessoa ou governo.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Revisões de série histórica</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Fontes oficiais às vezes revisam valores já publicados (ex: uma estimativa do PIB
              trimestral revisada meses depois). Quando isso acontece, o IFB registra a mudança em
              vez de sobrescrever o valor em silêncio — o histórico da revisão fica disponível na{" "}
              <a href="/transparencia" className="underline underline-offset-2 hover:text-ink">
                página de transparência
              </a>
              .
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Como as fontes são escolhidas</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Priorizamos a fonte oficial primária de cada indicador (o órgão que efetivamente
              produz o dado). Quando essa fonte não tem uma API simples e confiável, o IFB pode
              usar um espelho oficial — por exemplo, várias séries do IBGE são replicadas
              oficialmente pelo Banco Central em sua API pública (SGS), e são usadas como tal,
              sempre com a atribuição de fonte correta.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Correção de erros</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Correções manuais só acontecem quando um erro é identificado (ex: um valor mal
              importado). Toda correção manual fica registrada com motivo, valor anterior e valor
              novo — nunca é feita silenciosamente. O histórico completo está na{" "}
              <a href="/transparencia" className="underline underline-offset-2 hover:text-ink">
                página de transparência
              </a>
              .
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
