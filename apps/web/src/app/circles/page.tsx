import Link from "next/link";
import type { Metadata } from "next";

import {
  addCircleMember,
  addMovieNightCandidate,
  createCircle,
  createMovieNight,
  removeMovieNightVeto,
  vetoMovieNightCandidate,
  voteMovieNight,
} from "@/app/features/actions";
import {
  ExperienceShell,
  Panel,
  fieldClass,
} from "@/components/experience-shell";
import { SubmitButton } from "@/components/ui/submit-button";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Círculos" };
export const dynamic = "force-dynamic";

type Props = {
  searchParams: Promise<{ circle?: string; night?: string }>;
};

function matchTone(score: number): string {
  if (score >= 0.9) return "Quase perfeito";
  if (score >= 0.7) return "Match forte";
  if (score >= 0.5) return "Boa possibilidade";
  return "Match em construção";
}

export default async function CirclesPage({ searchParams }: Props) {
  const token = await requireAccessToken();
  const query = await searchParams;
  const circles = await experienceApi.circles(token);
  const selectedCircle =
    circles.find((circle) => circle.id === query.circle) ?? null;

  const night =
    query.night && /^[0-9a-f-]{36}$/i.test(query.night)
      ? await experienceApi.night(token, query.night).catch(() => null)
      : null;

  const [match, streaming] = selectedCircle
    ? await Promise.all([
        experienceApi
          .match(token, selectedCircle.id, night?.id)
          .catch(() => []),
        experienceApi
          .circleStreaming(token, selectedCircle.id)
          .catch(() => null),
      ])
    : [[], null];

  return (
    <ExperienceShell
      eyebrow="Círculos privados · Match explicável · Movie Night"
      title="Escolher junto sem virar debate infinito"
    >
      <section className="grid gap-4 md:grid-cols-3">
        <Panel>
          <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
            01 · Privado
          </p>
          <h2 className="mt-3 font-serif text-2xl text-white">
            O grupo não vira rede social pública
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            Biblioteca, diário e notas continuam privados. O círculo recebe só
            os sinais necessários para chegar a uma escolha.
          </p>
        </Panel>
        <Panel>
          <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
            02 · Explicável
          </p>
          <h2 className="mt-3 font-serif text-2xl text-white">
            O match mostra por que faz sentido
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            Interesse em comum, streaming configurado e contexto da sessão
            entram no resultado sem algoritmo secreto.
          </p>
        </Panel>
        <Panel>
          <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
            03 · Decide
          </p>
          <h2 className="mt-3 font-serif text-2xl text-white">
            Voto aberto, veto privado
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            Cada pessoa vota no favorito e pode tirar um filme da rodada sem
            expor quem usou o veto.
          </p>
        </Panel>
      </section>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <div className="space-y-5">
          <Panel>
            <p className="text-xs text-zinc-500">Comece pequeno</p>
            <h2 className="mt-2 font-serif text-2xl text-white">
              Novo círculo
            </h2>
            <form
              action={createCircle}
              className="mt-4 flex flex-col gap-3 sm:flex-row"
            >
              <input
                className={fieldClass}
                maxLength={100}
                name="name"
                placeholder="Ex.: Terror de sábado"
                required
              />
              <SubmitButton
                className="rounded-xl sm:self-end"
                pendingLabel="Criando..."
              >
                Criar círculo
              </SubmitButton>
            </form>
          </Panel>

          <div className="space-y-3">
            {circles.length ? (
              circles.map((circle) => {
                const selected = selectedCircle?.id === circle.id;
                return (
                  <Link
                    className={[
                      "block rounded-2xl border p-5 transition-[transform,border-color,background-color] duration-150 active:scale-[0.99]",
                      selected
                        ? "border-amber-300/35 bg-amber-300/[0.07]"
                        : "border-white/10 bg-white/[0.025] hover:border-white/20",
                    ].join(" ")}
                    href={`/circles?circle=${circle.id}`}
                    key={circle.id}
                  >
                    <p className="text-xs text-amber-200">
                      {circle.role === "OWNER"
                        ? "Você criou"
                        : "Você participa"}{" "}
                      · {circle.member_count} membro
                      {circle.member_count === 1 ? "" : "s"}
                    </p>
                    <div className="mt-2 flex items-center justify-between gap-4">
                      <h2 className="font-serif text-2xl text-white">
                        {circle.name}
                      </h2>
                      <span className="text-sm text-zinc-500">
                        {selected ? "Aberto" : "Abrir →"}
                      </span>
                    </div>
                  </Link>
                );
              })
            ) : (
              <Panel>
                <p className="text-sm leading-6 text-zinc-400">
                  Crie seu primeiro círculo para juntar watchlists e descobrir o
                  ponto de encontro do grupo.
                </p>
              </Panel>
            )}
          </div>
        </div>

        <div className="space-y-5">
          {selectedCircle ? (
            <>
              <Panel>
                <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
                  <div>
                    <p className="text-xs text-amber-200">
                      Círculo privado · {selectedCircle.member_count} membro
                      {selectedCircle.member_count === 1 ? "" : "s"}
                    </p>
                    <h2 className="mt-2 font-serif text-4xl text-white">
                      {selectedCircle.name}
                    </h2>
                    <p className="mt-3 max-w-xl text-sm leading-6 text-zinc-400">
                      O Matinê cruza somente watchlist, serviços escolhidos e o
                      contexto desta sessão. Nenhum histórico individual fica
                      visível para o grupo.
                    </p>
                  </div>
                  <Link
                    className="text-sm text-zinc-500 transition hover:text-white active:translate-y-px"
                    href="/circles"
                  >
                    Fechar círculo
                  </Link>
                </div>

                {streaming ? (
                  <div className="mt-6 rounded-xl border border-white/10 bg-black/20 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">
                          Streaming do grupo
                        </p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {streaming.configured_members} de{" "}
                          {streaming.member_count} membros configuraram seus
                          serviços.
                        </p>
                      </div>
                      <Link
                        className="text-xs text-amber-200"
                        href="/streaming"
                      >
                        Meus serviços →
                      </Link>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {streaming.providers.length ? (
                        streaming.providers.slice(0, 8).map((provider) => (
                          <span
                            className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-zinc-300"
                            key={provider.provider}
                          >
                            {provider.provider} · {provider.members}/
                            {streaming.member_count}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-zinc-500">
                          Ninguém configurou streaming ainda.
                        </span>
                      )}
                    </div>
                  </div>
                ) : null}

                {selectedCircle.role === "OWNER" ? (
                  <form
                    action={addCircleMember}
                    className="mt-6 grid gap-3 rounded-xl border border-white/10 bg-black/20 p-4 sm:grid-cols-[1fr_auto] sm:items-end"
                  >
                    <input
                      name="circle_id"
                      type="hidden"
                      value={selectedCircle.id}
                    />
                    <label className="text-sm text-zinc-300">
                      Convidar por username
                      <input
                        className={fieldClass}
                        name="username"
                        placeholder="ex.: amarilis"
                        required
                      />
                    </label>
                    <SubmitButton
                      className="rounded-xl"
                      pendingLabel="Adicionando..."
                      variant="secondary"
                    >
                      Adicionar pessoa
                    </SubmitButton>
                  </form>
                ) : null}
              </Panel>

              <Panel>
                <div className="flex flex-col justify-between gap-5 xl:flex-row xl:items-start">
                  <div className="max-w-xl">
                    <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
                      Movie Match
                    </p>
                    <h2 className="mt-2 font-serif text-3xl text-white">
                      Onde o grupo realmente se encontra
                    </h2>
                    <p className="mt-2 text-sm leading-6 text-zinc-500">
                      O score começa pela watchlist em comum e pode ganhar
                      contexto de streaming, duração e gênero quando esses sinais
                      estiverem disponíveis.
                    </p>
                  </div>

                  {!night ? (
                    <form
                      action={createMovieNight}
                      className="w-full rounded-xl border border-white/10 bg-black/20 p-4 xl:max-w-sm"
                    >
                      <input
                        name="circle_id"
                        type="hidden"
                        value={selectedCircle.id}
                      />
                      <label className="block text-xs text-zinc-400">
                        Nome da sessão
                        <input
                          className={fieldClass}
                          defaultValue="Filme da noite"
                          maxLength={120}
                          name="title"
                          required
                        />
                      </label>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <label className="text-xs text-zinc-400">
                          Até quantos minutos?
                          <input
                            className={fieldClass}
                            max={600}
                            min={30}
                            name="max_runtime_minutes"
                            placeholder="120"
                            type="number"
                          />
                        </label>
                        <label className="text-xs text-zinc-400">
                          Gêneros
                          <input
                            className={fieldClass}
                            name="preferred_genres"
                            placeholder="Terror, Suspense"
                          />
                        </label>
                      </div>
                      <SubmitButton
                        className="mt-4 w-full rounded-xl"
                        pendingLabel="Abrindo votação..."
                      >
                        Abrir Movie Night
                      </SubmitButton>
                    </form>
                  ) : (
                    <div className="rounded-xl border border-amber-300/20 bg-amber-300/[0.05] p-4 xl:max-w-sm">
                      <p className="text-xs font-semibold text-amber-100">
                        Contexto desta Movie Night
                      </p>
                      <div className="mt-2 space-y-1 text-sm text-zinc-300">
                        <p>
                          Duração:{" "}
                          {night.max_runtime_minutes
                            ? `até ${night.max_runtime_minutes} min`
                            : "sem limite"}
                        </p>
                        <p>
                          Gêneros:{" "}
                          {night.preferred_genres.length
                            ? night.preferred_genres.join(", ")
                            : "qualquer um"}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 grid gap-3">
                  {match.length ? (
                    match.slice(0, 12).map((item) => (
                      <article
                        className={[
                          "rounded-xl border p-4",
                          item.fits_context
                            ? "border-white/10 bg-black/20"
                            : "border-white/[0.06] bg-black/10 opacity-65",
                        ].join(" ")}
                        key={item.tmdb_id}
                      >
                        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="rounded-full bg-amber-300/10 px-2.5 py-1 text-[0.65rem] font-semibold text-amber-100">
                                {matchTone(item.score)}
                              </span>
                              <span className="text-xs text-zinc-500">
                                {(item.score * 100).toFixed(0)}%
                              </span>
                              {night ? (
                                <span
                                  className={[
                                    "rounded-full px-2.5 py-1 text-[0.65rem]",
                                    item.fits_context
                                      ? "bg-emerald-400/10 text-emerald-200"
                                      : "bg-zinc-800 text-zinc-500",
                                  ].join(" ")}
                                >
                                  {item.fits_context
                                    ? "Cabe na sessão"
                                    : "Fora do contexto"}
                                </span>
                              ) : null}
                            </div>
                            <Link
                              className="mt-2 block font-serif text-2xl text-white hover:text-amber-100"
                              href={`/movie/${item.tmdb_id}`}
                            >
                              {item.title ?? `Filme #${item.tmdb_id}`}
                            </Link>
                            <p className="mt-1 text-sm leading-6 text-zinc-400">
                              {item.reason}
                            </p>
                            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-600">
                              {item.runtime_minutes ? (
                                <span>{item.runtime_minutes} min</span>
                              ) : null}
                              {item.streaming_provider ? (
                                <span>
                                  pelo menos {item.streaming_ready_members} com{" "}
                                  {item.streaming_provider}
                                </span>
                              ) : item.streaming_checked ? (
                                <span>sem serviço em comum detectado</span>
                              ) : (
                                <span>streaming ainda não verificado</span>
                              )}
                            </div>
                          </div>

                          {night && item.fits_context ? (
                            <form action={addMovieNightCandidate}>
                              <input
                                name="night_id"
                                type="hidden"
                                value={night.id}
                              />
                              <input
                                name="tmdb_id"
                                type="hidden"
                                value={item.tmdb_id}
                              />
                              <SubmitButton
                                className="rounded-xl"
                                pendingLabel="Candidatando..."
                                variant="secondary"
                              >
                                Levar para votação
                              </SubmitButton>
                            </form>
                          ) : null}
                        </div>
                      </article>
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed border-white/10 p-6">
                      <p className="text-sm leading-6 text-zinc-400">
                        Ainda não existe interseção suficiente. Cada pessoa pode
                        alimentar sua própria watchlist e o match aparece sem
                        revelar o restante da biblioteca.
                      </p>
                      <Link
                        className="mt-4 inline-flex text-sm text-amber-200"
                        href="/search"
                      >
                        Buscar filmes para minha watchlist →
                      </Link>
                    </div>
                  )}
                </div>
              </Panel>

              {night ? (
                <Panel>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
                        Movie Night · {night.status}
                      </p>
                      <h2 className="mt-2 font-serif text-3xl text-white">
                        {night.title}
                      </h2>
                      <p className="mt-2 text-sm text-zinc-500">
                        Cada membro tem um voto. O veto remove o filme da rodada
                        sem identificar quem pediu a retirada.
                      </p>
                    </div>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-zinc-500">
                      1 voto por pessoa
                    </span>
                  </div>

                  <div className="mt-6 space-y-3">
                    {night.results.length ? (
                      night.results.map((result) => (
                        <div
                          className={[
                            "rounded-xl border p-4",
                            result.vetoed
                              ? "border-red-300/10 bg-red-400/[0.035]"
                              : "border-white/10 bg-black/20",
                          ].join(" ")}
                          key={result.tmdb_id}
                        >
                          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                            <div>
                              <div className="flex flex-wrap items-center gap-2">
                                <Link
                                  className="font-semibold text-white hover:text-amber-100"
                                  href={`/movie/${result.tmdb_id}`}
                                >
                                  {result.title ??
                                    `Filme #${result.tmdb_id}`}
                                </Link>
                                {result.vetoed ? (
                                  <span className="rounded-full bg-red-400/10 px-2.5 py-1 text-[0.65rem] text-red-200">
                                    Fora da rodada · veto privado
                                  </span>
                                ) : null}
                              </div>
                              <p className="mt-1 text-sm text-zinc-500">
                                {result.votes} voto
                                {result.votes === 1 ? "" : "s"}
                              </p>
                            </div>

                            <div className="flex flex-wrap gap-2">
                              {!result.vetoed ? (
                                <form action={voteMovieNight}>
                                  <input
                                    name="night_id"
                                    type="hidden"
                                    value={night.id}
                                  />
                                  <input
                                    name="tmdb_id"
                                    type="hidden"
                                    value={result.tmdb_id}
                                  />
                                  <SubmitButton
                                    className="rounded-xl"
                                    pendingLabel="Votando..."
                                  >
                                    Votar neste
                                  </SubmitButton>
                                </form>
                              ) : null}

                              <form
                                action={
                                  result.my_veto
                                    ? removeMovieNightVeto
                                    : vetoMovieNightCandidate
                                }
                              >
                                <input
                                  name="night_id"
                                  type="hidden"
                                  value={night.id}
                                />
                                <input
                                  name="tmdb_id"
                                  type="hidden"
                                  value={result.tmdb_id}
                                />
                                <SubmitButton
                                  className="rounded-xl"
                                  pendingLabel={
                                    result.my_veto
                                      ? "Retirando veto..."
                                      : "Aplicando veto..."
                                  }
                                  variant="secondary"
                                >
                                  {result.my_veto
                                    ? "Retirar meu veto"
                                    : "Vetar em silêncio"}
                                </SubmitButton>
                              </form>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="rounded-xl border border-dashed border-white/10 p-5 text-sm leading-6 text-zinc-400">
                        A votação está aberta. Use os matches acima para levar
                        filmes para a Movie Night.
                      </p>
                    )}
                  </div>
                </Panel>
              ) : null}
            </>
          ) : (
            <Panel>
              <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
                Como funciona
              </p>
              <h2 className="mt-3 font-serif text-3xl text-white">
                Grupo sem planilha, enquete ou “e aí, o que vocês querem ver?”
              </h2>
              <ol className="mt-6 space-y-4 text-sm leading-6 text-zinc-400">
                <li>
                  <span className="mr-3 text-amber-200">01</span>
                  Cada pessoa mantém biblioteca e serviços de streaming no
                  próprio perfil.
                </li>
                <li>
                  <span className="mr-3 text-amber-200">02</span>
                  O Matinê calcula somente os sinais necessários para encontrar
                  o gosto em comum.
                </li>
                <li>
                  <span className="mr-3 text-amber-200">03</span>
                  A Movie Night adiciona duração e gêneros do momento.
                </li>
                <li>
                  <span className="mr-3 text-amber-200">04</span>
                  O grupo vota e qualquer pessoa pode aplicar um veto privado.
                </li>
              </ol>
            </Panel>
          )}
        </div>
      </div>
    </ExperienceShell>
  );
}
