import type { EmailOtpType } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

import { createSupabaseServerClient } from "@/lib/supabase/server";

const allowedOtpTypes = new Set<EmailOtpType>([
  "email",
  "signup",
  "invite",
  "magiclink",
  "recovery",
  "email_change",
]);

function loginRedirect(origin: string, error: string): NextResponse {
  return NextResponse.redirect(
    new URL(`/login?error=${encodeURIComponent(error)}`, origin),
  );
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const callbackError =
    url.searchParams.get("error_code") ?? url.searchParams.get("error");

  if (callbackError) {
    console.warn("Supabase auth callback rejected", { code: callbackError });
    return loginRedirect(
      url.origin,
      callbackError === "otp_expired" ? "confirmation_expired" : "confirmation",
    );
  }

  const supabase = await createSupabaseServerClient();
  const code = url.searchParams.get("code");
  const tokenHash = url.searchParams.get("token_hash");
  const rawType = url.searchParams.get("type");

  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      console.warn("Supabase auth code exchange failed", {
        code: error.code,
        status: error.status,
      });
      return loginRedirect(url.origin, "confirmation");
    }
    return NextResponse.redirect(new URL("/account", url.origin));
  }

  if (
    tokenHash &&
    rawType &&
    allowedOtpTypes.has(rawType as EmailOtpType)
  ) {
    const { error } = await supabase.auth.verifyOtp({
      token_hash: tokenHash,
      type: rawType as EmailOtpType,
    });
    if (error) {
      console.warn("Supabase auth token verification failed", {
        code: error.code,
        status: error.status,
      });
      return loginRedirect(
        url.origin,
        error.code === "otp_expired" ? "confirmation_expired" : "confirmation",
      );
    }
    return NextResponse.redirect(new URL("/account", url.origin));
  }

  console.warn("Supabase auth callback missing exchange parameters");
  return loginRedirect(url.origin, "confirmation");
}
