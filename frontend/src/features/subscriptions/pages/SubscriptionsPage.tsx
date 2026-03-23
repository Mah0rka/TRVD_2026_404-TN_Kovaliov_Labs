import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { freezeSubscription, getSubscriptions, purchaseSubscription } from "../../../shared/api";

const plans = [
  {
    type: "MONTHLY" as const,
    title: "Місячний",
    price: "990",
    visits: "12 занять",
    duration: "30 днів"
  },
  {
    type: "YEARLY" as const,
    title: "Річний",
    price: "1490",
    visits: "Безліміт",
    duration: "365 днів"
  },
  {
    type: "PAY_AS_YOU_GO" as const,
    title: "Разове відвідування",
    price: "190",
    visits: "1 заняття",
    duration: "30 днів"
  }
];

function getSubscriptionTitle(type: (typeof plans)[number]["type"]): string {
  return plans.find((plan) => plan.type === type)?.title ?? type;
}

function getStatusLabel(status: string): string {
  if (status === "ACTIVE") {
    return "Активний";
  }

  if (status === "FROZEN") {
    return "На паузі";
  }

  return "Завершений";
}

export function SubscriptionsPage() {
  const queryClient = useQueryClient();
  const [freezeTarget, setFreezeTarget] = useState<string | null>(null);
  const [freezeDays, setFreezeDays] = useState(7);

  const subscriptionsQuery = useQuery({
    queryKey: ["my-subscriptions"],
    queryFn: getSubscriptions
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

  const currentSubscriptions = subscriptionsQuery.data ?? [];
  const blockingSubscription = currentSubscriptions.find(
    (subscription) => subscription.status === "ACTIVE" || subscription.status === "FROZEN"
  );

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <p className="eyebrow">Абонементи</p>
          <h1>Абонементи клубу</h1>
          <p className="muted">
            Клуб продає тільки абонементи. Вибери план, оформи покупку й керуй ним у кабінеті.
          </p>
        </div>

        <div className="schedule-grid">
          {plans.map((plan) => (
            <article className="schedule-item" key={plan.type}>
              <p className="eyebrow">{plan.duration}</p>
              <h2>{plan.title}</h2>
              <p className="muted">
                {plan.visits} · UAH {plan.price}
              </p>
              <button
                className="secondary-button"
                onClick={() => purchaseMutation.mutate(plan.type)}
                disabled={purchaseMutation.isPending || Boolean(blockingSubscription)}
              >
                {purchaseMutation.isPending
                  ? "Оформлення..."
                  : blockingSubscription
                    ? "Спочатку завершіть поточний план"
                    : "Купити абонемент"}
              </button>
            </article>
          ))}
        </div>

        {blockingSubscription ? (
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
                <p className="eyebrow">{getSubscriptionTitle(subscription.type)}</p>
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
      </section>
    </main>
  );
}
