import Link from "next/link";
import type { Metadata } from "next";

import {
  addCircleMember,
  addMovieNightCandidate,
  createCircle,
  createMovieNight,
  voteMovieNight,
} from "@/app/features/actions";
import { ExperienceShell, Panel, buttonClass, fieldClass } from "@/components/experience-shell";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Círculos" };
export const dynamic = "force-dynamic";

type Props = {
  searchParams: Promise<{ circle?: string; night?: string }>;
};

export default async function CirclesPage({ searchParams }: Props) {
  const token = await requireAccessToken();
  const query = await searchParams;
  const circles = await experienceApi.circles(token);
  const selectedCircle = circles.find((circle) => circle.id === query.circle) ?? null;
  const match = selectedCircle
    ? await experienceApi.match(token, selectedCircle.id).catch(() => [])
    : [];
  const night =
    query.night && /^[0-9a-f-]{36}$/i.test(query.night)
      ? await experienceApi.night(token, query.night).catch(() => null)
      : null;

  return (
    <ExperienceShell eyebrow="Fases 9–11 · Circles · Match · Movie Night" title="Escolher junto">
      <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="space-y-5">
          <Panel>
            <h2 className="font-serif text-2xl text-white">Novo círculo</h2>
            <form action={createCircle} className="mt-4 flex gap-3">
              <input className={fieldClass} maxLength={100} name="name" placeholder="Ex.: Terror de sábado" required />
              <button className={buttonClass} type="submit">Criar</button>
            </form>
          </Panel>
          {circles.map((circle) => (
            <Panel key={circle.id}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs text-amber-200">{circle.role} · {circle.member_count} membros</p>
                  <h2 className="mt-2 font-serif text-3xl text-white">{circle.name}</h2>
                </div>
                <Link className="text-sm text-amber-200" href={`/circles?circle=${circle.id}`}>Movie Match →</Link>
              </div>
              {circle.role === "OWNER" ? (
                <form action={addCircleMember} className="mt-5 flex gap-2">
                  <input name="circle_id" type="hidden" value={circle.id} />
                  <input className={fieldClass} name="username" placeholder="username para adicionar" required />
                  <button className={buttonClass} type="submit">Adicionar</button>
                </form>
              ) : null}
              <form action={createMovieNight} className="mt-3 flex gap-2">
                <input name="circle_id" type="hidden" value={circle.id} />
                <input className={fieldClass} name="title" placeholder="Nome da Movie Night" required />
                <button className={buttonClass} type="submit">Abrir votação</button>
              </form>
            </Panel>
          ))}
        </div>

        <div className="space-y-5">
          {selectedCircle ? (
            <Panel>
              <p className="text-xs text-amber-200">Movie Match explicável</p>
              <h2 className="mt-2 font-serif text-3xl text-white">{selectedCircle.name}</h2>
              <div className="mt-5 space-y-3">
                {match.length ? match.slice(0, 12).map((item) => (
                  <div className="rounded-xl border border-white/10 p-4" key={item.tmdb_id}>
                    <p className="font-semibold text-white">{item.title ?? `Filme #${item.tmdb_id}`}</p>
                    <p className="mt-1 text-sm text-zinc-400">{item.reason} · {(item.score * 100).toFixed(0)}%</p>
                  </div>
                )) : <p className="text-sm text-zinc-500">Nenhuma watchlist compartilhada ainda.</p>}
              </div>
            </Panel>
          ) : <Panel><p className="text-zinc-400">Abra um círculo para calcular compatibilidade sem perfilamento oculto.</p></Panel>}

          {night ? (
            <Panel>
              <p className="text-xs text-amber-200">Movie Night · {night.status}</p>
              <h2 className="mt-2 font-serif text-3xl text-white">{night.title}</h2>
              <form action={addMovieNightCandidate} className="mt-5 flex gap-2">
                <input name="night_id" type="hidden" value={night.id} />
                <input className={fieldClass} name="tmdb_id" placeholder="TMDB ID do candidato" required />
                <button className={buttonClass} type="submit">Candidatar</button>
              </form>
              <form action={voteMovieNight} className="mt-3 flex gap-2">
                <input name="night_id" type="hidden" value={night.id} />
                <input className={fieldClass} name="tmdb_id" placeholder="TMDB ID do seu voto" required />
                <button className={buttonClass} type="submit">Votar</button>
              </form>
              <div className="mt-5 space-y-2">
                {night.results.map((result) => (
                  <p className="text-sm text-zinc-300" key={result.tmdb_id}>{result.title ?? `Filme #${result.tmdb_id}`} · {result.votes} voto(s)</p>
                ))}
              </div>
            </Panel>
          ) : null}
        </div>
      </div>
    </ExperienceShell>
  );
}
