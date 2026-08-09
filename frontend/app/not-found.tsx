import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-2xl px-4 sm:px-6 py-24 text-center">
      <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Erro 404</p>
      <h1 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-tight">Página não encontrada</h1>
      <p className="mt-4 text-gray-500">
        O conteúdo que você procura não existe ou foi movido.
      </p>
      <Link
        href="/"
        className="mt-8 inline-block bg-yellow text-ink text-sm font-semibold px-5 py-2.5 hover:brightness-95 transition"
      >
        Voltar para a Home
      </Link>
    </section>
  );
}
