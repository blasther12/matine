import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";

import { removeLibraryMovie } from "@/app/library/actions";
import { Badge } from "@/components/ui/badge";
import { buttonClassName } from "@/components/ui/button";
import { SubmitButton } from "@/components/ui/submit-button";
import { getLibrary, getProfile, type LibraryStatus } from "@/lib/backend.server";
import { tmdbImageUrl } from "@/lib/api";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Minha biblioteca" };
export const dynamic = "force-dynamic";

const labels: Record<LibraryStatus, string> = {
  WATCHLIST: "Quero assistir",
  WATCHED: "Assistido",
  DROPPED: "Abandonado",
};

type Props = { searchParams: Promise<{ status?: string }> };

export default async function LibraryPage({ searchParams }: Props) {
  const supabase = await createSupabaseServerClient();
  const [{ data: userData }, { data: sessionData }, query] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession(),
    searchParams,
  ]);
  if (!userData.user || !sessionData.session) redirect("/login");

  const filter = query.status === "WATCHLIST" || query.status === "WATCHED" ? query.status : undefined;
  const token = sessionData.session.access_token;
  const [profile, library] = await Promise.all([getProfile(token), getLibrary(token, filter)]);
  if (!profile || library === null) redirect("/account");

  return (
    <main className="film-grain min-h-screen bg-background text-foreground">
      <header className="border-b border-white/[0.07] bg-background/90 backdrop-blur-xl">
        <div className="mx-auto flex min-h-20 max-w-7xl items-center justify-between gap-4 px-5 py-4 sm:px-8 lg:px-10">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid size-9 place-items-center rounded-xl border border-amber-200/20 bg-amber-300/10 font-serif text-lg text-amber-100">M</span>
            <span className="text-sm font-semibold tracking-[0.16em] text-zinc-100 uppercase">Matinê</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link className={buttonClassName("secondary", "min-h-9 px-4 py-1.5 text-xs")} href="/search">Buscar filmes</Link>
            <Link className="text-xs text-zinc-400 hover:text-white" href="/account">@{profile.username}</Link>
          </div>
        </div>
      </header>

      <section className="cinema-grid border-b border-white/[0.07] px-5 py-14 sm:px-8 lg:px-10">
        <div className="mx-auto max-w-7xl">
          <Badge tone="accent">Privada por padrão</Badge>
          <h1 className="mt-5 font-serif text-5xl tracking-[-0.04em] text-white sm:text-6xl">Minha biblioteca</h1>
          <p className="mt-4 max-w-2xl leading-7 text-zinc-400">Seu histórico, suas notas e seus favoritos ficam visíveis somente para você.</p>
          <nav aria-label="Filtros da biblioteca" className="mt-8 flex flex-wrap gap-2">
            <Link className={buttonClassName(filter ? "secondary" : "primary", "min-h-9 px-4 py-2 text-xs")} href="/library">Todos</Link>
            <Link className={buttonClassName(filter === "WATCHLIST" ? "primary" : "secondary", "min-h-9 px-4 py-2 text-xs")} href="/library?status=WATCHLIST">Quero assistir</Link>
            <Link className={buttonClassName(filter === "WATCHED" ? "primary" : "secondary", "min-h-9 px-4 py-2 text-xs")} href="/library?status=WATCHED">Assistidos</Link>
          </nav>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:px-10">
        {library.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-white/10 px-6 py-16 text-center">
            <p className="font-serif text-3xl text-white">Sua estante está vazia.</p>
            <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-zinc-500">Encontre um filme e marque se quer assistir, já assistiu ou abandonou.</p>
            <Link className={buttonClassName("primary", "mt-7")} href="/search">Descobrir filmes</Link>
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {library.map((entry) => {
              const poster = tmdbImageUrl(entry.poster_path ?? null, "w342");
              return (
                <article className="overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.025]" key={entry.tmdb_id}>
                  <Link className="block" href={`/movie/${entry.tmdb_id}`}>
                    <div className="relative aspect-[2/3] bg-zinc-900">
                      {poster ? <Image alt={`Pôster de ${entry.title ?? "filme"}`} className="object-cover" fill loading="lazy" sizes="(max-width: 640px) 100vw, 342px" src={poster} /> : <div className="grid h-full place-items-center px-6 text-center font-serif text-2xl text-zinc-600">{entry.title ?? `Filme #${entry.tmdb_id}`}</div>}
                      {entry.favorite ? <span className="absolute right-3 top-3 rounded-full bg-black/75 px-3 py-1 text-amber-200" aria-label="Favorito">★</span> : null}
                    </div>
                  </Link>
                  <div className="p-5">
                    <p className="text-xs font-medium tracking-[0.12em] text-amber-200 uppercase">{labels[entry.status]}</p>
                    <h2 className="mt-2 line-clamp-2 font-serif text-2xl text-white">{entry.title ?? `Filme #${entry.tmdb_id}`}</h2>
                    <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
                      <span>{entry.year ?? "Ano indisponível"}</span>
                      <span>{entry.rating ? `★ ${entry.rating.toFixed(1)}` : "Sem nota"}</span>
                    </div>
                    <form action={removeLibraryMovie} className="mt-5 border-t border-white/[0.07] pt-4">
                      <input name="tmdb_id" type="hidden" value={entry.tmdb_id} />
                      <SubmitButton className="min-h-8 rounded-lg px-3 py-1 text-xs" pendingLabel="Removendo..." variant="secondary">Remover da biblioteca</SubmitButton>
                    </form>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
