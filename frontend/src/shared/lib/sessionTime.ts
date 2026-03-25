// Показує, чи заняття вже стартувало для клієнтських та management-фільтрів.
export function hasSessionStarted(startTime: string, now = Date.now()): boolean {
  return new Date(startTime).getTime() <= now;
}

// Показує, чи заняття вже завершилось і має перейти в історію.
export function hasSessionEnded(endTime: string, now = Date.now()): boolean {
  return new Date(endTime).getTime() <= now;
}
