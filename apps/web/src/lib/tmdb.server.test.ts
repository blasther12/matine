import { afterEach, describe, expect, it, vi } from "vitest";

import { handleCatalogRequest } from "./tmdb.server";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("TMDB server catalog", () => {
  it("keeps the token server-side and maps search results", async () => {
    vi.stubEnv("TMDB_API_KEY", "read-access-token");
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        page: 1,
        total_pages: 1,
        total_results: 1,
        results: [
          {
            id: 348,
            title: "Alien",
            original_title: "Alien",
            overview: "In space no one can hear you scream.",
            release_date: "1979-05-25",
            poster_path: "/poster.jpg",
            vote_average: 8.2,
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await handleCatalogRequest(
      new Request("http://localhost/api/backend/movies/search?q=Alien&page=1"),
      ["search"],
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      total_results: 1,
      results: [{ tmdb_id: 348, title: "Alien", year: 1979 }],
    });
    const [, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(init.headers).toMatchObject({ Authorization: "Bearer read-access-token" });
  });

  it("fails safely when the server token is missing", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await handleCatalogRequest(
      new Request("http://localhost/api/backend/movies/search?q=Alien&page=1"),
      ["search"],
    );

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({ error: "catalog_not_configured" });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
