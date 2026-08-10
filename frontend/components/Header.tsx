import Link from "next/link";
import MobileNav from "@/components/MobileNav";

const NAV_LINKS = [
  { href: "/brasil/linha-do-tempo", label: "Brasil" },
  { href: "/estados", label: "Estados" },
  { href: "/governo", label: "Governo" },
  { href: "/comparar", label: "Comparar" },
  { href: "/indicadores", label: "Indicadores" },
  { href: "/metodologia", label: "Metodologia" },
];

export default function Header() {
  return (
    <header className="border-b border-ink bg-paper sticky top-0 z-40">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 h-16 flex items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span
            aria-hidden
            className="inline-flex h-8 w-8 items-center justify-center bg-ink text-yellow font-bold text-sm"
          >
            IFB
          </span>
          <span className="leading-none text-[11px] font-semibold tracking-wide uppercase">
            Instituto
            <br />
            Fiscaliza Brasil
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="hover:text-ink text-gray-500 transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-4">
          <Link
            href="/apoiar"
            className="bg-yellow text-ink text-sm font-semibold px-4 py-2 hover:brightness-95 transition"
          >
            Apoiar o IFB
          </Link>
        </div>

        <MobileNav links={NAV_LINKS} />
      </div>
    </header>
  );
}
