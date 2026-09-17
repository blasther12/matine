import Link from "next/link";

import { buttonClassName } from "@/components/ui/button";

export default function MovieNotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-6 text-center">
      <div>
        <p className="font-mono text-xs tracking-widest text-amber-200 uppercase">404</p>
        <h1 className="mt-4 font-serif text-5xl text-white">Filme não encontrado.</h1>
        <p className="mt-4 text-zinc-500">O identificador pode estar incorreto ou o título saiu do catálogo.</p>
        <Link className={buttonClassName("primary", "mt-8")} href="/search">
          Voltar à busca
        </Link>
      </div>
    </main>
  );
}
