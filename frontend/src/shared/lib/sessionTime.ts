export function hasSessionStarted(startTime: string, now = Date.now()): boolean {
  return new Date(startTime).getTime() <= now;
}

export function hasSessionEnded(endTime: string, now = Date.now()): boolean {
  return new Date(endTime).getTime() <= now;
}
