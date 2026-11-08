/**
 * Call caps for the public LiveLife demo scoring route (app/api/demo-livelife-score).
 *
 * The demo has no login, so nothing else limits who can call a route that spends money.
 * Two in-memory counters: one per caller address per hour, one for the whole route per
 * day. In memory is enough here: the website is one persistent Node process, and a restart only gives a fresh allowance. Nothing is stored.
 */

export interface LimitConfig {
  perAddressPerHour: number;
  perDay: number;
}

// One call is one STUDENT's whole submission (all eight answers), so a class behind one school
// network can all take it in an hour.
export const DEFAULT_LIMITS: LimitConfig = { perAddressPerHour: 40, perDay: 300 };

const HOUR = 3_600_000;
const DAY = 86_400_000;
/** A hard stop on how many addresses are remembered, so the map cannot grow without end. */
const MAX_ADDRESSES = 5000;

export type LimitResult = { ok: true } | { ok: false; reason: "address" | "day" };

export function createLimiter(config: LimitConfig = DEFAULT_LIMITS, now: () => number = Date.now) {
  const perAddress = new Map<string, number[]>();
  let dayStart = now();
  let dayCount = 0;

  function take(address: string): LimitResult {
    const t = now();
    if (t - dayStart >= DAY) {
      dayStart = t;
      dayCount = 0;
    }
    if (dayCount >= config.perDay) return { ok: false, reason: "day" };

    const recent = (perAddress.get(address) ?? []).filter(x => t - x < HOUR);
    if (recent.length >= config.perAddressPerHour) {
      perAddress.set(address, recent);
      return { ok: false, reason: "address" };
    }
    recent.push(t);
    perAddress.set(address, recent);
    dayCount += 1;

    if (perAddress.size > MAX_ADDRESSES) {
      for (const [k, v] of perAddress) {
        if (!v.some(x => t - x < HOUR)) perAddress.delete(k);
      }
    }
    return { ok: true };
  }

  return { take };
}
