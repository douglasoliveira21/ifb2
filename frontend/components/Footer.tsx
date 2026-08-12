import Link from "next/link";

const COLUMNS: { title: string; links: { href: string; label: string }[] }[] = [
  {
    title: "Institucional",
    links: [
      { href: "/sobre", label: "Sobre" },
      { href: "/metodologia", label: "Metodologia" },
      { href: "/fontes", label: "Fontes" },
      { href: "/transparencia", label: "Transparência" },
    ],
  },
  {
    title: "Explorar",
    links: [
      { href: "/indicadores", label: "Indicadores" },
      { href: "/estados", label: "Estados" },
      { href: "/governo", label: "Governo" },
      { href: "/rankings", label: "Rankings" },
      { href: "/frases-verificadas", label: "Frases Verificadas" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/politica-editorial", label: "Política editorial" },
      { href: "/privacidade", label: "Privacidade" },
      { href: "/contato", label: "Contato" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-ink mt-16">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 grid grid-cols-2 sm:grid-cols-4 gap-8">
        <div className="col-span-2 sm:col-span-1">
          <Link href="/" className="flex items-center gap-2">
            <span
              aria-hidden
              className="inline-flex h-8 w-8 items-center justify-center bg-ink text-yellow font-bold text-sm"
            >
              IFB
            </span>
          </Link>
          <p className="mt-3 text-xs text-gray-500 leading-relaxed">
            Fiscalizamos resultados, não discursos.
          </p>
          <Link
            href="/apoiar"
            className="mt-4 inline-block bg-yellow text-ink text-xs font-semibold px-3 py-2 hover:brightness-95 transition"
          >
            Apoiar o IFB
          </Link>
        </div>

        {COLUMNS.map((column) => (
          <div key={column.title}>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
              {column.title}
            </p>
            <ul className="mt-3 space-y-2">
              {column.links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-gray-500 hover:text-ink transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-ink">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-4 text-xs text-gray-500">
          Instituto Fiscaliza Brasil — dados públicos, fonte sempre visível.
        </div>
      </div>
    </footer>
  );
}
