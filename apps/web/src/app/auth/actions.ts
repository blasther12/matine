"use server";

import { redirect } from "next/navigation";

import { createProfile } from "@/lib/backend.server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

function text(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

function siteUrl(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL;
  if (configured) return new URL(configured).origin;
  const host = process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
  return host ? `https://${host}` : "http://localhost:3000";
}

export async function signIn(formData: FormData): Promise<never> {
  const email = text(formData, "email");
  const password = text(formData, "password");
  if (!email || password.length < 8) redirect("/login?error=invalid");

  const supabase = await createSupabaseServerClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) redirect("/login?error=credentials");
  redirect("/account");
}

export async function signUp(formData: FormData): Promise<never> {
  const email = text(formData, "email");
  const password = text(formData, "password");
  if (!email || password.length < 8) redirect("/login?error=invalid");

  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: `${siteUrl()}/auth/callback` },
  });
  if (error) redirect("/login?error=signup");
  redirect(data.session ? "/account" : "/login?status=confirm-email");
}

export async function signOut(): Promise<never> {
  const supabase = await createSupabaseServerClient();
  await supabase.auth.signOut();
  redirect("/");
}

export async function finishProfile(formData: FormData): Promise<never> {
  const username = text(formData, "username").toLowerCase();
  const displayName = text(formData, "display_name");
  if (!/^[a-z0-9_]{3,30}$/.test(username) || !displayName || displayName.length > 80) {
    redirect("/account?error=profile");
  }

  const supabase = await createSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  if (!data.session) redirect("/login");
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
