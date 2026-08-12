import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacidade — Instituto Fiscaliza Brasil",
  description: "Como o IFB trata dados pessoais de quem visita o site.",
  alternates: { canonical: "/privacidade" },
};

export default function PrivacidadePage() {
  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Privacidade</h1>
        <p className="mt-3 text-lg text-gray-500">
          Como o IFB trata dados pessoais de quem visita o site.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 space-y-6">
          <div>
            <h2 className="text-xl font-bold">Não exigimos cadastro</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Todo o conteúdo do IFB — indicadores, comparações, rankings, frases verificadas — é
              acessível sem criar conta, sem login e sem fornecer nenhum dado pessoal.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Não usamos cookies de rastreamento nem publicidade</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              O IFB não exibe anúncios e não usa cookies de rastreamento, pixels de redes sociais ou
              ferramentas de publicidade de terceiros. O site pode registrar métricas técnicas
              básicas e agregadas de acesso (como volume de visitas), sem identificar
              individualmente quem visitou.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Dados que você nos envia por conta própria</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Se você entrar em contato por e-mail (veja{" "}
              <a href="/contato" className="underline underline-offset-2 hover:text-ink">
                /contato
              </a>
              ), usamos as informações fornecidas apenas para responder à sua mensagem — nunca para
              fins comerciais, publicidade ou repasse a terceiros.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Doações via Pix</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              O IFB não processa nem armazena dados de pagamento — doações via Pix (
              <a href="/apoiar" className="underline underline-offset-2 hover:text-ink">
                /apoiar
              </a>
              ) são feitas diretamente pelo aplicativo do seu banco, fora do site do IFB.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-bold">Alterações a esta política</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              Se esta política mudar de forma relevante, a data de atualização abaixo será revisada.
              Última atualização: agosto de 2026.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
