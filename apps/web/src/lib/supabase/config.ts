const DEFAULT_SUPABASE_URL = "https://gpizkywylfhdttecbzjn.supabase.co";
const DEFAULT_SUPABASE_PUBLISHABLE_KEY =
  "sb_publishable_wAez1j-30SDUHXLuOjS4Mw_at1FwFpP";

export function supabaseConfig(): { url: string; publishableKey: string } {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? DEFAULT_SUPABASE_URL;
  const publishableKey =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
    DEFAULT_SUPABASE_PUBLISHABLE_KEY;

  const parsed = new URL(url);
  if (parsed.protocol !== "https:" || parsed.username || parsed.password) {
    throw new Error("NEXT_PUBLIC_SUPABASE_URL must be a credential-free HTTPS URL");
  }

  return { url: parsed.origin, publishableKey };
}
