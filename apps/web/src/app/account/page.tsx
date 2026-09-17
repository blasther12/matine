import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { finishProfile, signOut } from "@/app/auth/actions";
import { getProfile } from "@/lib/backend.server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Minha conta" };

type Props = { searchParams: Promise<{ error?: string }> };

export default async function AccountPage({ searchParams }: Props) {
  const supabase = await createSupabaseServerClient();
  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) redirect("/login");
  const { data: sessionData } = await supabase.auth.getSession();
  if (!sessionData.session) redirect("/login");

  let profile = null;
  try {
    profile = await getProfile(sessionData.session.access_token);
  } catch {
    // The page still offers a safe retry after transient backend failures.
  }
  const state = await searchParams;

  return (
    <main className="cinema-grid min-h-screen px-5 py-12">
      <section className="mx-auto max-w-3xl rounded-3xl border border-white/10 bg-zinc-950/85 p-6 shadow-2xl sm:p-10">
        <div className="flex items-center justify-between gap-4">
          <Link className="text-sm text-amber-200 hover:text-amber-100" href="/">← Início</Link>
          <form action={signOut}><button className="text-sm text-zinc-400 hover:text-white" type="submit">Sair</button></form>
        </div>
        {profile ? (
          <div className="mt-10">
            <p className="font-mono text-xs tracking-[0.2em] text-amber-200 uppercase">Perfil privado</p>
            <h1 className="mt-3 font-serif text-5xl text-white">{profile.display_name}</h1>
            <p className="mt-3 text-zinc-400">@{profile.username}</p>
            <p className="mt-8 rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-zinc-300">Sua conta está pronta. Biblioteca, diário e avaliações são vinculados somente a este perfil interno.</p>
            <Link className="mt-6 inline-flex rounded-xl bg-amber-300 px-5 py-3 font-semibold text-zinc-950" href="/library">Abrir minha biblioteca</Link>
          </div>
        ) : (
          <form action={finishProfile} className="mt-10 space-y-5">
            <div><p className="font-mono text-xs tracking-[0.2em] text-amber-200 uppercase">Primeiro acesso</p><h1 className="mt-3 font-serif text-4xl text-white">Crie seu perfil privado</h1></div>
            <label className="block text-sm text-zinc-300">Nome de usuário<input className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white" name="username" pattern="[a-zA-Z0-9_]{3,30}" minLength={3} maxLength={30} required /></label>
            <label className="block text-sm text-zinc-300">Nome de exibição<input className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white" name="display_name" minLength={1} maxLength={80} required /></label>
            <button className="rounded-xl bg-amber-300 px-5 py-3 font-semibold text-zinc-950" type="submit">Salvar perfil</button>
            {state.error ? <p role="alert" className="text-sm text-red-200">Nome indisponível ou serviço temporariamente indisponível.</p> : null}
          </form>
        )}
      </section>
    </main>
  );
}
