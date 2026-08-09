import type { Metadata } from "next";
import { getTransparency } from "@/lib/api";
import DemoBanner from "@/components/DemoBanner";

export const metadata: Metadata = {
  title: "Fontes — Instituto Fiscaliza Brasil",
  description: "Fontes oficiais usadas pelo IFB para cada indicador.",
};

export default async function FontesPage() {
  const { transparency, isDemo } = await getTransparency();

  return (
    <>
      {isDemo && <DemoBanner />}

      <section className="mx-auto max-w-3xl px-4 sm:px-6 pt-10 sm:pt-16 pb-6">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Fontes</h1>
        <p className="mt-3 text-lg text-gray-500">
          O IFB não produz dados — consolida e apresenta dados públicos já produzidos por
          instituições oficiais.
        </p>
      </section>

      <section className="border-t border-ink">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-10">
          {!transparency || transparency.sources.length === 0 ? (
            <p className="text-gray-500">Dado ainda não disponível.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {transparency.sources.map((source) => (
                <li key={source.name} className="py-4">
                  <p className="font-medium">{source.name}</p>
                  {source.description && (
                    <p className="text-sm text-gray-500 mt-1">{source.description}</p>
                  )}
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-gray-500 underline underline-offset-2 hover:text-ink mt-1 inline-block"
                  >
                    {source.url}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </>
  );
}
