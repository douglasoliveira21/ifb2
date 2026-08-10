import Link from "next/link";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Admin — Instituto Fiscaliza Brasil",
  robots: { index: false, follow: false },
};

// Nunca pré-renderizar em build: as páginas de admin exigem credenciais e
// dado sempre atual (sync status, correções), nunca fazem sentido como
// HTML estático gerado antes do deploy.
export const dynamic = "force-dynamic";

const ADMIN_LINKS = [
  { href: "/admin", label: "Painel" },
  { href: "/admin/indicadores", label: "Indicadores" },
  { href: "/admin/sincronizacoes", label: "Sincronizações" },
  { href: "/admin/correcoes", label: "Correções" },
  { href: "/admin/frases-verificadas", label: "Frases Verificadas" },
  { href: "/admin/metodologias", label: "Metodologias" },
  { href: "/admin/fontes", label: "Fontes" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="bg-gray-50 min-h-screen">
      <nav className="border-b border-ink bg-ink text-paper">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 flex flex-wrap gap-x-6 gap-y-2 text-sm py-3">
          {ADMIN_LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-yellow transition-colors">
              {link.label}
            </Link>
          ))}
          <Link href="/" className="ml-auto text-gray-400 hover:text-paper">
            ← Voltar ao site
          </Link>
        </div>
      </nav>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">{children}</div>
    </div>
  );
}
