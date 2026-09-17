import { describe, expect, it } from "vitest";

import { foundationPillars, privacyPrinciples } from "./foundation";

describe("Phase 0 product foundation", () => {
  it("keeps the initial product pillars unique", () => {
    const ids = foundationPillars.map(({ id }) => id);

    expect(new Set(ids).size).toBe(ids.length);
  });

  it("includes private-by-default in the visible principles", () => {
    expect(privacyPrinciples).toContainEqual(
      expect.objectContaining({ id: "private-default" }),
    );
  });
});
