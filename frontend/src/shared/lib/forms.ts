// Модуль містить допоміжні утиліти для клієнтської частини.

import type { ZodError } from "zod";

// Перетворює помилки Zod на зручну мапу для полів форми.
export function getFieldErrors(error: ZodError): Record<string, string> {
  const fieldErrors: Record<string, string> = {};

  for (const issue of error.issues) {
    const fieldName = String(issue.path[0] ?? "form");
    if (!fieldErrors[fieldName]) {
      fieldErrors[fieldName] = issue.message;
    }
  }

  return fieldErrors;
}
