import type { Metadata } from "next";

import { addDiaryEntry } from "@/app/features/actions";
import { ExperienceShell, Panel, buttonClass, fieldClass } from "@/components/experience-shell";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Diário" };
export const dynamic = "force-dynamic";

export default async function DiaryPage() {
  const entries = await experienceApi.diary(await requireAccessToken());
  return (
    <ExperienceShell eyebrow="Fase 4 · Diary" title="Diário de filmes">
      <div className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <Panel>
          <h2 className="font-serif text-2xl text-white">Registrar sessão</h2>
          <form action={addDiaryEntry} className="mt-5 space-y-4">
            <label className="block text-sm text-zinc-300">TMDB ID<input className={fieldClass} name="tmdb_id" inputMode="numeric" required /></label>
            <label className="block text-sm text-zinc-300">Data<input className={fieldClass} name="watched_at" type="date" required /></label>
            <label className="block text-sm text-zinc-300">Notas<textarea className={fieldClass} maxLength={2000} name="notes" rows={4} /></label>
            <label className="flex gap-2 text-sm text-zinc-300"><input name="rewatch" type="checkbox" /> Reassistido</label>
            <button className={buttonClass} type="submit">Adicionar ao diário</button>
          </form>
        </Panel>
        <div className="space-y-4">
          {entries.length ? entries.map((entry) => (
            <Panel key={entry.id}>
              <div className="flex items-start justify-between gap-4">
                <div><p className="text-xs text-amber-200">{entry.watched_at}{entry.rewatch ? " · rewatch" : ""}</p><h2 className="mt-2 font-serif text-2xl text-white">{entry.title ?? `Filme #${entry.tmdb_id}`}</h2></div>
                <span className="text-xs text-zinc-600">TMDB {entry.tmdb_id}</span>
              </div>
              {entry.notes ? <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-zinc-400">{entry.notes}</p> : null}
            </Panel>
          )) : <Panel><p className="text-zinc-400">Nenhuma sessão registrada ainda.</p></Panel>}
        </div>
      </div>
    </ExperienceShell>
  );
}
