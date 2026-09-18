import "server-only";

import { z } from "zod";

const diarySchema = z.object({
  id: z.string().uuid(),
  tmdb_id: z.number().int(),
  watched_at: z.string(),
  rewatch: z.boolean(),
  notes: z.string().nullable(),
  title: z.string().nullable().optional(),
  poster_path: z.string().nullable().optional(),
  created_at: z.string(),
});

const reviewSchema = z.object({
  id: z.string().uuid(),
  username: z.string(),
  tmdb_id: z.number().int(),
  title: z.string().nullable().optional(),
  body: z.string(),
  spoiler: z.boolean(),
  visibility: z.enum(["PRIVATE", "FOLLOWERS", "PUBLIC"]),
  created_at: z.string(),
  updated_at: z.string(),
});

const listItemSchema = z.object({
  tmdb_id: z.number().int(),
  position: z.number().int(),
  note: z.string().nullable(),
  title: z.string().nullable().optional(),
  poster_path: z.string().nullable().optional(),
});

const movieListSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().nullable(),
  visibility: z.enum(["PRIVATE", "PUBLIC"]),
  items: z.array(listItemSchema),
  created_at: z.string(),
  updated_at: z.string(),
});

const feedItemSchema = z.object({
  username: z.string(),
  tmdb_id: z.number().int(),
  title: z.string().nullable(),
  body: z.string(),
  spoiler: z.boolean(),
  created_at: z.string(),
});

const streamingSchema = z.object({ providers: z.array(z.string()) });

const circleSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  role: z.string(),
  member_count: z.number().int(),
  created_at: z.string(),
});

const matchSchema = z.object({
  tmdb_id: z.number().int(),
  title: z.string().nullable(),
  poster_path: z.string().nullable(),
  interested_members: z.number().int(),
  member_count: z.number().int(),
  score: z.number(),
  reason: z.string(),
});

const recommendationSchema = z.object({
  tmdb_id: z.number().int(),
  title: z.string().nullable(),
  poster_path: z.string().nullable(),
  score: z.number(),
  reasons: z.array(z.string()),
});

const statsSchema = z.object({
  library_total: z.number().int(),
  watchlist_total: z.number().int(),
  watched_total: z.number().int(),
  dropped_total: z.number().int(),
  favorite_total: z.number().int(),
  diary_total: z.number().int(),
  review_total: z.number().int(),
  list_total: z.number().int(),
  average_rating: z.number().nullable(),
});

const wrappedSchema = z.object({
  year: z.number().int(),
  watches: z.number().int(),
  distinct_movies: z.number().int(),
  rewatches: z.number().int(),
  reviews: z.number().int(),
  top_movie_tmdb_id: z.number().int().nullable(),
  top_movie_title: z.string().nullable(),
});

const nightSchema = z.object({
  id: z.string().uuid(),
  circle_id: z.string().uuid(),
  title: z.string(),
  status: z.string(),
  results: z.array(z.object({
    tmdb_id: z.number().int(),
    title: z.string().nullable(),
    votes: z.number().int(),
  })),
  created_at: z.string(),
});

export type DiaryEntry = z.infer<typeof diarySchema>;
export type Review = z.infer<typeof reviewSchema>;
export type MovieList = z.infer<typeof movieListSchema>;
export type FeedItem = z.infer<typeof feedItemSchema>;
export type Circle = z.infer<typeof circleSchema>;
export type MatchItem = z.infer<typeof matchSchema>;
export type Recommendation = z.infer<typeof recommendationSchema>;
export type Stats = z.infer<typeof statsSchema>;
export type Wrapped = z.infer<typeof wrappedSchema>;
export type MovieNight = z.infer<typeof nightSchema>;

function backendBase(): string {
  const host = process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
  return host ? `https://${host}/api/backend` : "http://localhost:3000/api/backend";
}

async function request<T>(
  token: string,
  path: string,
  schema: z.ZodType<T>,
  init?: { method?: "POST"; body?: unknown },
): Promise<T> {
  const response = await fetch(`${backendBase()}${path}`, {
    method: init?.method ?? "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: init?.body === undefined ? undefined : JSON.stringify(init.body),
    cache: "no-store",
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) {
    throw new Error(`experience_request_failed:${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return schema.parse(await response.json());
}

const nothing = z.undefined();

export const experienceApi = {
  diary: (token: string) => request(token, "/me/diary", z.array(diarySchema)),
  addDiary: (token: string, body: unknown) =>
    request(token, "/me/diary", diarySchema, { method: "POST", body }),
  reviews: (token: string) => request(token, "/me/reviews", z.array(reviewSchema)),
  saveReview: (token: string, body: unknown) =>
    request(token, "/me/reviews", reviewSchema, { method: "POST", body }),
  lists: (token: string) => request(token, "/me/lists", z.array(movieListSchema)),
  createList: (token: string, body: unknown) =>
    request(token, "/me/lists", movieListSchema, { method: "POST", body }),
  addListItem: (token: string, listId: string, body: unknown) =>
    request(token, `/me/lists/${listId}/items`, nothing, { method: "POST", body }),
  follow: (token: string, body: unknown) =>
    request(token, "/social/follow", nothing, { method: "POST", body }),
  feed: (token: string) => request(token, "/social/feed", z.array(feedItemSchema)),
  streaming: (token: string) => request(token, "/me/streaming", streamingSchema),
  saveStreaming: (token: string, body: unknown) =>
    request(token, "/me/streaming", streamingSchema, { method: "POST", body }),
  circles: (token: string) => request(token, "/me/circles", z.array(circleSchema)),
  createCircle: (token: string, body: unknown) =>
    request(token, "/me/circles", circleSchema, { method: "POST", body }),
  addCircleMember: (token: string, circleId: string, body: unknown) =>
    request(token, `/me/circles/${circleId}/members`, nothing, { method: "POST", body }),
  match: (token: string, circleId: string) =>
    request(token, `/me/circles/${circleId}/match`, z.array(matchSchema)),
  createNight: (token: string, circleId: string, body: unknown) =>
    request(token, `/me/circles/${circleId}/movie-nights`, nightSchema, { method: "POST", body }),
  addCandidate: (token: string, nightId: string, body: unknown) =>
    request(token, `/me/movie-nights/${nightId}/candidates`, nothing, { method: "POST", body }),
  vote: (token: string, nightId: string, body: unknown) =>
    request(token, `/me/movie-nights/${nightId}/vote`, nothing, { method: "POST", body }),
  night: (token: string, nightId: string) =>
    request(token, `/me/movie-nights/${nightId}`, nightSchema),
  recommendations: (token: string) =>
    request(token, "/me/recommendations", z.array(recommendationSchema)),
  stats: (token: string) => request(token, "/me/stats", statsSchema),
  wrapped: (token: string, year: number) =>
    request(token, `/me/wrapped?year=${encodeURIComponent(String(year))}`, wrappedSchema),
};
