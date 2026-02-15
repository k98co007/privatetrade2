export function nowMs(): number {
  return Date.now();
}

export function isFresh(fetchedAt: number, ttlMs: number): boolean {
  return nowMs() - fetchedAt <= ttlMs;
}
