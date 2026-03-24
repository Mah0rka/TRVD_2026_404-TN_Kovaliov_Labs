import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  createMembershipPlan,
  deleteMembershipPlan,
  freezeSubscription,
  getSubscriptionPlans,
  getSubscriptions,
  purchaseSubscription,
  type Subscription,
  updateMembershipPlan,
  type MembershipPlan
} from "../../../shared/api";
import { useAuthStore } from "../../auth";

function getStatusLabel(status: string): string {
  if (status === "ACTIVE") {
    return "Активний";
  }

  if (status === "FROZEN") {
    return "На паузі";
  }

  return "Завершений";
}

function getPlanTypeLabel(type: MembershipPlan["type"]): string {
  if (type === "MONTHLY") {
    return "Місячний";
  }

  if (type === "YEARLY") {
    return "Річний";
  }

  return "Разове відвідування";
}

function getPlanMeta(plan: MembershipPlan): string {
  const visits = plan.visits_limit ? `${plan.visits_limit} занять` : "Безліміт";
  return `${visits} · ${plan.duration_days} днів · ${plan.currency} ${plan.price}`;
}

function emptyPlanForm() {
  return {
    title: "",
    description: "",
    type: "MONTHLY" as MembershipPlan["type"],
    duration_days: 30,
    visits_limit: 12,
    price: 990,
    currency: "UAH",
    sort_order: 100,
    is_active: true,
    is_public: true
  };
}

export function SubscriptionsPage() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const isClient = user?.role === "CLIENT";
  const isManagement = user?.role === "ADMIN" || user?.role === "OWNER";
  const [freezeTarget, setFreezeTarget] = useState<string | null>(null);
  const [freezeDays, setFreezeDays] = useState(7);
  const [showAllPlans, setShowAllPlans] = useState(false);
  const [editingPlanId, setEditingPlanId] = useState<string | null>(null);
  const [selectedPlanId, setSelectedPlanId] = useState<string>("");
  const [planForm, setPlanForm] = useState(emptyPlanForm());

  const plansQuery = useQuery({
    queryKey: ["membership-plans"],
    queryFn: getSubscriptionPlans
  });

  const subscriptionsQuery = useQuery({
    queryKey: ["my-subscriptions"],
    queryFn: getSubscriptions,
    enabled: isClient
  });

  const purchaseMutation = useMutation({
    mutationFn: purchaseSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["my-payments"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-subscriptions"] });
    }
  });

  const freezeMutation = useMutation({
    mutationFn: ({ id, days }: { id: string; days: number }) => freezeSubscription(id, days),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-subscriptions"] });
      setFreezeTarget(null);
    }
  });

  const createPlanMutation = useMutation({
    mutationFn: createMembershipPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["membership-plans"] });
      setPlanForm(emptyPlanForm());
    }
  });

  const updatePlanMutation = useMutation({
    mutationFn: ({
      id,
      payload
    }: {
      id: string;
      payload: Partial<Omit<MembershipPlan, "id" | "created_at" | "updated_at">>;
    }) =>
      updateMembershipPlan(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["membership-plans"] });
      setEditingPlanId(null);
      setPlanForm(emptyPlanForm());
    }
  });

  const deletePlanMutation = useMutation({
    mutationFn: deleteMembershipPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["membership-plans"] });
    }
  });

  const currentSubscriptions = subscriptionsQuery.data ?? [];
  const blockingSubscription = currentSubscriptions.find(
    (subscription) => subscription.status === "ACTIVE" || subscription.status === "FROZEN"
  );
  const plans = plansQuery.data ?? [];
  const sortedPlans = useMemo(
    () => [...plans].sort((left, right) => left.sort_order - right.sort_order),
    [plans]
  );
  const hiddenPlansCount = Math.max(sortedPlans.length - 3, 0);
  const selectedPlan =
    sortedPlans.find((plan) => plan.id === selectedPlanId) ?? sortedPlans[0] ?? null;
  const clientVisiblePlans =
    sortedPlans.length > 3 ? (selectedPlan ? [selectedPlan] : []) : sortedPlans;
  const adminVisiblePlans = showAllPlans || sortedPlans.length <= 3 ? sortedPlans : sortedPlans.slice(0, 3);

  useEffect(() => {
    if (!sortedPlans.length) {
      if (selectedPlanId) {
        setSelectedPlanId("");
      }
      return;
    }

    if (!selectedPlanId || !sortedPlans.some((plan) => plan.id === selectedPlanId)) {
      setSelectedPlanId(sortedPlans[0].id);
    }
  }, [selectedPlanId, sortedPlans]);

  function startEditingPlan(plan: MembershipPlan) {
    setEditingPlanId(plan.id);
    setPlanForm({
      title: plan.title,
      description: plan.description ?? "",
      type: plan.type,
      duration_days: plan.duration_days,
      visits_limit: plan.visits_limit ?? 0,
      price: plan.price,
      currency: plan.currency,
      sort_order: plan.sort_order,
      is_active: plan.is_active,
      is_public: Boolean(plan.is_public)
    });
  }

  function resetPlanEditor() {
    setEditingPlanId(null);
    setPlanForm(emptyPlanForm());
  }

  function buildPlanPayload() {
    return {
      ...planForm,
      visits_limit: planForm.visits_limit > 0 ? planForm.visits_limit : null
    };
  }

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <p className="eyebrow">Абонементи</p>
          <h1>{isManagement ? "Плани абонементів клубу" : "Абонементи клубу"}</h1>
          <p className="muted">
            {isManagement
              ? "Усі плани беруться з системи. Тут можна створювати, редагувати й видаляти реальні абонементи клубу."
              : "Клуб продає тільки абонементи. Вибери план із системи, оформи покупку й керуй ним у кабінеті."}
          </p>
        </div>

        {plansQuery.isLoading ? <p className="muted">Завантаження планів абонементів...</p> : null}
        {plansQuery.isError ? (
          <p className="error-banner">
            {plansQuery.error instanceof Error ? plansQuery.error.message : "Помилка завантаження планів"}
          </p>
        ) : null}

        {isClient && sortedPlans.length > 3 ? (
          <div className="surface-card subscriptions-picker">
            <label>
              Оберіть абонемент
              <select value={selectedPlanId} onChange={(event) => setSelectedPlanId(event.target.value)}>
                {sortedPlans.map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.title} · {plan.currency} {plan.price}
                  </option>
                ))}
              </select>
            </label>
            <p className="muted">
              У системі зараз {sortedPlans.length} абонементів, тому ми показуємо вибраний план окремо.
            </p>
          </div>
        ) : null}

        <div className="schedule-grid">
          {(isManagement ? adminVisiblePlans : clientVisiblePlans).map((plan) => (
            <article className="schedule-item" key={plan.id}>
              <p className="eyebrow">
                {getPlanTypeLabel(plan.type)} · {plan.duration_days} днів
              </p>
              <h2>{plan.title}</h2>
              <p className="muted">{getPlanMeta(plan)}</p>
              {plan.description ? <p className="muted">{plan.description}</p> : null}
              {isManagement ? (
                <p className="muted">
                  Статус: {plan.is_active ? "активний" : "прихований"} ·{" "}
                  {plan.is_public ? "публічний" : "непублічний"}
                </p>
              ) : null}
              <div className="actions-row">
                {isClient ? (
                  <button
                    className="secondary-button"
                    onClick={() => purchaseMutation.mutate(plan.id)}
                    disabled={purchaseMutation.isPending || Boolean(blockingSubscription) || !plan.is_active}
                  >
                    {purchaseMutation.isPending
                      ? "Оформлення..."
                      : !plan.is_active
                        ? "План вимкнено"
                        : blockingSubscription
                          ? "Спочатку завершіть поточний план"
                          : "Купити абонемент"}
                  </button>
                ) : null}
                {isManagement ? (
                  <>
                    <button className="ghost-link" onClick={() => startEditingPlan(plan)}>
                      Редагувати
                    </button>
                    <button
                      className="danger-link"
                      onClick={() => deletePlanMutation.mutate(plan.id)}
                      disabled={deletePlanMutation.isPending}
                    >
                      Видалити
                    </button>
                  </>
                ) : null}
              </div>
            </article>
          ))}
        </div>

        {isManagement && sortedPlans.length > 3 ? (
          <div className="actions-row">
            <button className="ghost-link" onClick={() => setShowAllPlans((current) => !current)}>
              {showAllPlans ? "Сховати додаткові абонементи" : `Показати ще ${hiddenPlansCount} абонементи`}
            </button>
          </div>
        ) : null}

        {blockingSubscription && isClient ? (
          <p className="muted">
            У вас уже є {blockingSubscription.status === "FROZEN" ? "заморожений" : "активний"} абонемент.
            Новий план можна оформити після завершення або зміни поточного.
          </p>
        ) : null}
        {purchaseMutation.isError ? (
          <p className="error-banner">
            {purchaseMutation.error instanceof Error ? purchaseMutation.error.message : "Помилка під час покупки"}
          </p>
        ) : null}

        {isManagement ? (
          <div className="surface-card form-grid">
            <div className="heading-row">
              <h3>{editingPlanId ? "Редагування абонемента" : "Створити абонемент"}</h3>
              {editingPlanId ? (
                <button className="ghost-link" onClick={resetPlanEditor}>
                  Скасувати
                </button>
              ) : null}
            </div>
            <label>
              Назва
              <input
                value={planForm.title}
                onChange={(event) => setPlanForm((current) => ({ ...current, title: event.target.value }))}
              />
            </label>
            <label>
              Опис
              <input
                value={planForm.description}
                onChange={(event) =>
                  setPlanForm((current) => ({ ...current, description: event.target.value }))
                }
              />
            </label>
            <label>
              Тип
              <select
                value={planForm.type}
                onChange={(event) =>
                  setPlanForm((current) => ({ ...current, type: event.target.value as MembershipPlan["type"] }))
                }
              >
                <option value="MONTHLY">Місячний</option>
                <option value="YEARLY">Річний</option>
                <option value="PAY_AS_YOU_GO">Разове відвідування</option>
              </select>
            </label>
            <label>
              Тривалість, днів
              <input
                type="number"
                min={1}
                value={planForm.duration_days}
                onChange={(event) =>
                  setPlanForm((current) => ({ ...current, duration_days: Number(event.target.value) }))
                }
              />
            </label>
            <label>
              Ліміт відвідувань
              <input
                type="number"
                min={0}
                value={planForm.visits_limit ?? 0}
                onChange={(event) =>
                  setPlanForm((current) => ({
                    ...current,
                    visits_limit: Number(event.target.value)
                  }))
                }
              />
            </label>
            <label>
              Ціна
              <input
                type="number"
                min={1}
                step="0.01"
                value={planForm.price}
                onChange={(event) =>
                  setPlanForm((current) => ({ ...current, price: Number(event.target.value) }))
                }
              />
            </label>
            <label>
              Валюта
              <input
                value={planForm.currency}
                onChange={(event) => setPlanForm((current) => ({ ...current, currency: event.target.value }))}
              />
            </label>
            <label>
              Порядок
              <input
                type="number"
                min={0}
                value={planForm.sort_order}
                onChange={(event) =>
                  setPlanForm((current) => ({ ...current, sort_order: Number(event.target.value) }))
                }
              />
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={planForm.is_active}
                onChange={(event) =>
                  setPlanForm((current) => ({ ...current, is_active: event.target.checked }))
                }
              />
              План активний
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={planForm.is_public}
                onChange={(event) =>
                  setPlanForm((current) => ({ ...current, is_public: event.target.checked }))
                }
              />
              Публічний план для сайту та покупки
            </label>
            <button
              className="secondary-button"
              onClick={() =>
                editingPlanId
                  ? updatePlanMutation.mutate({ id: editingPlanId, payload: buildPlanPayload() })
                  : createPlanMutation.mutate(buildPlanPayload())
              }
              disabled={
                createPlanMutation.isPending ||
                updatePlanMutation.isPending ||
                !planForm.title ||
                !planForm.duration_days ||
                !planForm.price
              }
            >
              {editingPlanId
                ? updatePlanMutation.isPending
                  ? "Збереження..."
                  : "Зберегти абонемент"
                : createPlanMutation.isPending
                  ? "Створення..."
                  : "Створити абонемент"}
            </button>
            {createPlanMutation.isError || updatePlanMutation.isError || deletePlanMutation.isError ? (
              <p className="error-banner">
                {(createPlanMutation.error instanceof Error && createPlanMutation.error.message) ||
                  (updatePlanMutation.error instanceof Error && updatePlanMutation.error.message) ||
                  (deletePlanMutation.error instanceof Error && deletePlanMutation.error.message) ||
                  "Помилка роботи з абонементом"}
              </p>
            ) : null}
          </div>
        ) : null}

        {isManagement ? (
          <div className="surface-card management-note-card">
            <h3>Клієнтські абонементи керуються через Учасників</h3>
            <p className="muted">
              Видача, видалення, відновлення та історія придбаних абонементів тепер зібрані в
              одному місці через картку конкретного учасника.
            </p>
            <Link className="secondary-button" to="/dashboard/users">
              Відкрити учасників
            </Link>
          </div>
        ) : null}

        {isClient ? (
          <>
            <div className="heading-row">
              <h3>Мої абонементи</h3>
              <Link className="ghost-link" to="/dashboard/payments">
                Історія покупок
              </Link>
            </div>

            {subscriptionsQuery.isLoading ? <p className="muted">Завантаження абонементів...</p> : null}
            {subscriptionsQuery.isError ? (
              <p className="error-banner">
                {subscriptionsQuery.error instanceof Error ? subscriptionsQuery.error.message : "Помилка"}
              </p>
            ) : null}

            <div className="schedule-grid">
              {subscriptionsQuery.data?.length ? (
                subscriptionsQuery.data.map((subscription) => (
                  <article className="schedule-item" key={subscription.id}>
                    <p className="eyebrow">{subscription.plan?.title ?? subscription.type}</p>
                    <h2>{getStatusLabel(subscription.status)}</h2>
                    <p className="muted">
                      {new Date(subscription.start_date).toLocaleDateString("uk-UA")} -{" "}
                      {new Date(subscription.end_date).toLocaleDateString("uk-UA")}
                    </p>
                    <p className="muted">Залишилось відвідувань: {subscription.remaining_visits ?? "∞"}</p>
                    {subscription.status === "ACTIVE" ? (
                      <button className="ghost-link" onClick={() => setFreezeTarget(subscription.id)}>
                        Заморозити
                      </button>
                    ) : null}
                  </article>
                ))
              ) : (
                <article className="schedule-item empty-card">
                  <h2>Активних абонементів немає</h2>
                  <p className="muted">Оберіть один із планів вище, щоб відкрити свій доступ до клубу.</p>
                </article>
              )}
            </div>

            {freezeTarget ? (
              <div className="create-panel">
                <label>
                  Кількість днів заморозки
                  <input
                    type="number"
                    min={7}
                    max={30}
                    value={freezeDays}
                    onChange={(event) => setFreezeDays(Number(event.target.value))}
                  />
                </label>
                <button
                  className="secondary-button"
                  onClick={() => freezeMutation.mutate({ id: freezeTarget, days: freezeDays })}
                  disabled={freezeMutation.isPending}
                >
                  {freezeMutation.isPending ? "Оновлення..." : "Підтвердити заморозку"}
                </button>
                {freezeMutation.isError ? (
                  <p className="error-banner">
                    {freezeMutation.error instanceof Error ? freezeMutation.error.message : "Помилка заморозки"}
                  </p>
                ) : null}
              </div>
            ) : null}
          </>
        ) : null}

      </section>
    </main>
  );
}
