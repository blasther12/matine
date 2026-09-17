import type { Metadata } from "next";
import Link from "next/link";

import { signIn, signUp } from "@/app/auth/actions";

export const metadata: Metadata = { title: "Entrar" };

type Props = { searchParams: Promise<{ error?: string; status?: string }> };

export default async function LoginPage({ searchParams }: Props) {
  const state = await searchParams;
  return (
    <main className="cinema-grid grid min-h-screen place-items-center px-5 py-12">
      <section className="w-full max-w-4xl rounded-3xl border border-white/10 bg-zinc-950/85 p-6 shadow-2xl backdrop-blur-xl sm:p-10">
        <Link className="text-sm text-amber-200 hover:text-amber-100" href="/">
          ← Voltar à Matinê
        </Link>
        <div className="mt-7 grid gap-10 md:grid-cols-2">
          <AuthForm action={signIn} title="Entrar" submit="Acessar minha conta" />
          <AuthForm action={signUp} title="Criar conta" submit="Começar minha Matinê" />
        </div>
        {state.error ? (
          <p role="alert" className="mt-7 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-200">
            Não foi possível concluir. Confira os dados e tente novamente.
          </p>
        ) : null}
        {state.status === "confirm-email" ? (
          <p role="status" className="mt-7 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-200">
            Confira seu e-mail para confirmar a conta. A Matinê não armazena sua senha.
          </p>
        ) : null}
      </section>
    </main>
  );
}

function AuthForm({
  action,
  title,
  submit,
}: {
  action: (formData: FormData) => Promise<never>;
  title: string;
  submit: string;
}) {
  return (
    <form action={action} className="space-y-5">
      <div>
        <p className="font-serif text-3xl text-white">{title}</p>
        <p className="mt-2 text-sm leading-6 text-zinc-400">Autenticação protegida pelo Supabase.</p>
      </div>
      <label className="block text-sm text-zinc-300">
        E-mail
        <input className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-amber-300" name="email" type="email" autoComplete="email" required />
      </label>
      <label className="block text-sm text-zinc-300">
        Senha
        <input className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-amber-300" name="password" type="password" autoComplete={title === "Entrar" ? "current-password" : "new-password"} minLength={8} required />
      </label>
      <button className="w-full rounded-xl bg-amber-300 px-4 py-3 font-semibold text-zinc-950 transition hover:bg-amber-200" type="submit">{submit}</button>
    </form>
  );
}
