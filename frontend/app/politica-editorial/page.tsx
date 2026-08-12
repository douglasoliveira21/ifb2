import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política editorial — Instituto Fiscaliza Brasil",
  description:
    "Os critérios que o IFB segue para escolher indicadores, verificar frases de campanha e corrigir erros, sem viés partidário.",
  alternates: { canonical: "/politica-editorial" },
};

export default function PoliticaEditorialPage() {
  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Política editorial</h1>
        <p className="mt-3 text-lg text-gray-500">
          Os critérios que seguimos ao escolher o que publicar e como publicar.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 space-y-6">
          <div>
            <h2 className="text-xl font-bold">Como escolhemos indicadores</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Um indicador só entra no IFB se existir uma fonte oficial primária, pública e com
              série histórica auditável (uma API, um portal de dados abertos ou um arquivo público
              regularmente atualizado). Não publicamos estimativas próprias nem projeções — só o
              que o órgão responsável já publicou. Isso significa que alguns temas relevantes ainda
              não aparecem no IFB simplesmente porque a fonte correspondente não disponibiliza os
              dados de forma processável (o detalhe de cada fonte está em{" "}
              <a href="/fontes" className="underline underline-offset-2 hover:text-ink">
                /fontes
              </a>
              ).
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Como funcionam as Frases Verificadas</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Cada frase verificada compara uma citação pública (discurso, entrevista, post) com o
              dado oficial correspondente, sempre com a fonte da citação e a fonte do dado lado a
              lado. O veredito (confirmado, parcialmente confirmado, distorcido, falso ou
              inconclusivo) é sobre a precisão factual da frase em relação ao número — nunca sobre a
              opinião ou a intenção de quem falou. Frases de qualquer espectro político podem ser
              verificadas; a seleção não segue partido, cargo ou popularidade de quem falou.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Neutralidade de apresentação</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Nenhuma página do IFB usa cor de partido, foto de candidato como destaque ou linguagem
              que sugira aprovação ou reprovação de uma gestão. A classificação de &ldquo;melhorou&rdquo;
              ou &ldquo;piorou&rdquo; de um indicador segue uma regra fixa e pública (definida em{" "}
              <a href="/metodologia" className="underline underline-offset-2 hover:text-ink">
                /metodologia
              </a>
              ), aplicada da mesma forma a qualquer período ou governante.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Correções</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Qualquer erro identificado — em um valor, em uma frase verificada ou em um texto — é
              corrigido publicamente, com data, motivo e o que mudou registrados em{" "}
              <a href="/transparencia" className="underline underline-offset-2 hover:text-ink">
                /transparencia
              </a>
              . Se você identificar um erro, veja como reportar em{" "}
              <a href="/contato" className="underline underline-offset-2 hover:text-ink">
                /contato
              </a>
              .
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Independência editorial</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              O apoio financeiro ao IFB (detalhado em{" "}
              <a href="/apoiar" className="underline underline-offset-2 hover:text-ink">
                /apoiar
              </a>
              ) nunca influencia qual indicador é publicado, como um dado é classificado ou o
              veredito de uma frase verificada. Não existe publicidade nem patrocínio editorial no
              IFB.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
