import type { Metadata } from "next";

import { followUser } from "@/app/features/actions";
import { ExperienceShell, Panel, fieldClass } from "@/components/experience-shell";
import { SubmitButton } from "@/components/ui/submit-button";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Social" };
export const dynamic = "force-dynamic";

export default async function SocialPage() {
  const feed = await experienceApi.feed(await requireAccessToken());
  return (
    <ExperienceShell eyebrow="Fase 7 · Social" title="Feed social">
      <Panel>
        <form action={followUser} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex-1 text-sm text-zinc-300">Seguir por username<input className={fieldClass} name="username" placeholder="username" required /></label>
          <SubmitButton className="rounded-xl" pendingLabel="Seguindo...">Seguir</SubmitButton>
        </form>
      </Panel>
      <div className="mt-6 space-y-4">
        {feed.length ? feed.map((item, index) => (
          <Panel key={`${item.username}-${item.tmdb_id}-${index}`}>
            <p className="text-xs text-amber-200">@{item.username} · {item.spoiler ? "spoiler" : "sem spoiler"}</p>
            <h2 className="mt-2 font-serif text-2xl text-white">{item.title ?? `Filme #${item.tmdb_id}`}</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-300">{item.body}</p>
          </Panel>
        )) : <Panel><p className="text-zinc-400">Seu feed ainda está vazio. Reviews privadas nunca aparecem aqui.</p></Panel>}
      </div>
    </ExperienceShell>
  );
}
