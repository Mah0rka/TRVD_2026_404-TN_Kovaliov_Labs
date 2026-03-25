// Коротко: файл підтримує логіку модуля експорту модуля.

export { hasSessionHint } from "./lib/session";
export {
  allRoles,
  clientAndManagementRoles,
  clientRoles,
  managementRoles,
  trainerRoles,
  userHasRole
} from "./lib/roles";
export {
  loginSchema,
  registerSchema,
  type LoginFormValues,
  type RegisterFormValues
} from "./lib/validation";
export { useAuthStore } from "./model/store";
export { AuthBootstrap } from "./ui/AuthBootstrap";
export { LogoutHandler } from "./ui/LogoutHandler";
export { ProtectedLayout } from "./ui/ProtectedLayout";
export { PublicOnlyLayout } from "./ui/PublicOnlyLayout";
export { RoleBoundary } from "./ui/RoleBoundary";
