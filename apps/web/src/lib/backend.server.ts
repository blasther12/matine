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

const libraryMovieSchema = z.object({
  tmdb_id: z.number().int().positive().max(2_147_483_647),
  status: z.enum(["WATCHLIST", "WATCHED", "DROPPED"]),
  rating: z.number().min(0.5).max(5).nullable(),
  favorite: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

const librarySchema = z.object({ items: z.array(libraryMovieSchema) });

export type LibraryMovie = z.infer<typeof libraryMovieSchema>;
export type LibraryStatus = LibraryMovie["status"];

function backendBase(): string {
  const configured = process.env.BACKEND_URL?.trim();
  if (configured) {
    const base = configured.replace(/\/$/, "");
    return base.endsWith("/api/backend") ? base : `${base}/api/backend`;
  }

  const host = process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
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
  if (response.status === 404 && !init) return null;
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

async function libraryRequest<T>(
  accessToken: string,
  path: string,
  schema: z.ZodType<T>,
  init?: { method: "POST" | "PATCH" | "DELETE"; body?: unknown },
): Promise<T | null> {
  const response = await fetch(`${backendBase()}${path}`, {
    method: init?.method ?? "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init?.body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: init?.body === undefined ? undefined : JSON.stringify(init.body),
    cache: "no-store",
    signal: AbortSignal.timeout(8_000),
  });
  if (response.status === 404) return null;
  if (response.status === 204) return null;
  if (!response.ok) throw new Error(`library_request_failed:${response.status}`);
  return schema.parse(await response.json());
}

export async function getLibrary(
  accessToken: string,
  status?: Extract<LibraryStatus, "WATCHLIST" | "WATCHED">,
): Promise<LibraryMovie[] | null> {
  const path = status === "WATCHLIST" ? "/me/watchlist" : status === "WATCHED" ? "/me/watched" : "/me/movies";
  const result = await libraryRequest(accessToken, path, librarySchema);
  return result?.items ?? null;
}

export function getLibraryMovie(
  accessToken: string,
  tmdbId: number,
): Promise<LibraryMovie | null> {
  return libraryRequest(accessToken, `/me/movies/${tmdbId}`, libraryMovieSchema);
}

export function saveLibraryMovie(
  accessToken: string,
  tmdbId: number,
  movie: { status: LibraryStatus; rating: number | null; favorite: boolean },
): Promise<LibraryMovie | null> {
  return libraryRequest(accessToken, `/me/movies/${tmdbId}`, libraryMovieSchema, {
    method: "POST",
    body: movie,
  });
}

export function deleteLibraryMovie(accessToken: string, tmdbId: number): Promise<null> {
  return libraryRequest(accessToken, `/me/movies/${tmdbId}`, z.never(), {
    method: "DELETE",
  });
}
