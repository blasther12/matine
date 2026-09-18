import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";

import { ExperienceShell, Panel } from "@/components/experience-shell";
import { requireAccessToken } from "@/lib/auth.server";
import { tmdbImageUrl } from "@/lib/api";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Recomendações" };
export const dynamic = "force-dynamic";

export default async function RecommendationsPage() {
  const items = await experienceApi.recommendations(await requireAccessToken());
  return (
    <ExperienceShell eyebrow="Fase 12 · Recommendations" title="Para você, com motivos">
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {items.length ? items.map((item) => {
          const poster = tmdbImageUrl(item.poster_path, "w342");
          return <Panel key={item.tmdb_id}><Link href={`/movie/${item.tmdb_id}`}>{poster ? <div className="relative mb-4 aspect-[2/3] overflow-hidden rounded-xl"><Image alt="" className="object-cover" fill src={poster} sizes="342px" /></div> : null}<h2 className="font-serif text-2xl text-white">{item.title ?? `Filme #${item.tmdb_id}`}</h2></Link><p className="mt-2 text-sm text-amber-200">score {item.score.toFixed(2)}</p><ul className="mt-3 space-y-1 text-xs text-zinc-400">{item.reasons.map((reason) => <li key={reason}>• {reason}</li>)}</ul></Panel>;
        }) : <Panel><p className="text-zinc-400">Adicione filmes assistidos, notas e itens à watchlist para gerar recomendações explicáveis.</p></Panel>}
      </div>
    </ExperienceShell>
  );
}
