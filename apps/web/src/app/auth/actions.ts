"use server";

import { redirect } from "next/navigation";

import { createProfile } from "@/lib/backend.server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

function text(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

function siteUrl(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configured) return new URL(configured).origin;

  const host =
    process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
  return host ? `https://${host}` : "http://localhost:3000";
}

function authErrorCode(
  code: string | undefined,
  fallback: string,
): string {
  const allowed = new Set([
    "email_not_confirmed",
    "email_address_invalid",
    "email_provider_disabled",
    "over_email_send_rate_limit",
    "over_request_rate_limit",
    "signup_disabled",
    "user_already_exists",
  ]);

  return code && allowed.has(code) ? code : fallback;
}

export async function signIn(formData: FormData): Promise<never> {
  const email = text(formData, "email");
  const password = text(formData, "password");

  if (!email || password.length < 8) {
    redirect("/login?error=invalid");
  }

  const supabase = await createSupabaseServerClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error?.code === "email_not_confirmed") {
    redirect("/login?error=email_not_confirmed");
  }

  if (error) {
    console.error("Supabase sign-in failed", {
      code: error.code,
      status: error.status,
    });
    redirect("/login?error=credentials");
  }

  redirect("/account");
}

export async function signUp(formData: FormData): Promise<never> {
  const email = text(formData, "email");
  const password = text(formData, "password");

  if (!email || password.length < 8) {
    redirect("/login?error=invalid");
  }

  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${siteUrl()}/auth/callback`,
    },
  });

  if (error) {
    console.error("Supabase sign-up failed", {
      code: error.code,
      status: error.status,
    });
    redirect(
      `/login?error=${encodeURIComponent(
        authErrorCode(error.code, "signup"),
      )}`,
    );
  }

  redirect(data.session ? "/account" : "/login?status=confirm-email");
}

export async function resendConfirmation(formData: FormData): Promise<never> {
  const email = text(formData, "email");

  if (!email) {
    redirect("/login?error=invalid");
  }

  const supabase = await createSupabaseServerClient();
  const { error } = await supabase.auth.resend({
    type: "signup",
    email,
    options: {
      emailRedirectTo: `${siteUrl()}/auth/callback`,
    },
  });

  if (error) {
    console.error("Supabase confirmation resend failed", {
      code: error.code,
      status: error.status,
    });
    redirect(
      `/login?error=${encodeURIComponent(
        authErrorCode(error.code, "resend"),
      )}`,
    );
  }

  redirect("/login?status=confirmation-resent");
}

export async function signOut(): Promise<never> {
  const supabase = await createSupabaseServerClient();
  await supabase.auth.signOut();
  redirect("/");
}

export async function finishProfile(formData: FormData): Promise<never> {
  const username = text(formData, "username").toLowerCase();
  const displayName = text(formData, "display_name");

  if (
    !/^[a-z0-9_]{3,30}$/.test(username) ||
    !displayName ||
    displayName.length > 80
  ) {
    redirect("/account?error=profile");
  }

  const supabase = await createSupabaseServerClient();
  const { data } = await supabase.auth.getSession();

  if (!data.session) {
    redirect("/login");
  }

  try {
    await createProfile(data.session.access_token, {
      username,
      display_name: displayName,
    });
  } catch {
    redirect("/account?error=profile");
  }

  redirect("/account");
}
