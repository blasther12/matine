import type { Metadata } from "next";

import { saveReview } from "@/app/features/actions";
import { ExperienceShell, Panel, buttonClass, fieldClass } from "@/components/experience-shell";
import { requireAccessToken } from "@/lib/auth.server";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Reviews" };
export const dynamic = "force-dynamic";

export default async function ReviewsPage() {
  const items = await experienceApi.reviews(await requireAccessToken());
  return (
    <ExperienceShell eyebrow="Fase 5 · Reviews" title="Suas reviews">
      <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <Panel>
          <h2 className="font-serif text-2xl text-white">Escrever ou editar</h2>
          <form action={saveReview} className="mt-5 space-y-4">
            <label className="block text-sm text-zinc-300">TMDB ID<input className={fieldClass} name="tmdb_id" required /></label>
            <label className="block text-sm text-zinc-300">Review<textarea className={fieldClass} maxLength={5000} minLength={1} name="body" rows={6} required /></label>
            <label className="block text-sm text-zinc-300">Visibilidade<select className={fieldClass} defaultValue="PRIVATE" name="visibility"><option value="PRIVATE">Privada</option><option value="FOLLOWERS">Seguidores</option><option value="PUBLIC">Pública</option></select></label>
            <label className="flex gap-2 text-sm text-zinc-300"><input name="spoiler" type="checkbox" /> Contém spoiler</label>
            <button className={buttonClass} type="submit">Salvar review</button>
          </form>
        </Panel>
        <div className="space-y-4">
          {items.length ? items.map((review) => (
            <Panel key={review.id}>
              <p className="text-xs text-amber-200">{review.visibility}{review.spoiler ? " · SPOILER" : ""}</p>
              <h2 className="mt-2 font-serif text-2xl text-white">{review.title ?? `Filme #${review.tmdb_id}`}</h2>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-zinc-300">{review.body}</p>
            </Panel>
          )) : <Panel><p className="text-zinc-400">Você ainda não escreveu nenhuma review.</p></Panel>}
        </div>
      </div>
    </ExperienceShell>
  );
}
