import type { Metadata } from "next";

import { ExperienceShell, Panel, buttonClass, fieldClass } from "@/components/experience-shell";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Wrapped" };
export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ year?: string }> };

export default async function WrappedPage({ searchParams }: Props) {
  const current = new Date().getFullYear();
  const raw = (await searchParams).year;
  const parsed = raw && /^\d{4}$/.test(raw) ? Number(raw) : current;
  const year = Math.min(current, Math.max(2000, parsed));
  const data = await experienceApi.wrapped(await requireAccessToken(), year);
  return (
    <ExperienceShell eyebrow="Fase 14 · Wrapped" title={`Seu ${year} em filmes`}>
      <Panel>
        <form className="flex max-w-sm gap-3" method="get"><input className={fieldClass} min={2000} max={current} name="year" type="number" defaultValue={year} /><button className={buttonClass}>Abrir</button></form>
      </Panel>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Panel><p className="text-zinc-500">Sessões</p><p className="mt-2 font-serif text-5xl text-white">{data.watches}</p></Panel>
        <Panel><p className="text-zinc-500">Filmes únicos</p><p className="mt-2 font-serif text-5xl text-white">{data.distinct_movies}</p></Panel>
        <Panel><p className="text-zinc-500">Rewatches</p><p className="mt-2 font-serif text-5xl text-white">{data.rewatches}</p></Panel>
        <Panel><p className="text-zinc-500">Reviews</p><p className="mt-2 font-serif text-5xl text-white">{data.reviews}</p></Panel>
      </div>
      <Panel><p className="text-sm text-zinc-500">Destaque pelas suas notas</p><p className="mt-3 font-serif text-3xl text-white">{data.top_movie_title ?? (data.top_movie_tmdb_id ? `Filme #${data.top_movie_tmdb_id}` : "Ainda sem destaque")}</p></Panel>
    </ExperienceShell>
  );
}
