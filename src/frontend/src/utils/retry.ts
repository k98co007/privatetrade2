export const DEFAULT_SSE_BACKOFF_SECONDS = [1, 2, 4, 8, 10] as const;

export function getBackoffDelayMs(attempt: number): number {
  const schedule = DEFAULT_SSE_BACKOFF_SECONDS;
  return (schedule[Math.min(attempt, schedule.length - 1)] ?? 10) * 1000;
}
