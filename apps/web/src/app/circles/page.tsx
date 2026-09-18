import Link from "next/link";
import type { Metadata } from "next";

import {
  addCircleMember,
  addMovieNightCandidate,
  createCircle,
  createMovieNight,
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
  if (score >= 1) return "Unanimidade";
  if (score >= 0.67) return "Match forte";
  return "Boa possibilidade";
}

export default async function CirclesPage({ searchParams }: Props) {
  const token = await requireAccessToken();
  const query = await searchParams;
  const circles = await experienceApi.circles(token);
  const selectedCircle =
    circles.find((circle) => circle.id === query.circle) ?? null;
  const match = selectedCircle
    ? await experienceApi.match(token, selectedCircle.id).catch(() => [])
    : [];
  const night =
    query.night && /^[0-9a-f-]{36}$/i.test(query.night)
      ? await experienceApi.night(token, query.night).catch(() => null)
      : null;

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
            Só membros entram no círculo. Biblioteca, diário e notas continuam
            privados e não são expostos ao grupo.
          </p>
        </Panel>
        <Panel>
          <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
            02 · Explicável
          </p>
          <h2 className="mt-3 font-serif text-2xl text-white">
            O match mostra o motivo
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            Em vez de um algoritmo secreto, o Matinê mostra quantas pessoas do
            grupo já querem assistir a cada filme.
          </p>
        </Panel>
        <Panel>
          <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
            03 · Decide
          </p>
          <h2 className="mt-3 font-serif text-2xl text-white">
            Do gosto em comum para a sessão
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            Abra uma Movie Night, candidate os matches e vote sem copiar links,
            IDs ou abrir uma enquete em outro app.
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
            <form action={createCircle} className="mt-4 flex flex-col gap-3 sm:flex-row">
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
                      {circle.role === "OWNER" ? "Você criou" : "Você participa"} ·{" "}
                      {circle.member_count} membro
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
                      O Movie Match usa somente sinais explícitos das bibliotecas
                      dos membros. Nenhum histórico oculto é compartilhado.
                    </p>
                  </div>
                  <Link
                    className="text-sm text-zinc-500 transition hover:text-white active:translate-y-px"
                    href="/circles"
                  >
                    Fechar círculo
                  </Link>
                </div>

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
                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                  <div>
                    <p className="font-mono text-[0.62rem] tracking-[0.18em] text-amber-200 uppercase">
                      Movie Match
                    </p>
                    <h2 className="mt-2 font-serif text-3xl text-white">
                      Onde as watchlists se encontram
                    </h2>
                    <p className="mt-2 text-sm text-zinc-500">
                      Quanto maior a porcentagem, mais gente do círculo já marcou
                      aquele filme como “quero assistir”.
                    </p>
                  </div>
                  {!night ? (
                    <form action={createMovieNight} className="min-w-64">
                      <input
                        name="circle_id"
                        type="hidden"
                        value={selectedCircle.id}
                      />
                      <input
                        className={fieldClass}
                        defaultValue="Filme da noite"
                        maxLength={120}
                        name="title"
                        required
                      />
                      <SubmitButton
                        className="mt-3 w-full rounded-xl"
                        pendingLabel="Abrindo votação..."
                      >
                        Abrir Movie Night
                      </SubmitButton>
                    </form>
                  ) : null}
                </div>

                <div className="mt-6 grid gap-3">
                  {match.length ? (
                    match.slice(0, 12).map((item) => (
                      <article
                        className="rounded-xl border border-white/10 bg-black/20 p-4"
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
                            </div>
                            <Link
                              className="mt-2 block font-serif text-2xl text-white hover:text-amber-100"
                              href={`/movie/${item.tmdb_id}`}
                            >
                              {item.title ?? `Filme #${item.tmdb_id}`}
                            </Link>
                            <p className="mt-1 text-sm text-zinc-400">
                              {item.reason}
                            </p>
                          </div>

                          {night ? (
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
                        precisar revelar o restante da biblioteca.
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
                    </div>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-zinc-500">
                      1 voto por pessoa
                    </span>
                  </div>

                  <div className="mt-6 space-y-3">
                    {night.results.length ? (
                      night.results.map((result) => (
                        <div
                          className="flex flex-col justify-between gap-3 rounded-xl border border-white/10 bg-black/20 p-4 sm:flex-row sm:items-center"
                          key={result.tmdb_id}
                        >
                          <div>
                            <Link
                              className="font-semibold text-white hover:text-amber-100"
                              href={`/movie/${result.tmdb_id}`}
                            >
                              {result.title ?? `Filme #${result.tmdb_id}`}
                            </Link>
                            <p className="mt-1 text-sm text-zinc-500">
                              {result.votes} voto{result.votes === 1 ? "" : "s"}
                            </p>
                          </div>
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
                  Cada pessoa cuida da própria biblioteca.
                </li>
                <li>
                  <span className="mr-3 text-amber-200">02</span>
                  O Matinê encontra somente o gosto em comum necessário para
                  decidir.
                </li>
                <li>
                  <span className="mr-3 text-amber-200">03</span>
                  O grupo abre uma Movie Night com candidatos reais do match.
                </li>
                <li>
                  <span className="mr-3 text-amber-200">04</span>
                  Cada membro vota uma vez e o resultado fica no próprio círculo.
                </li>
              </ol>
            </Panel>
          )}
        </div>
      </div>
    </ExperienceShell>
  );
}
