// Коротко: допоміжний модуль містить утиліти для допоміжних форм.

import type { ZodError } from "zod";

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
