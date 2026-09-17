import type { Metadata } from "next";
import Link from "next/link";

import {
  resendConfirmation,
  signIn,
  signUp,
} from "@/app/auth/actions";

export const metadata: Metadata = { title: "Entrar" };

type Props = {
  searchParams: Promise<{ error?: string; status?: string }>;
};

function errorMessage(error?: string): string | null {
  if (!error) return null;
  if (error === "email_not_confirmed") {
    return "Seu e-mail ainda não foi confirmado. Confirme pelo link enviado pelo Supabase ou reenvie a confirmação abaixo.";
  }
  if (error === "email_address_invalid") {
    return "O Supabase recusou esse endereço de e-mail.";
  }
  if (error === "email_provider_disabled") {
    return "Cadastro por e-mail está desabilitado no Supabase.";
  }
  if (error === "signup_disabled") {
    return "Novos cadastros estão desabilitados no Supabase.";
  }
  if (error === "over_email_send_rate_limit" || error === "over_request_rate_limit") {
    return "O Supabase bloqueou novas tentativas temporariamente por limite de requisições ou e-mails. Aguarde alguns minutos e tente novamente.";
  }
  if (error === "user_already_exists") {
    return "Já existe uma conta com esse e-mail. Tente entrar ou reenviar a confirmação.";
  }
  if (error === "credentials") {
    return "E-mail ou senha inválidos.";
  }
  if (error === "resend") {
    return "Não foi possível reenviar a confirmação agora. Tente novamente em instantes.";
  }
  if (error === "invalid") {
    return "Preencha um e-mail válido e use uma senha com pelo menos 8 caracteres.";
  }
  return "Não foi possível concluir. Confira os dados e tente novamente.";
}

export default async function LoginPage({ searchParams }: Props) {
  const state = await searchParams;
  const message = errorMessage(state.error);

  return (
    <main className="cinema-grid grid min-h-screen place-items-center px-5 py-12">
      <section className="w-full max-w-4xl rounded-3xl border border-white/10 bg-zinc-950/85 p-6 shadow-2xl backdrop-blur-xl sm:p-10">
        <Link
          className="text-sm text-amber-200 hover:text-amber-100"
          href="/"
        >
          ← Voltar à Matinê
        </Link>

        <div className="mt-7 grid gap-10 md:grid-cols-2">
          <AuthForm
            action={signIn}
            title="Entrar"
            submit="Acessar minha conta"
          />
          <AuthForm
            action={signUp}
            title="Criar conta"
            submit="Começar minha Matinê"
          />
        </div>

        {message ? (
          <p
            role="alert"
            className="mt-7 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-200"
          >
            {message}
          </p>
        ) : null}

        {state.status === "confirm-email" ? (
          <p
            role="status"
            className="mt-7 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-200"
          >
            Conta criada. Confira seu e-mail para confirmar a conta antes de entrar.
          </p>
        ) : null}

        {state.status === "confirmation-resent" ? (
          <p
            role="status"
            className="mt-7 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-200"
          >
            E-mail de confirmação reenviado. Confira também a caixa de spam.
          </p>
        ) : null}

        <form
          action={resendConfirmation}
          className="mt-8 rounded-2xl border border-white/10 bg-white/[0.03] p-5"
        >
          <p className="text-sm font-semibold text-zinc-100">
            Não recebeu o e-mail de confirmação?
          </p>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <input
              className="min-w-0 flex-1 rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-amber-300"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="seu@email.com"
              required
            />
            <button
              className="rounded-xl border border-amber-300/30 px-4 py-3 text-sm font-semibold text-amber-100 transition hover:bg-amber-300/10"
              type="submit"
            >
              Reenviar confirmação
            </button>
          </div>
        </form>
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
        <p className="mt-2 text-sm leading-6 text-zinc-400">
          Autenticação protegida pelo Supabase.
        </p>
      </div>

      <label className="block text-sm text-zinc-300">
        E-mail
        <input
          className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-amber-300"
          name="email"
          type="email"
          autoComplete="email"
          required
        />
      </label>

      <label className="block text-sm text-zinc-300">
        Senha
        <input
          className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white outline-none focus:border-amber-300"
          name="password"
          type="password"
          autoComplete={title === "Entrar" ? "current-password" : "new-password"}
          minLength={8}
          required
        />
      </label>

      <button
        className="w-full rounded-xl bg-amber-300 px-4 py-3 font-semibold text-zinc-950 transition hover:bg-amber-200"
        type="submit"
      >
        {submit}
      </button>
    </form>
  );
}
