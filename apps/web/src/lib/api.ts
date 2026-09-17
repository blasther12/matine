import { z } from "zod";

const imagePathSchema = z.string().regex(/^\/[A-Za-z0-9._/-]+$/).nullable();

const tmdbAttributionSchema = z.object({
  source: z.literal("TMDB"),
  notice: z.string(),
});

const providerSchema = z.object({
  tmdb_provider_id: z.number().int().positive(),
  name: z.string(),
  logo_path: imagePathSchema,
  display_priority: z.number().int().nonnegative(),
});

export const movieSearchSchema = z.object({
  page: z.number().int().positive(),
  total_pages: z.number().int().nonnegative(),
  total_results: z.number().int().nonnegative(),
  results: z.array(
    z.object({
      tmdb_id: z.number().int().positive(),
      title: z.string(),
      original_title: z.string(),
      overview: z.string(),
      release_date: z.string().nullable(),
      year: z.number().int().nullable(),
      poster_path: imagePathSchema,
      vote_average: z.number().min(0).max(10),
    }),
  ),
  attribution: tmdbAttributionSchema,
});

export const movieDetailsSchema = z.object({
  tmdb_id: z.number().int().positive(),
  title: z.string(),
  original_title: z.string(),
  overview: z.string(),
  release_date: z.string().nullable(),
  year: z.number().int().nullable(),
  runtime_minutes: z.number().int().nonnegative().nullable(),
  poster_path: imagePathSchema,
  backdrop_path: imagePathSchema,
  vote_average: z.number().min(0).max(10),
  vote_count: z.number().int().nonnegative(),
  genres: z.array(z.object({ tmdb_id: z.number().int().positive(), name: z.string() })),
  trailer: z
    .object({
      site: z.literal("YouTube"),
      key: z.string().regex(/^[A-Za-z0-9_-]+$/),
      name: z.string(),
    })
    .nullable(),
  attribution: tmdbAttributionSchema,
});

export const movieCreditsSchema = z.object({
  tmdb_id: z.number().int().positive(),
  cast: z.array(
    z.object({
      tmdb_id: z.number().int().positive(),
      name: z.string(),
      character: z.string(),
      profile_path: imagePathSchema,
      order: z.number().int().nonnegative(),
    }),
  ),
  crew: z.array(
    z.object({
      tmdb_id: z.number().int().positive(),
      name: z.string(),
      job: z.string(),
      department: z.string(),
      profile_path: imagePathSchema,
    }),
  ),
  attribution: tmdbAttributionSchema,
});

export const movieProvidersSchema = z.object({
  tmdb_id: z.number().int().positive(),
  region: z.literal("BR"),
  streaming: z.array(providerSchema),
  free: z.array(providerSchema),
  ads: z.array(providerSchema),
  rent: z.array(providerSchema),
  buy: z.array(providerSchema),
  attribution: tmdbAttributionSchema,
  availability_attribution: z.object({
    source: z.literal("JustWatch"),
    notice: z.string(),
  }),
});

export type MovieSearch = z.infer<typeof movieSearchSchema>;
export type MovieDetails = z.infer<typeof movieDetailsSchema>;
export type MovieCredits = z.infer<typeof movieCreditsSchema>;
export type MovieProviders = z.infer<typeof movieProvidersSchema>;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
  ) {
    super(code);
    this.name = "ApiError";
  }
}

function validatedApiBase(value: string): string {
  const parsed = new URL(value);
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash
  ) {
    throw new Error("API base must be an HTTP(S) URL without credentials, query, or fragment");
  }
  return value.replace(/\/$/, "");
}

function serverApiBase(): string {
  const configured = process.env.API_INTERNAL_URL ?? process.env.BACKEND_URL;
  if (configured) return validatedApiBase(configured);

  const vercelHost = process.env.VERCEL_URL ?? process.env.VERCEL_PROJECT_PRODUCTION_URL;
  const origin = vercelHost ? `https://${vercelHost}` : "http://localhost:3000";
  return `${origin}/api/backend`;
}

function apiUrl(path: string): string {
  if (!path.startsWith("/") || path.startsWith("//")) {
    throw new Error("API path must be root-relative");
  }
  return typeof window === "undefined"
    ? `${serverApiBase()}${path}`
    : `/api/backend${path}`;
}

async function request<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const response = await fetch(apiUrl(path), {
    headers: { Accept: "application/json" },
    cache: "no-store",
    signal: AbortSignal.timeout(10_000),
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = z.object({ error: z.string() }).safeParse(body);
    throw new ApiError(response.status, error.success ? error.data.error : "request_failed");
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    throw new ApiError(502, "invalid_api_response");
  }
  return parsed.data;
}

export function searchMovies(query: string, page = 1): Promise<MovieSearch> {
  const params = new URLSearchParams({ q: query, page: String(page) });
  return request(`/movies/search?${params.toString()}`, movieSearchSchema);
}

export function getMovieDetails(tmdbId: number): Promise<MovieDetails> {
  return request(`/movies/${tmdbId}`, movieDetailsSchema);
}

export function getMovieCredits(tmdbId: number): Promise<MovieCredits> {
  return request(`/movies/${tmdbId}/credits`, movieCreditsSchema);
}

export function getMovieProviders(tmdbId: number): Promise<MovieProviders> {
  return request(`/movies/${tmdbId}/providers`, movieProvidersSchema);
}

export function tmdbImageUrl(
  path: string | null,
  size: "w185" | "w342" | "w500" | "w780" | "original",
): string | null {
  if (path === null || path.includes("..") || !/^\/[A-Za-z0-9._/-]+$/.test(path)) {
    return null;
  }
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

export function formatRuntime(minutes: number | null): string | null {
  if (minutes === null || minutes <= 0) return null;
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return hours > 0 ? `${hours}h ${remainder.toString().padStart(2, "0")}min` : `${remainder}min`;
}
