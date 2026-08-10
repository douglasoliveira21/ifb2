import type { Metadata } from "next";
import QRCode from "qrcode";
import CopyPixKey from "@/components/CopyPixKey";

export const metadata: Metadata = {
  title: "Apoiar — Instituto Fiscaliza Brasil",
  description: "Como apoiar o IFB a continuar publicando indicadores públicos, verificáveis e sem viés.",
};

const PIX_KEY = "65212b5c-4fb8-48ad-a729-2664ab13d6bb";
const PIX_TITULAR = "Douglas Souza de Oliveira";
const PIX_CIDADE = "Contagem/MG";
// BR Code (EMV) gerado pelo banco — usado literalmente, sem recalcular
// nenhum campo, para não arriscar um checksum (CRC16) incorreto que
// invalidaria o QR em bancos mais rigorosos na validação.
const PIX_COPIA_E_COLA =
  "00020126580014BR.GOV.BCB.PIX013665212b5c-4fb8-48ad-a729-2664ab13d6bb5204000053039865802BR5925DOUGLAS SOUZA DE OLIVEIRA6008CONTAGEM62070503***6304329A";

const PLANS = [
  {
    name: "Apoiador IFB",
    monthly: "R$ 15,00",
    annual: "R$ 180,00",
    audience: "Para quem quer contribuir com o básico do dia a dia do projeto.",
  },
  {
    name: "Apoiador Cidadão",
    monthly: "R$ 30,00",
    annual: "R$ 360,00",
    audience: "Para quem usa o IFB com frequência e quer sustentar a atualização constante dos dados.",
  },
  {
    name: "Empresa/organização IFB",
    monthly: "R$ 150,00",
    annual: "R$ 1.800,00",
    audience: "Para empresas e organizações que quiserem apoiar institucionalmente o projeto.",
  },
];

export default async function ApoiarPage() {
  const qrSvg = await QRCode.toString(PIX_COPIA_E_COLA, {
    type: "svg",
    margin: 1,
    color: { dark: "#111111", light: "#ffffff" },
  });

  return (
    <>
      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Apoiar o IFB</h1>
        <p className="mt-3 text-lg text-gray-500">
          Fiscalizamos resultados, não discursos — e isso só se sustenta se o IFB não depender de
          quem está sendo fiscalizado.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10 space-y-6">
          <div>
            <h2 className="text-xl font-bold">Por que o apoio importa</h2>
            <p className="mt-2 text-sm text-gray-500 leading-relaxed">
              O IFB existe para que qualquer cidadão possa conferir, com fonte oficial e sem
              interpretação partidária, se um número citado em campanha eleitoral — desemprego,
              dívida pública, desmatamento, IDEB — bate com o que os órgãos oficiais realmente
              publicaram. Manter isso no ar tem custo: servidor, banco de dados e o tempo de
              acompanhar dezenas de fontes diferentes, cada uma com sua própria forma de mudar de
              endereço, quebrar ou exigir atualização.
            </p>
            <p className="mt-3 text-sm text-gray-500 leading-relaxed">
              O IFB não vende assinatura para acessar indicador nenhum — todo dado é público e
              gratuito para qualquer pessoa, sempre foi e sempre vai ser. Apoiar financeiramente é
              uma forma de manter isso assim, sem depender de publicidade, patrocínio editorial ou
              qualquer arranjo que crie incentivo para favorecer um lado.
            </p>
          </div>

          <div className="border-t border-gray-100 pt-6">
            <p className="text-sm text-gray-500 leading-relaxed">
              <strong className="text-ink">Apoiar não muda nenhum dado, classificação ou
              indicador</strong> — tudo é calculado da mesma forma para todo mundo, independente de
              quem apoia o projeto. A lista de fontes e a metodologia de cada indicador são públicas
              em{" "}
              <a href="/metodologia" className="underline underline-offset-2 hover:text-ink">
                /metodologia
              </a>{" "}
              e{" "}
              <a href="/transparencia" className="underline underline-offset-2 hover:text-ink">
                /transparencia
              </a>
              .
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10">
          <h2 className="text-xl font-bold">Doar via Pix</h2>
          <p className="mt-2 text-sm text-gray-500 leading-relaxed">
            Qualquer valor, avulso ou recorrente (você mesmo escolhe a frequência no app do seu
            banco). Titular {PIX_TITULAR}, {PIX_CIDADE}.
          </p>

          <div className="mt-6 grid grid-cols-1 sm:grid-cols-[auto_1fr] gap-6 sm:gap-8 items-start">
            <div
              className="w-40 h-40 border border-ink p-2 shrink-0 mx-auto sm:mx-0"
              // SVG gerado a partir do mesmo texto "copia e cola" abaixo — o
              // pacote `qrcode` só cuida da codificação/renderização, o
              // conteúdo em si já é o BR Code validado pelo banco.
              dangerouslySetInnerHTML={{ __html: qrSvg }}
            />

            <div className="space-y-6 w-full">
              <div className="border border-ink p-6">
                <CopyPixKey pixKey={PIX_KEY} label="Chave Pix (aleatória)" />
              </div>
              <div className="border border-ink p-6">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Pix Copia e Cola
                </p>
                <p className="mt-1 text-xs text-gray-500 break-all font-mono">{PIX_COPIA_E_COLA}</p>
                <div className="mt-3">
                  <CopyPixKey pixKey={PIX_COPIA_E_COLA} showValue={false} buttonLabel="Copiar Pix Copia e Cola" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10">
          <h2 className="text-xl font-bold">Planos de apoio recorrente</h2>
          <p className="mt-2 text-sm text-gray-500 leading-relaxed">
            Valores de referência para quem prefere se comprometer com um valor fixo — envie via
            Pix mensalmente, ou o valor anual de uma vez.
          </p>

          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm min-w-[520px]">
              <thead>
                <tr className="border-b border-ink text-left text-xs uppercase tracking-wide text-gray-500">
                  <th className="py-2 pr-4">Plano</th>
                  <th className="py-2 pr-4">Mensal</th>
                  <th className="py-2 pr-4">Anual</th>
                  <th className="py-2">Para quem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {PLANS.map((plan) => (
                  <tr key={plan.name}>
                    <td className="py-4 pr-4 font-medium align-top">{plan.name}</td>
                    <td className="py-4 pr-4 stat-figure font-bold align-top whitespace-nowrap">
                      {plan.monthly}
                    </td>
                    <td className="py-4 pr-4 stat-figure font-bold align-top whitespace-nowrap">
                      {plan.annual}
                    </td>
                    <td className="py-4 text-gray-500 align-top">{plan.audience}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-6 text-sm text-gray-500 leading-relaxed">
            Empresas e organizações que apoiarem institucionalmente podem ser listadas como
            financiadoras em{" "}
            <a href="/transparencia" className="underline underline-offset-2 hover:text-ink">
              /transparencia
            </a>{" "}
            — nunca como patrocinadoras editoriais.
          </p>
        </div>
      </section>
    </>
  );
}
