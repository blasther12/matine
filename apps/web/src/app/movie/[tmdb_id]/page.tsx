import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { buttonClassName } from "@/components/ui/button";
import {
  ApiError,
  formatRuntime,
  getMovieCredits,
  getMovieDetails,
  getMovieProviders,
  type MovieProviders,
  tmdbImageUrl,
} from "@/lib/api";

export const dynamic = "force-dynamic";

function ProviderGroup({
  label,
  providers,
}: {
  label: string;
  providers: MovieProviders["streaming"];
}) {
  if (providers.length === 0) return null;
  return (
    <div>
      <h3 className="font-mono text-[0.62rem] tracking-[0.18em] text-zinc-500 uppercase">
        {label}
      </h3>
      <div className="mt-3 flex flex-wrap gap-3">
        {providers.map((provider) => {
          const logo = tmdbImageUrl(provider.logo_path, "w185");
          return (
            <div
              className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.035] p-2 pr-3 text-xs text-zinc-300"
              key={provider.tmdb_provider_id}
            >
              {logo ? (
                <Image
                  alt=""
                  className="rounded-lg"
                  height={32}
                  src={logo}
                  width={32}
                />
              ) : (
                <span className="size-8 rounded-lg bg-zinc-800" />
              )}
              {provider.name}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default async function MoviePage({
  params,
}: {
  params: Promise<{ tmdb_id: string }>;
}) {
  const rawId = (await params).tmdb_id;
  if (!/^\d{1,10}$/.test(rawId)) notFound();
  const tmdbId = Number(rawId);
  if (!Number.isSafeInteger(tmdbId) || tmdbId < 1 || tmdbId > 2_147_483_647) {
    notFound();
  }

  let movie;
  try {
    movie = await getMovieDetails(tmdbId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const [creditsResult, providersResult] = await Promise.allSettled([
    getMovieCredits(tmdbId),
    getMovieProviders(tmdbId),
  ]);
  const credits = creditsResult.status === "fulfilled" ? creditsResult.value : null;
  const providers = providersResult.status === "fulfilled" ? providersResult.value : null;
  const directors = credits?.crew.filter((member) => member.job === "Director") ?? [];
  const poster = tmdbImageUrl(movie.poster_path, "w500");
  const backdrop = tmdbImageUrl(movie.backdrop_path, "original");
  const runtime = formatRuntime(movie.runtime_minutes);

  return (
    <div className="film-grain min-h-screen bg-background text-foreground">
      <header className="relative z-30 border-b border-white/[0.07] bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid size-9 place-items-center rounded-xl border border-amber-200/20 bg-amber-300/10 font-serif text-lg text-amber-100">
              M
            </span>
            <span className="text-sm font-semibold tracking-[0.16em] text-zinc-100 uppercase">
              Matinê
            </span>
          </Link>
          <Link className={buttonClassName("secondary", "min-h-9 px-4 py-1.5 text-xs")} href="/search">
            Nova busca
          </Link>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden border-b border-white/[0.07]">
          {backdrop && (
            <>
              <Image
                alt=""
                className="object-cover opacity-30"
                fill
                priority
                sizes="100vw"
                src={backdrop}
              />
              <div className="absolute inset-0 bg-[linear-gradient(90deg,#08090b_8%,rgba(8,9,11,.72)_55%,#08090b),linear-gradient(0deg,#08090b,transparent_70%)]" />
            </>
          )}
          <div className="relative mx-auto grid max-w-7xl gap-10 px-5 py-14 sm:px-8 sm:py-20 md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr] lg:px-10">
            <div className="mx-auto w-full max-w-[280px]">
              <div className="relative aspect-[2/3] overflow-hidden rounded-2xl border border-white/10 bg-zinc-900 shadow-2xl">
                {poster ? (
                  <Image
                    alt={`Pôster de ${movie.title}`}
                    className="object-cover"
                    fill
                    priority
                    sizes="(max-width: 768px) 70vw, 280px"
                    src={poster}
                  />
                ) : (
                  <div className="grid h-full place-items-center px-8 text-center font-serif text-3xl text-zinc-600">
                    {movie.title}
                  </div>
                )}
              </div>
            </div>

            <div className="self-end pb-3">
              <div className="flex flex-wrap gap-2">
                {movie.genres.map((genre) => (
                  <Badge key={genre.tmdb_id}>{genre.name}</Badge>
                ))}
              </div>
              <h1 className="mt-6 max-w-4xl text-balance font-serif text-5xl leading-[0.96] tracking-[-0.04em] text-white sm:text-6xl lg:text-7xl">
                {movie.title}
              </h1>
              {movie.original_title !== movie.title && (
                <p className="mt-3 text-sm text-zinc-500">{movie.original_title}</p>
              )}
              <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-sm text-zinc-400">
                {movie.year && <span>{movie.year}</span>}
                {runtime && <span>{runtime}</span>}
                <span className="text-amber-200">★ {movie.vote_average.toFixed(1)} TMDB</span>
                {directors.length > 0 && (
                  <span>Direção: {directors.map((director) => director.name).join(", ")}</span>
                )}
              </div>
              <p className="mt-7 max-w-3xl text-pretty text-base leading-8 text-zinc-300">
                {movie.overview || "Sinopse ainda não disponível em português."}
              </p>
              {movie.trailer && (
                <a
                  className={buttonClassName("primary", "mt-8")}
                  href={`https://www.youtube.com/watch?v=${movie.trailer.key}`}
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  Assistir trailer
                  <span aria-hidden="true">↗</span>
                </a>
              )}
            </div>
          </div>
        </section>

        <div className="mx-auto grid max-w-7xl gap-14 px-5 py-16 sm:px-8 lg:grid-cols-[1fr_0.75fr] lg:px-10 lg:py-20">
          <section>
            <div className="flex items-end justify-between">
              <div>
                <Badge>Créditos</Badge>
                <h2 className="mt-4 font-serif text-3xl text-white">Elenco principal</h2>
              </div>
              <span className="text-xs text-zinc-600">Fonte: TMDB</span>
            </div>
            {credits && credits.cast.length > 0 ? (
              <div className="mt-7 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                {credits.cast.slice(0, 8).map((member) => {
                  const profile = tmdbImageUrl(member.profile_path, "w185");
                  return (
                    <article
                      className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.025]"
                      key={`${member.tmdb_id}-${member.character}`}
                    >
                      <div className="relative aspect-[3/4] bg-zinc-900">
                        {profile ? (
                          <Image
                            alt={`Foto de ${member.name}`}
                            className="object-cover"
                            fill
                            sizes="(max-width: 640px) 50vw, 180px"
                            src={profile}
                          />
                        ) : (
                          <div className="grid h-full place-items-center text-2xl text-zinc-700">○</div>
                        )}
                      </div>
                      <div className="p-3">
                        <h3 className="text-sm font-semibold text-zinc-200">{member.name}</h3>
                        <p className="mt-1 line-clamp-1 text-xs text-zinc-600">{member.character}</p>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <p className="mt-7 rounded-2xl border border-dashed border-white/10 p-8 text-sm text-zinc-500">
                Créditos indisponíveis no momento.
              </p>
            )}
          </section>

          <aside>
            <Badge tone="accent">Onde assistir · BR</Badge>
            <h2 className="mt-4 font-serif text-3xl text-white">Disponibilidade</h2>
            {providers &&
            [
              providers.streaming,
              providers.free,
              providers.ads,
              providers.rent,
              providers.buy,
            ].some((group) => group.length > 0) ? (
              <div className="mt-7 space-y-7 rounded-2xl border border-white/[0.08] bg-white/[0.025] p-6">
                <ProviderGroup label="Streaming" providers={providers.streaming} />
                <ProviderGroup label="Grátis" providers={providers.free} />
                <ProviderGroup label="Com anúncios" providers={providers.ads} />
                <ProviderGroup label="Alugar" providers={providers.rent} />
                <ProviderGroup label="Comprar" providers={providers.buy} />
                <p className="border-t border-white/[0.07] pt-5 text-[0.65rem] leading-5 text-zinc-600">
                  Disponibilidade fornecida pelo JustWatch via TMDB. Consulte o serviço antes de assinar ou comprar.
                </p>
              </div>
            ) : (
              <p className="mt-7 rounded-2xl border border-dashed border-white/10 p-8 text-sm leading-6 text-zinc-500">
                Nenhuma opção informada para o Brasil neste momento.
              </p>
            )}
          </aside>
        </div>
      </main>

      <footer className="border-t border-white/[0.07] px-5 py-8 text-center text-[0.65rem] leading-5 text-zinc-600">
        Este produto usa a API do TMDB, mas não é endossado nem certificado pelo TMDB.
      </footer>
    </div>
  );
}
