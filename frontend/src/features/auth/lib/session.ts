export function hasSessionHint(): boolean {
  return document.cookie.split("; ").some((entry) => entry.startsWith("fcms_csrf_token="));
}
