import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contato — Instituto Fiscaliza Brasil",
  description: "Como reportar um erro, sugerir um indicador ou entrar em contato com o IFB.",
  alternates: { canonical: "/contato" },
};

const CONTACT_EMAIL = "douglassouza62@gmail.com";

export default function ContatoPage() {
  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Contato</h1>
        <p className="mt-3 text-lg text-gray-500">
          Encontrou um erro, quer sugerir um indicador ou tem uma dúvida? Fale com a gente.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 space-y-6">
          <div>
            <h2 className="text-xl font-bold">E-mail</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="stat-figure text-lg font-medium underline underline-offset-2 hover:text-ink"
              >
                {CONTACT_EMAIL}
              </a>
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Reportar um erro em um indicador</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Inclua o nome do indicador, a localização (Brasil, estado ou município) e, se possível,
              um link para a fonte oficial que mostra o valor correto. Toda correção confirmada é
              publicada em{" "}
              <a href="/transparencia" className="underline underline-offset-2 hover:text-ink">
                /transparencia
              </a>
              , com o motivo e o que mudou.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Sugerir um indicador ou fonte</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Se você conhece uma fonte oficial pública com série histórica sobre um tema ainda não
              coberto pelo IFB, mande o link — o critério de inclusão está em{" "}
              <a href="/politica-editorial" className="underline underline-offset-2 hover:text-ink">
                /politica-editorial
              </a>
              .
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
