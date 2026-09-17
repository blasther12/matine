"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  deleteLibraryMovie,
  saveLibraryMovie as saveLibraryMovieRequest,
  type LibraryStatus,
} from "@/lib/backend.server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

const validStatuses = new Set<LibraryStatus>(["WATCHLIST", "WATCHED", "DROPPED"]);

function tmdbId(formData: FormData): number | null {
  const raw = formData.get("tmdb_id");
  if (typeof raw !== "string" || !/^\d{1,10}$/.test(raw)) return null;
  const value = Number(raw);
  return Number.isSafeInteger(value) && value > 0 && value <= 2_147_483_647 ? value : null;
}

async function accessToken(): Promise<string> {
  const supabase = await createSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  if (!data.session) redirect("/login");
  return data.session.access_token;
}

export async function saveLibraryMovie(formData: FormData): Promise<void> {
  const id = tmdbId(formData);
  const statusValue = formData.get("status");
  const ratingValue = formData.get("rating");
  if (id === null || typeof statusValue !== "string" || !validStatuses.has(statusValue as LibraryStatus)) {
    return;
  }
  const rating = ratingValue === "" || ratingValue === null ? null : Number(ratingValue);
  if (rating !== null && (!Number.isFinite(rating) || rating < 0.5 || rating > 5 || rating * 2 % 1 !== 0)) {
    return;
  }

  await saveLibraryMovieRequest(await accessToken(), id, {
    status: statusValue as LibraryStatus,
    rating,
    favorite: formData.get("favorite") === "on",
  });
  revalidatePath(`/movie/${id}`);
  revalidatePath("/library");
}

export async function removeLibraryMovie(formData: FormData): Promise<void> {
  const id = tmdbId(formData);
  if (id === null) return;
  await deleteLibraryMovie(await accessToken(), id);
  revalidatePath(`/movie/${id}`);
  revalidatePath("/library");
}
