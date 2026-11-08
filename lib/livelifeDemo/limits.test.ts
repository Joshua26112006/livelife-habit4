import { describe, expect, it } from "vitest";
import { createLimiter } from "./limits";

describe("livelife demo limiter", () => {
  it("lets an address through up to its hourly allowance, then refuses", () => {
    let t = 0;
    const l = createLimiter({ perAddressPerHour: 3, perDay: 100 }, () => t);
    expect(l.take("a").ok).toBe(true);
    expect(l.take("a").ok).toBe(true);
    expect(l.take("a").ok).toBe(true);
    expect(l.take("a")).toEqual({ ok: false, reason: "address" });
    // another address is not affected
    expect(l.take("b").ok).toBe(true);
    // an hour later the first address is allowed again
    t += 3_600_001;
    expect(l.take("a").ok).toBe(true);
  });

  it("stops the whole route at the daily cap, whoever calls", () => {
    let t = 0;
    const l = createLimiter({ perAddressPerHour: 100, perDay: 2 }, () => t);
    expect(l.take("a").ok).toBe(true);
    expect(l.take("b").ok).toBe(true);
    expect(l.take("c")).toEqual({ ok: false, reason: "day" });
    t += 86_400_001;
    expect(l.take("c").ok).toBe(true);
  });

  it("a refused call does not use up the allowance", () => {
    let t = 0;
    const l = createLimiter({ perAddressPerHour: 1, perDay: 100 }, () => t);
    expect(l.take("a").ok).toBe(true);
    for (let i = 0; i < 5; i++) expect(l.take("a").ok).toBe(false);
    t += 3_600_001;
    expect(l.take("a").ok).toBe(true);
  });
});
