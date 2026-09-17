"use client";

import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { searchMovies, tmdbImageUrl } from "@/lib/api";

function useDebouncedValue(value: string, delay: number): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value.trim()), delay);
    return () => window.clearTimeout(timer);
  }, [delay, value]);
  return debounced;
}

function MovieCard({
  movie,
}: {
  movie: Awaited<ReturnType<typeof searchMovies>>["results"][number];
}) {
  const poster = tmdbImageUrl(movie.poster_path, "w342");
  return (
    <Link
      className="group overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.025] transition hover:-translate-y-1 hover:border-amber-200/30 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-300"
      href={`/movie/${movie.tmdb_id}`}
    >
      <div className="relative aspect-[2/3] overflow-hidden bg-zinc-900">
        {poster ? (
          <Image
            alt={`Pôster de ${movie.title}`}
            className="object-cover transition duration-500 group-hover:scale-[1.025]"
            fill
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw"
            src={poster}
          />
        ) : (
          <div className="grid h-full place-items-center px-6 text-center font-serif text-xl text-zinc-600">
            {movie.title}
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 to-transparent" />
        <span className="absolute right-3 bottom-3 rounded-full bg-black/70 px-2.5 py-1 font-mono text-[0.62rem] text-amber-100 backdrop-blur">
          ★ {movie.vote_average.toFixed(1)}
        </span>
      </div>
      <div className="p-4">
        <h2 className="line-clamp-2 font-semibold text-zinc-100">{movie.title}</h2>
        <p className="mt-1 text-xs text-zinc-500">{movie.year ?? "Ano não informado"}</p>
      </div>
    </Link>
  );
}

export function SearchClient() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 350);
  const enabled = debouncedQuery.length >= 2;
  const result = useQuery({
    queryKey: ["movie-search", debouncedQuery],
    queryFn: () => searchMovies(debouncedQuery),
    enabled,
    placeholderData: (previous) => previous,
  });

  return (
    <>
      <div className="mx-auto max-w-3xl text-center">
        <Badge tone="accent">Catálogo TMDB · Fase 1</Badge>
        <h1 className="mt-6 text-balance font-serif text-5xl tracking-[-0.04em] text-white sm:text-6xl">
          Encontre seu próximo filme.
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-pretty leading-7 text-zinc-400">
          A consulta é enviada ao TMDB apenas para responder agora. Não criamos um histórico das suas buscas.
        </p>
        <label className="sr-only" htmlFor="movie-search">
          Buscar filme
        </label>
        <div className="relative mt-9">
          <input
            autoComplete="off"
            autoFocus
            className="h-14 w-full rounded-full border border-white/12 bg-white/[0.055] px-6 pr-28 text-base text-white outline-none transition placeholder:text-zinc-600 focus:border-amber-200/50 focus:ring-4 focus:ring-amber-300/10"
            id="movie-search"
            maxLength={100}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Alien, Central do Brasil, Parasita…"
            type="search"
            value={query}
          />
          <span className="absolute top-1/2 right-5 -translate-y-1/2 font-mono text-[0.6rem] tracking-widest text-zinc-600 uppercase">
            {result.isFetching ? "Buscando" : "350 ms"}
          </span>
        </div>
      </div>

      <div aria-live="polite" className="mt-14">
        {!enabled && (
          <div className="rounded-2xl border border-dashed border-white/10 py-16 text-center text-sm text-zinc-500">
            Digite ao menos dois caracteres para começar.
          </div>
        )}

        {result.isPending && enabled && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {Array.from({ length: 10 }, (_, index) => (
              <div
                aria-hidden="true"
                className="aspect-[2/3] animate-pulse rounded-2xl bg-white/[0.055]"
                key={index}
              />
            ))}
          </div>
        )}

        {result.isError && (
          <div className="rounded-2xl border border-red-300/15 bg-red-300/[0.04] px-6 py-12 text-center">
            <p className="font-semibold text-zinc-100">Não foi possível buscar agora.</p>
            <p className="mt-2 text-sm text-zinc-500">Tente novamente em alguns instantes.</p>
          </div>
        )}

        {result.data && result.data.results.length === 0 && (
          <div className="rounded-2xl border border-dashed border-white/10 py-16 text-center">
            <p className="font-serif text-2xl text-zinc-200">Nenhum filme encontrado.</p>
            <p className="mt-2 text-sm text-zinc-500">Tente o título original ou uma busca mais curta.</p>
          </div>
        )}

        {result.data && result.data.results.length > 0 && (
          <>
            <div className="mb-5 flex items-end justify-between gap-4">
              <p className="text-sm text-zinc-500">
                {result.data.total_results.toLocaleString("pt-BR")} resultado(s)
              </p>
              <p className="text-right text-[0.65rem] text-zinc-600">Fonte: TMDB</p>
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
              {result.data.results.map((movie) => (
                <MovieCard key={movie.tmdb_id} movie={movie} />
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}
