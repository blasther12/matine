import type { Metadata } from "next";

import { addMovieListItem, createMovieList } from "@/app/features/actions";
import { ExperienceShell, Panel, buttonClass, fieldClass } from "@/components/experience-shell";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Listas" };
export const dynamic = "force-dynamic";

export default async function ListsPage() {
  const lists = await experienceApi.lists(await requireAccessToken());
  return (
    <ExperienceShell eyebrow="Fase 6 · Lists" title="Listas de filmes">
      <Panel>
        <form action={createMovieList} className="grid gap-3 md:grid-cols-[1fr_1.4fr_0.7fr_auto] md:items-end">
          <label className="text-sm text-zinc-300">Nome<input className={fieldClass} maxLength={100} name="name" required /></label>
          <label className="text-sm text-zinc-300">Descrição<input className={fieldClass} maxLength={1000} name="description" /></label>
          <label className="text-sm text-zinc-300">Visibilidade<select className={fieldClass} name="visibility" defaultValue="PRIVATE"><option value="PRIVATE">Privada</option><option value="PUBLIC">Pública</option></select></label>
          <button className={buttonClass} type="submit">Criar lista</button>
        </form>
      </Panel>
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        {lists.length ? lists.map((list) => (
          <Panel key={list.id}>
            <p className="text-xs text-amber-200">{list.visibility}</p>
            <h2 className="mt-2 font-serif text-3xl text-white">{list.name}</h2>
            {list.description ? <p className="mt-2 text-sm text-zinc-400">{list.description}</p> : null}
            <ol className="mt-5 space-y-2 text-sm text-zinc-300">
              {list.items.map((item) => <li key={item.tmdb_id}>{item.position + 1}. {item.title ?? `Filme #${item.tmdb_id}`}{item.note ? ` · ${item.note}` : ""}</li>)}
            </ol>
            <form action={addMovieListItem} className="mt-5 grid gap-2 sm:grid-cols-4">
              <input name="list_id" type="hidden" value={list.id} />
              <input className={fieldClass} name="tmdb_id" placeholder="TMDB ID" required />
              <input className={fieldClass} defaultValue={list.items.length} min={0} name="position" type="number" required />
              <input className={fieldClass} name="note" placeholder="Nota opcional" />
              <button className={buttonClass} type="submit">Adicionar</button>
            </form>
          </Panel>
        )) : <Panel><p className="text-zinc-400">Nenhuma lista criada.</p></Panel>}
      </div>
    </ExperienceShell>
  );
}
