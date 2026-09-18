import type { Metadata } from "next";

import { saveStreamingPreferences } from "@/app/features/actions";
import { ExperienceShell, Panel, buttonClass, fieldClass } from "@/components/experience-shell";
import { SubmitButton } from "@/components/ui/submit-button";
import { requireAccessToken } from "@/lib/auth.server";
import { getMovieProviders } from "@/lib/api";
import { experienceApi } from "@/lib/experience.server";

export const metadata: Metadata = { title: "Streaming" };
export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ tmdb_id?: string }> };

export default async function StreamingPage({ searchParams }: Props) {
  const token = await requireAccessToken();
  const preferences = await experienceApi.streaming(token);
  const raw = (await searchParams).tmdb_id ?? "";
  const tmdbId = /^\d{1,10}$/.test(raw) ? Number(raw) : null;
  const providers = tmdbId ? await getMovieProviders(tmdbId).catch(() => null) : null;
  const available = providers ? [...providers.streaming, ...providers.free, ...providers.ads, ...providers.rent, ...providers.buy] : [];
  const preferred = new Set(preferences.providers.map((value) => value.toLocaleLowerCase("pt-BR")));
  const matches = available.filter((provider) => preferred.has(provider.name.toLocaleLowerCase("pt-BR")));

  return (
    <ExperienceShell eyebrow="Fase 8 · Streaming" title="Onde você assiste">
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <form action={saveStreamingPreferences} className="space-y-4">
            <label className="block text-sm text-zinc-300">Serviços que você usa, separados por vírgula<input className={fieldClass} defaultValue={preferences.providers.join(", ")} name="providers" placeholder="Netflix, Prime Video, Max" /></label>
            <SubmitButton className="rounded-xl" pendingLabel="Salvando...">Salvar preferências</SubmitButton>
          </form>
          <p className="mt-4 text-xs leading-5 text-zinc-500">Escolha manual. O Matinê não infere suas assinaturas nem dados de cobrança.</p>
        </Panel>
        <Panel>
          <form className="flex gap-3" method="get">
            <input className={fieldClass} name="tmdb_id" placeholder="TMDB ID para conferir" defaultValue={raw} />
            <button className={buttonClass} type="submit">Filtrar</button>
          </form>
          {providers ? <div className="mt-5"><p className="text-sm text-zinc-300">Compatíveis com suas preferências: {matches.length ? matches.map((item) => item.name).join(", ") : "nenhum"}</p><p className="mt-3 text-xs text-zinc-500">Disponibilidade BR via JustWatch/TMDB.</p></div> : null}
        </Panel>
      </div>
    </ExperienceShell>
  );
}
