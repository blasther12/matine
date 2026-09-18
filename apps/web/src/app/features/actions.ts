"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { experienceApi } from "@/lib/experience.server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

function text(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

function positiveInt(value: string): number | null {
  if (!/^\d{1,10}$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}

async function token(): Promise<string> {
  const supabase = await createSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  if (!data.session) redirect("/login");
  return data.session.access_token;
}

export async function addDiaryEntry(formData: FormData): Promise<void> {
  const tmdbId = positiveInt(text(formData, "tmdb_id"));
  const watchedAt = text(formData, "watched_at");
  if (tmdbId === null || !/^\d{4}-\d{2}-\d{2}$/.test(watchedAt)) return;
  await experienceApi.addDiary(await token(), {
    tmdb_id: tmdbId,
    watched_at: watchedAt,
    rewatch: formData.get("rewatch") === "on",
    notes: text(formData, "notes") || null,
  });
  revalidatePath("/diary");
}

export async function saveReview(formData: FormData): Promise<void> {
  const tmdbId = positiveInt(text(formData, "tmdb_id"));
  const body = text(formData, "body");
  const visibility = text(formData, "visibility");
  if (
    tmdbId === null ||
    !body ||
    !["PRIVATE", "FOLLOWERS", "PUBLIC"].includes(visibility)
  ) return;
  await experienceApi.saveReview(await token(), {
    tmdb_id: tmdbId,
    body,
    spoiler: formData.get("spoiler") === "on",
    visibility,
  });
  revalidatePath("/reviews");
  revalidatePath("/social");
}

export async function createMovieList(formData: FormData): Promise<void> {
  const name = text(formData, "name");
  const visibility = text(formData, "visibility");
  if (!name || !["PRIVATE", "PUBLIC"].includes(visibility)) return;
  await experienceApi.createList(await token(), {
    name,
    description: text(formData, "description") || null,
    visibility,
  });
  revalidatePath("/lists");
}

export async function addMovieListItem(formData: FormData): Promise<void> {
  const listId = text(formData, "list_id");
  const tmdbId = positiveInt(text(formData, "tmdb_id"));
  const position = Number(text(formData, "position"));
  if (
    !/^[0-9a-f-]{36}$/i.test(listId) ||
    tmdbId === null ||
    !Number.isInteger(position) ||
    position < 0
  ) return;
  await experienceApi.addListItem(await token(), listId, {
    tmdb_id: tmdbId,
    position,
    note: text(formData, "note") || null,
  });
  revalidatePath("/lists");
}

export async function followUser(formData: FormData): Promise<void> {
  const username = text(formData, "username").toLowerCase();
  if (!/^[a-z0-9_]{3,30}$/.test(username)) return;
  await experienceApi.follow(await token(), { username });
  revalidatePath("/social");
}

export async function saveStreamingPreferences(formData: FormData): Promise<void> {
  const providers = text(formData, "providers")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .slice(0, 20);
  await experienceApi.saveStreaming(await token(), { providers });
  revalidatePath("/streaming");
}

export async function createCircle(formData: FormData): Promise<void> {
  const name = text(formData, "name");
  if (!name) return;
  const circle = await experienceApi.createCircle(await token(), { name });
  redirect(`/circles?circle=${circle.id}`);
}

export async function addCircleMember(formData: FormData): Promise<void> {
  const circleId = text(formData, "circle_id");
  const username = text(formData, "username").toLowerCase();
  if (!/^[0-9a-f-]{36}$/i.test(circleId) || !/^[a-z0-9_]{3,30}$/.test(username)) return;
  await experienceApi.addCircleMember(await token(), circleId, { username });
  revalidatePath("/circles");
}

export async function createMovieNight(formData: FormData): Promise<void> {
  const circleId = text(formData, "circle_id");
  const title = text(formData, "title");
  const runtimeRaw = text(formData, "max_runtime_minutes");
  const runtime = runtimeRaw ? Number(runtimeRaw) : null;
  const preferredGenres = text(formData, "preferred_genres")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .slice(0, 5);

  if (
    !/^[0-9a-f-]{36}$/i.test(circleId) ||
    !title ||
    (runtime !== null &&
      (!Number.isInteger(runtime) || runtime < 30 || runtime > 600))
  ) return;

  const night = await experienceApi.createNight(await token(), circleId, {
    title,
    max_runtime_minutes: runtime,
    preferred_genres: preferredGenres,
  });
  redirect(`/circles?circle=${circleId}&night=${night.id}`);
}

export async function addMovieNightCandidate(formData: FormData): Promise<void> {
  const nightId = text(formData, "night_id");
  const tmdbId = positiveInt(text(formData, "tmdb_id"));
  if (!/^[0-9a-f-]{36}$/i.test(nightId) || tmdbId === null) return;
  await experienceApi.addCandidate(await token(), nightId, { tmdb_id: tmdbId });
  revalidatePath("/circles");
}

export async function voteMovieNight(formData: FormData): Promise<void> {
  const nightId = text(formData, "night_id");
  const tmdbId = positiveInt(text(formData, "tmdb_id"));
  if (!/^[0-9a-f-]{36}$/i.test(nightId) || tmdbId === null) return;
  await experienceApi.vote(await token(), nightId, { tmdb_id: tmdbId });
  revalidatePath("/circles");
}


export async function vetoMovieNightCandidate(formData: FormData): Promise<void> {
  const nightId = text(formData, "night_id");
  const tmdbId = positiveInt(text(formData, "tmdb_id"));
  if (!/^[0-9a-f-]{36}$/i.test(nightId) || tmdbId === null) return;
  await experienceApi.veto(await token(), nightId, { tmdb_id: tmdbId });
  revalidatePath("/circles");
}

export async function removeMovieNightVeto(formData: FormData): Promise<void> {
  const nightId = text(formData, "night_id");
  const tmdbId = positiveInt(text(formData, "tmdb_id"));
  if (!/^[0-9a-f-]{36}$/i.test(nightId) || tmdbId === null) return;
  await experienceApi.removeVeto(await token(), nightId, { tmdb_id: tmdbId });
  revalidatePath("/circles");
}
