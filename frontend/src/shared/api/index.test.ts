// Тести перевіряють ключові сценарії цього модуля.

import * as api from "./index";
import { apiRequest, getErrorMessage } from "./core/http";
import { authApi } from "./modules/auth";
import { bookingsApi } from "./modules/bookings";
import { paymentsApi } from "./modules/payments";
import { publicApi } from "./modules/public";
import { reportsApi } from "./modules/reports";
import { schedulesApi } from "./modules/schedules";
import { subscriptionsApi } from "./modules/subscriptions";
import { usersApi } from "./modules/users";
import { queryKeys } from "./queryKeys";

describe("shared/api barrel", () => {
  it("re-exports http helpers and module APIs", () => {
    expect(api.apiRequest).toBe(apiRequest);
    expect(api.getErrorMessage).toBe(getErrorMessage);
    expect(api.authApi).toBe(authApi);
    expect(api.publicApi).toBe(publicApi);
    expect(api.usersApi).toBe(usersApi);
    expect(api.schedulesApi).toBe(schedulesApi);
    expect(api.subscriptionsApi).toBe(subscriptionsApi);
    expect(api.bookingsApi).toBe(bookingsApi);
    expect(api.paymentsApi).toBe(paymentsApi);
    expect(api.reportsApi).toBe(reportsApi);
    expect(api.queryKeys).toBe(queryKeys);
  });

  it("keeps centralized query key factories stable", () => {
    expect(api.queryKeys.dashboard.revenue()).toEqual(["dashboard", "revenue"]);
    expect(api.queryKeys.schedules.calendar("from", "to")).toEqual([
      "schedules",
      "calendar",
      "from",
      "to"
    ]);
    expect(api.queryKeys.users.list()).toEqual(["users", "list", "ALL"]);
  });
});
