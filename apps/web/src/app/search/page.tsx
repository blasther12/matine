import { connection } from "next/server";
import Link from "next/link";

import { SearchClient } from "./search-client";

export const metadata = {
  title: "Buscar filmes",
  description: "Busque filmes no catálogo TMDB sem criar histórico de pesquisa.",
};

export default async function SearchPage() {
  await connection();
  return (
    <div className="film-grain min-h-screen bg-background text-foreground">
      <header className="border-b border-white/[0.07] bg-background/85 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid size-9 place-items-center rounded-xl border border-amber-200/20 bg-amber-300/10 font-serif text-lg text-amber-100">
              M
            </span>
            <span className="text-sm font-semibold tracking-[0.16em] text-zinc-100 uppercase">
              Matinê
            </span>
          </Link>
          <span className="font-mono text-[0.62rem] tracking-widest text-zinc-600 uppercase">
            privado por padrão
          </span>
        </div>
      </header>
      <main className="cinema-grid min-h-[calc(100vh-5rem)]">
        <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 sm:py-20 lg:px-10">
          <SearchClient />
        </div>
      </main>
    </div>
  );
}
