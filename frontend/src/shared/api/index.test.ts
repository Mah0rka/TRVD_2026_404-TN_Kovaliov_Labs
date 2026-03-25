// Коротко: тести перевіряють сценарії модуля експорту модуля.

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
  });
});
