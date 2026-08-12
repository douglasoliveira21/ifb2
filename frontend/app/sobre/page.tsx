import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sobre — Instituto Fiscaliza Brasil",
  description:
    "O que é o Instituto Fiscaliza Brasil, por que ele existe e como transforma dados públicos oficiais em indicadores que qualquer pessoa consegue conferir.",
  alternates: { canonical: "/sobre" },
};

export default function SobrePage() {
  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Sobre o IFB</h1>
        <p className="mt-3 text-lg text-gray-500">
          Fiscalizamos resultados, não discursos.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 space-y-6">
          <div>
            <h2 className="text-xl font-bold">O que é o IFB</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              O Instituto Fiscaliza Brasil é um projeto independente que reúne indicadores públicos
              oficiais — desemprego, inflação, dívida pública, desmatamento, mortalidade infantil,
              IDEB, segurança pública, entre outros — em um único lugar, com fonte, série histórica
              e metodologia sempre visíveis. A ideia é simples: qualquer pessoa deveria conseguir
              conferir, em poucos segundos, se um número citado em campanha eleitoral ou em um
              discurso bate com o que os órgãos oficiais realmente publicaram.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Por que o IFB existe</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Dado público oficial já existe — IBGE, Banco Central, Tesouro Nacional, INPE, INEP e
              dezenas de outros órgãos publicam suas séries regularmente. O problema é que esse dado
              está espalhado, em formatos diferentes, com nomenclaturas diferentes, e sem uma forma
              simples de comparar &ldquo;o que era quando um mandato começou&rdquo; com &ldquo;o que é
              agora&rdquo;. O IFB existe para fechar essa distância: não produzimos dado novo, apenas
              organizamos o que já é público, sempre com a fonte original um clique de distância.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Princípios</h2>
            <ul className="mt-2 space-y-3 text-sm text-gray-500 leading-relaxed list-disc pl-5">
              <li>
                <strong className="text-ink">Sem viés partidário.</strong> O IFB nunca associa um
                indicador a uma cor de partido nem trata o titular de um cargo como protagonista de
                um gráfico — mostramos a evolução do número, não uma narrativa sobre quem governava.
              </li>
              <li>
                <strong className="text-ink">Sempre com fonte oficial.</strong> Todo valor exibido
                vem de uma API pública de um órgão oficial, nunca de estimativa própria ou de
                terceiros não oficiais.
              </li>
              <li>
                <strong className="text-ink">Erros são corrigidos publicamente.</strong> Quando um
                erro é identificado, a correção é registrada com motivo, valor anterior e valor novo
                — nunca em silêncio. Veja o histórico em{" "}
                <a href="/transparencia" className="underline underline-offset-2 hover:text-ink">
                  /transparencia
                </a>
                .
              </li>
              <li>
                <strong className="text-ink">Correlação não é causalidade.</strong> Mostrar a
                evolução de um indicador durante um período de governo não significa atribuir esse
                resultado automaticamente a quem governava — fatores externos e defasagens de
                política pública também importam. Mais em{" "}
                <a href="/metodologia" className="underline underline-offset-2 hover:text-ink">
                  /metodologia
                </a>
                .
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-xl font-bold">Quem mantém o IFB</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              O IFB é mantido de forma independente, sem patrocínio editorial e sem venda de acesso
              a nenhum indicador — todo o conteúdo é público e gratuito. Detalhes sobre como o
              projeto se sustenta financeiramente estão em{" "}
              <a href="/apoiar" className="underline underline-offset-2 hover:text-ink">
                /apoiar
              </a>
              . Para falar com a equipe do IFB, veja{" "}
              <a href="/contato" className="underline underline-offset-2 hover:text-ink">
                /contato
              </a>
              .
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
