import { z } from "zod";

import type { Subscription } from "../core/contracts";
import { subscriptionSchema } from "../core/contracts";
import { request } from "../core/http";

export async function getSubscriptions(): Promise<Subscription[]> {
  const data = await request<unknown>("/subscriptions/my-subscriptions", { method: "GET" });
  return z.array(subscriptionSchema).parse(data);
}

export async function purchaseSubscription(
  type: "MONTHLY" | "YEARLY" | "PAY_AS_YOU_GO"
): Promise<Subscription> {
  const data = await request<unknown>("/subscriptions/purchase", {
    method: "POST",
    body: JSON.stringify({ type })
  });

  return subscriptionSchema.parse(data);
}

export async function freezeSubscription(id: string, days: number): Promise<Subscription> {
  const data = await request<unknown>(`/subscriptions/${id}/freeze`, {
    method: "PATCH",
    body: JSON.stringify({ days })
  });

  return subscriptionSchema.parse(data);
}
