import "server-only";

import { z } from "zod";

const profileSchema = z.object({
  id: z.string().uuid(),
  username: z.string(),
  display_name: z.string(),
  avatar_url: z.string().url().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type Profile = z.infer<typeof profileSchema>;

function backendBase(): string {
  const configured = process.env.BACKEND_URL;
  if (configured) return configured.replace(/\/$/, "");
  const host = process.env.VERCEL_URL ?? process.env.VERCEL_PROJECT_PRODUCTION_URL;
  return host ? `https://${host}/api/backend` : "http://localhost:3000/api/backend";
}

async function profileRequest(
  accessToken: string,
  init?: { method: "POST"; body: { username: string; display_name: string } },
): Promise<Profile | null> {
  const response = await fetch(`${backendBase()}/me`, {
    method: init?.method ?? "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init ? { "Content-Type": "application/json" } : {}),
    },
    body: init ? JSON.stringify(init.body) : undefined,
    cache: "no-store",
    signal: AbortSignal.timeout(8_000),
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`profile_request_failed:${response.status}`);
  return profileSchema.parse(await response.json());
}

export function getProfile(accessToken: string): Promise<Profile | null> {
  return profileRequest(accessToken);
}

export function createProfile(
  accessToken: string,
  profile: { username: string; display_name: string },
): Promise<Profile | null> {
  return profileRequest(accessToken, { method: "POST", body: profile });
}
