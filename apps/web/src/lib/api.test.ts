import { describe, expect, it } from "vitest";

import { formatRuntime, movieDetailsSchema, tmdbImageUrl } from "./api";

describe("catalog helpers", () => {
  it("builds only fixed-host TMDB image URLs", () => {
    expect(tmdbImageUrl("/poster.jpg", "w342")).toBe(
      "https://image.tmdb.org/t/p/w342/poster.jpg",
    );
    expect(tmdbImageUrl("https://attacker.example/x", "w342")).toBeNull();
    expect(tmdbImageUrl("/../../secret", "w342")).toBeNull();
  });

  it("formats runtimes", () => {
    expect(formatRuntime(117)).toBe("1h 57min");
    expect(formatRuntime(42)).toBe("42min");
    expect(formatRuntime(null)).toBeNull();
  });

  it("rejects arbitrary trailer sites and keys", () => {
    const base = {
      tmdb_id: 348,
      title: "Alien",
      original_title: "Alien",
      overview: "",
      release_date: "1979-05-25",
      year: 1979,
      runtime_minutes: 117,
      poster_path: "/poster.jpg",
      backdrop_path: null,
      vote_average: 8.2,
      vote_count: 1,
      genres: [],
      attribution: { source: "TMDB", notice: "notice" },
    };
    expect(
      movieDetailsSchema.safeParse({
        ...base,
        trailer: { site: "Other", key: "https://attacker.example", name: "x" },
      }).success,
    ).toBe(false);
  });
});
