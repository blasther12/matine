import type { Metadata } from "next";

import { ExperienceShell, Panel } from "@/components/experience-shell";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Stats" };
export const dynamic = "force-dynamic";

export default async function StatsPage() {
  const stats = await experienceApi.stats(await requireAccessToken());
  const cards = [
    ["Biblioteca", stats.library_total],
    ["Quero assistir", stats.watchlist_total],
    ["Assistidos", stats.watched_total],
    ["Abandonados", stats.dropped_total],
    ["Favoritos", stats.favorite_total],
    ["Diário", stats.diary_total],
    ["Reviews", stats.review_total],
    ["Listas", stats.list_total],
    ["Nota média", stats.average_rating ?? "—"],
  ];
  return <ExperienceShell eyebrow="Fase 13 · Stats" title="Seu cinema em números"><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{cards.map(([label, value]) => <Panel key={String(label)}><p className="text-sm text-zinc-500">{label}</p><p className="mt-3 font-serif text-5xl text-white">{value}</p></Panel>)}</div></ExperienceShell>;
}
