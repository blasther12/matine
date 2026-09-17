import { z } from "zod";

const TMDB_ORIGIN = "https://api.themoviedb.org/3";
const TMDB_NOTICE = "This product uses the TMDB API but is not endorsed or certified by TMDB.";
const JUSTWATCH_NOTICE = "Availability data is provided by JustWatch through TMDB.";
const imagePathPattern = /^\/[A-Za-z0-9._/-]+$/;
const videoKeyPattern = /^[A-Za-z0-9_-]+$/;

const movieSummarySchema = z.object({
  id: z.number().int().positive(),
  title: z.string(),
  original_title: z.string(),
  overview: z.string(),
  release_date: z.string().optional().default(""),
  poster_path: z.string().nullable().optional().default(null),
  vote_average: z.number().min(0).max(10),
});

const searchSchema = z.object({
  page: z.number().int().positive(),
  total_pages: z.number().int().nonnegative(),
  total_results: z.number().int().nonnegative(),
  results: z.array(movieSummarySchema),
});

const videoSchema = z.object({
  site: z.string(),
  key: z.string(),
  name: z.string(),
  type: z.string(),
  official: z.boolean().optional().default(false),
});

const detailsSchema = movieSummarySchema.extend({
  backdrop_path: z.string().nullable().optional().default(null),
  runtime: z.number().int().nonnegative().nullable().optional().default(null),
  vote_count: z.number().int().nonnegative(),
  genres: z.array(z.object({ id: z.number().int().positive(), name: z.string() })),
  videos: z.object({ results: z.array(videoSchema) }).optional().default({ results: [] }),
});

const personSchema = z.object({
  id: z.number().int().positive(),
  name: z.string(),
  profile_path: z.string().nullable().optional().default(null),
});

const creditsSchema = z.object({
  id: z.number().int().positive(),
  cast: z.array(
    personSchema.extend({
      character: z.string().optional().default(""),
      order: z.number().int().nonnegative().optional().default(0),
    }),
  ),
  crew: z.array(
    personSchema.extend({
      job: z.string().optional().default(""),
      department: z.string().optional().default(""),
    }),
  ),
});

const providerSchema = z.object({
  provider_id: z.number().int().positive(),
  provider_name: z.string(),
  logo_path: z.string().nullable().optional().default(null),
  display_priority: z.number().int().nonnegative().optional().default(0),
});

const providerRegionSchema = z.object({
  flatrate: z.array(providerSchema).optional().default([]),
  free: z.array(providerSchema).optional().default([]),
  ads: z.array(providerSchema).optional().default([]),
  rent: z.array(providerSchema).optional().default([]),
  buy: z.array(providerSchema).optional().default([]),
});

const providersSchema = z.object({
  id: z.number().int().positive(),
  results: z.record(z.string(), providerRegionSchema),
});

class CatalogError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(code);
  }
}

function text(value: string, maximum: number, fallback = ""): string {
  const normalized = value.trim();
  return (normalized || fallback).slice(0, maximum);
}

function imagePath(value: string | null): string | null {
  return value && !value.includes("..") && imagePathPattern.test(value) ? value : null;
}

function releaseDate(value: string): string | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(parsed.valueOf()) ? null : value;
}

function movieItem(movie: z.infer<typeof movieSummarySchema>) {
  const date = releaseDate(movie.release_date);
  const title = text(movie.title, 500, "Untitled");
  return {
    tmdb_id: movie.id,
    title,
    original_title: text(movie.original_title, 500, title),
    overview: text(movie.overview, 10_000),
    release_date: date,
    year: date ? Number(date.slice(0, 4)) : null,
    poster_path: imagePath(movie.poster_path),
    vote_average: movie.vote_average,
  };
}

function apiToken(): string {
  const token = process.env.TMDB_API_KEY?.trim();
  if (!token) throw new CatalogError(503, "catalog_not_configured");
  return token;
}

function tmdbOrigin(): string {
  const configured = process.env.TMDB_BASE_URL?.trim() || TMDB_ORIGIN;
  const parsed = new URL(configured);
  if (parsed.protocol !== "https:" || parsed.username || parsed.password) {
    throw new CatalogError(503, "catalog_not_configured");
  }
  return parsed.origin + parsed.pathname.replace(/\/$/, "");
}

async function tmdb(path: string, parameters: Record<string, string> = {}): Promise<unknown> {
  const url = new URL(`${tmdbOrigin()}${path}`);
  for (const [key, value] of Object.entries(parameters)) url.searchParams.set(key, value);
  const token = apiToken();
  let response: Response;
  try {
    response = await fetch(url, {
      headers: { Accept: "application/json", Authorization: `Bearer ${token}` },
      cache: "no-store",
      signal: AbortSignal.timeout(8_000),
    });
  } catch {
    throw new CatalogError(502, "catalog_unavailable");
  }
  if (response.status === 404) throw new CatalogError(404, "movie_not_found");
  if (!response.ok) {
    throw new CatalogError(
      response.status === 401 || response.status === 403 ? 503 : 502,
      response.status === 401 || response.status === 403
        ? "catalog_not_configured"
        : "catalog_unavailable",
    );
  }
  try {
    return await response.json();
  } catch {
    throw new CatalogError(502, "invalid_catalog_response");
  }
}

function json(body: unknown, status = 200, cache = "no-store"): Response {
  return Response.json(body, { status, headers: { "Cache-Control": cache } });
}

function movieId(value: string): number {
  if (!/^[1-9]\d{0,9}$/.test(value)) throw new CatalogError(404, "movie_not_found");
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id > 2_147_483_647) {
    throw new CatalogError(404, "movie_not_found");
  }
  return id;
}

function provider(value: z.infer<typeof providerSchema>) {
  return {
    tmdb_provider_id: value.provider_id,
    name: text(value.provider_name, 300, "Provider"),
    logo_path: imagePath(value.logo_path),
    display_priority: value.display_priority,
  };
}

export async function handleCatalogRequest(request: Request, segments: string[]): Promise<Response> {
  try {
    if (segments.length === 1 && segments[0] === "search") {
      const url = new URL(request.url);
      const query = url.searchParams.get("q")?.trim() ?? "";
      const pageValue = url.searchParams.get("page") ?? "1";
      const page = Number(pageValue);
      if (
        query.length < 2 ||
        query.length > 100 ||
        /\p{C}/u.test(query) ||
        !/^\d{1,3}$/.test(pageValue) ||
        !Number.isInteger(page) ||
        page < 1 ||
        page > 500
      ) {
        throw new CatalogError(422, "invalid_search");
      }
      const upstream = searchSchema.parse(
        await tmdb("/search/movie", {
          query,
          page: String(page),
          language: process.env.TMDB_LANGUAGE?.trim() || "pt-BR",
          region: process.env.TMDB_REGION?.trim() || "BR",
          include_adult: "false",
        }),
      );
      return json({
        page: upstream.page,
        total_pages: upstream.total_pages,
        total_results: upstream.total_results,
        results: upstream.results.map(movieItem),
        attribution: { source: "TMDB", notice: TMDB_NOTICE },
      });
    }

    if (segments.length < 1 || segments.length > 2) {
      throw new CatalogError(404, "route_not_found");
    }
    const id = movieId(segments[0] ?? "");

    if (segments.length === 1) {
      const movie = detailsSchema.parse(
        await tmdb(`/movie/${id}`, {
          language: process.env.TMDB_LANGUAGE?.trim() || "pt-BR",
          append_to_response: "videos",
        }),
      );
      const base = movieItem(movie);
      const trailer = [...movie.videos.results]
        .sort((left, right) =>
          Number(right.site === "YouTube") - Number(left.site === "YouTube") ||
          Number(right.type === "Trailer") - Number(left.type === "Trailer") ||
          Number(right.official) - Number(left.official),
        )
        .find((video) => video.site === "YouTube" && videoKeyPattern.test(video.key));
      return json(
        {
          ...base,
          runtime_minutes: movie.runtime,
          backdrop_path: imagePath(movie.backdrop_path),
          vote_count: movie.vote_count,
          genres: movie.genres.map((genre) => ({
            tmdb_id: genre.id,
            name: text(genre.name, 100, "Genre"),
          })),
          trailer: trailer
            ? { site: "YouTube", key: trailer.key, name: text(trailer.name, 500, "Trailer") }
            : null,
          attribution: { source: "TMDB", notice: TMDB_NOTICE },
        },
        200,
        "public, max-age=300, s-maxage=300",
      );
    }

    if (segments[1] === "credits") {
      const credits = creditsSchema.parse(
        await tmdb(`/movie/${id}/credits`, {
          language: process.env.TMDB_LANGUAGE?.trim() || "pt-BR",
        }),
      );
      return json(
        {
          tmdb_id: credits.id,
          cast: [...credits.cast]
            .sort((left, right) => left.order - right.order)
            .slice(0, 20)
            .map((member) => ({
              tmdb_id: member.id,
              name: text(member.name, 300, "Unknown"),
              character: text(member.character, 500),
              profile_path: imagePath(member.profile_path),
              order: member.order,
            })),
          crew: credits.crew.slice(0, 50).map((member) => ({
            tmdb_id: member.id,
            name: text(member.name, 300, "Unknown"),
            job: text(member.job, 300),
            department: text(member.department, 300),
            profile_path: imagePath(member.profile_path),
          })),
          attribution: { source: "TMDB", notice: TMDB_NOTICE },
        },
        200,
        "public, max-age=300, s-maxage=300",
      );
    }

    if (segments[1] === "providers") {
      const providers = providersSchema.parse(await tmdb(`/movie/${id}/watch/providers`));
      const region = providers.results.BR ?? providerRegionSchema.parse({});
      return json(
        {
          tmdb_id: providers.id,
          region: "BR",
          streaming: region.flatrate.map(provider),
          free: region.free.map(provider),
          ads: region.ads.map(provider),
          rent: region.rent.map(provider),
          buy: region.buy.map(provider),
          attribution: { source: "TMDB", notice: TMDB_NOTICE },
          availability_attribution: { source: "JustWatch", notice: JUSTWATCH_NOTICE },
        },
        200,
        "public, max-age=300, s-maxage=300",
      );
    }

    throw new CatalogError(404, "route_not_found");
  } catch (error) {
    if (error instanceof CatalogError) return json({ error: error.code }, error.status);
    if (error instanceof z.ZodError) return json({ error: "invalid_catalog_response" }, 502);
    console.error("[catalog] unexpected server error", {
      error: error instanceof Error ? error.message : String(error),
    });
    return json({ error: "catalog_unavailable" }, 502);
  }
}
