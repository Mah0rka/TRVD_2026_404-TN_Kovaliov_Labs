// Коротко: тести перевіряють сценарії модуля ролей доступу.

import { userHasRole } from "./roles";

describe("userHasRole", () => {
  it("returns true when role is allowed", () => {
    expect(userHasRole({ role: "ADMIN" }, ["ADMIN", "OWNER"])).toBe(true);
  });

  it("returns false when user is missing", () => {
    expect(userHasRole(null, ["CLIENT"])).toBe(false);
  });

  it("returns false when role is not allowed", () => {
    expect(userHasRole({ role: "TRAINER" }, ["CLIENT", "OWNER"])).toBe(false);
  });
});
