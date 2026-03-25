// Тести перевіряють ключові сценарії цього модуля.

import * as authExports from "./index";
import { hasSessionHint } from "./lib/session";
import {
  allRoles,
  clientAndManagementRoles,
  clientRoles,
  managementRoles,
  trainerRoles,
  userHasRole
} from "./lib/roles";
import { loginSchema, registerSchema } from "./lib/validation";
import { useAuthStore } from "./model/store";
import { AuthBootstrap } from "./ui/AuthBootstrap";
import { LogoutHandler } from "./ui/LogoutHandler";
import { ProtectedLayout } from "./ui/ProtectedLayout";
import { PublicOnlyLayout } from "./ui/PublicOnlyLayout";
import { RoleBoundary } from "./ui/RoleBoundary";

describe("features/auth barrel", () => {
  it("re-exports auth contracts and ui pieces", () => {
    expect(authExports.hasSessionHint).toBe(hasSessionHint);
    expect(authExports.allRoles).toBe(allRoles);
    expect(authExports.clientRoles).toBe(clientRoles);
    expect(authExports.managementRoles).toBe(managementRoles);
    expect(authExports.trainerRoles).toBe(trainerRoles);
    expect(authExports.clientAndManagementRoles).toBe(clientAndManagementRoles);
    expect(authExports.userHasRole).toBe(userHasRole);
    expect(authExports.loginSchema).toBe(loginSchema);
    expect(authExports.registerSchema).toBe(registerSchema);
    expect(authExports.useAuthStore).toBe(useAuthStore);
    expect(authExports.AuthBootstrap).toBe(AuthBootstrap);
    expect(authExports.LogoutHandler).toBe(LogoutHandler);
    expect(authExports.ProtectedLayout).toBe(ProtectedLayout);
    expect(authExports.PublicOnlyLayout).toBe(PublicOnlyLayout);
    expect(authExports.RoleBoundary).toBe(RoleBoundary);
  });
});
