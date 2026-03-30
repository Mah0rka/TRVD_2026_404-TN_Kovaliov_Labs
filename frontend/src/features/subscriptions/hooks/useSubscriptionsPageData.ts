import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createMembershipPlan,
  deleteMembershipPlan,
  freezeSubscription,
  getSubscriptionPlans,
  getSubscriptions,
  purchaseSubscription,
  queryKeys,
  updateMembershipPlan,
  type MembershipPlan
} from "../../../shared/api";

type UseSubscriptionsPageDataOptions = {
  isClient: boolean;
};

// Централізує queries та mutations для сторінки абонементів разом з їх invalidation policy.
// Це особливо важливо тут, бо одна дія впливає одразу на декілька surface-ів:
// список планів, власні абонементи, платежі та dashboard summary.
export function useSubscriptionsPageData({ isClient }: UseSubscriptionsPageDataOptions) {
  const queryClient = useQueryClient();

  // Плани потрібні всім: клієнту для покупки, менеджменту для адміністрування.
  const plansQuery = useQuery({
    queryKey: queryKeys.subscriptions.plans(),
    queryFn: getSubscriptionPlans
  });

  // Власні абонементи мають сенс лише для клієнтського кабінету.
  const subscriptionsQuery = useQuery({
    queryKey: queryKeys.subscriptions.mine(),
    queryFn: getSubscriptions,
    enabled: isClient
  });

  const purchaseMutation = useMutation({
    mutationFn: purchaseSubscription,
    onSuccess: () => {
      // Купівля впливає не лише на самі абонементи, а і на платежі та dashboard summary.
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.mine() });
      queryClient.invalidateQueries({ queryKey: queryKeys.payments.mine() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.bookings() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.subscriptions() });
    }
  });

  const freezeMutation = useMutation({
    mutationFn: ({ id, days }: { id: string; days: number }) => freezeSubscription(id, days),
    onSuccess: () => {
      // Заморозка змінює тільки стан конкретного абонемента, тому інвалідовуємо
      // лише клієнтський список, не зачіпаючи каталог планів.
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.mine() });
    }
  });

  const createPlanMutation = useMutation({
    mutationFn: createMembershipPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.plans() });
    }
  });

  const updatePlanMutation = useMutation({
    mutationFn: ({
      id,
      payload
    }: {
      id: string;
      payload: Partial<Omit<MembershipPlan, "id" | "created_at" | "updated_at">>;
    }) => updateMembershipPlan(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.plans() });
    }
  });

  const deletePlanMutation = useMutation({
    mutationFn: deleteMembershipPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.plans() });
    }
  });

  return {
    plansQuery,
    subscriptionsQuery,
    purchaseMutation,
    freezeMutation,
    createPlanMutation,
    updatePlanMutation,
    deletePlanMutation
  };
}
