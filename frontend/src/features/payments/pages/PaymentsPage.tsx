import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { useAuthStore } from "../../auth";
import { getMyPayments, getPayments } from "../../../shared/api";

export function PaymentsPage() {
  const user = useAuthStore((state) => state.user);
  const isManagement = user?.role === "ADMIN" || user?.role === "OWNER";
  const [statusFilter, setStatusFilter] = useState("");
  const [methodFilter, setMethodFilter] = useState("");

  const paymentsQuery = useQuery({
    queryKey: isManagement ? ["payments-ledger", statusFilter, methodFilter] : ["my-payments"],
    queryFn: () =>
      isManagement
        ? getPayments({ status: statusFilter || undefined, method: methodFilter || undefined })
        : getMyPayments()
  });

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <p className="eyebrow">Покупки</p>
          <h1>{isManagement ? "Історія оплат клубу" : "Історія покупок"}</h1>
          <p className="muted">
            {isManagement
              ? "Тут зібрані всі оплати за абонементи й продажі клубу."
              : "У кабінеті лишилися тільки покупки абонементів. Нові оплати проходять зі сторінки абонементів."}
          </p>
        </div>

        {isManagement ? (
          <div className="create-panel">
            <label>
              Статус
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">Усі</option>
                <option value="SUCCESS">Підтверджено</option>
                <option value="FAILED">Неуспішно</option>
              </select>
            </label>
            <label>
              Метод
              <select value={methodFilter} onChange={(event) => setMethodFilter(event.target.value)}>
                <option value="">Усі</option>
                <option value="CARD">Картка</option>
                <option value="CASH">Готівка</option>
              </select>
            </label>
          </div>
        ) : (
          <div className="surface-card dashboard-focus-card">
            <p className="service-meta">Тільки абонементи</p>
            <h3>Абонементи продаються зі сторінки тарифів</h3>
            <p>
              Обери план, оформи покупку й повернись сюди, щоб побачити свою історію оплат.
            </p>
            <div className="dashboard-hero-actions">
              <Link className="secondary-button" to="/dashboard/subscriptions">
                Відкрити абонементи
              </Link>
              <Link className="ghost-link" to="/dashboard">
                На головну
              </Link>
            </div>
          </div>
        )}

        {paymentsQuery.isLoading ? <p className="muted">Завантаження оплат...</p> : null}
        {paymentsQuery.isError ? (
          <p className="error-banner">
            {paymentsQuery.error instanceof Error ? paymentsQuery.error.message : "Помилка"}
          </p>
        ) : null}

        <div className="schedule-grid">
          {paymentsQuery.data?.length ? (
            paymentsQuery.data.map((payment) => (
              <article className="schedule-item" key={payment.id}>
                <p className="eyebrow">{payment.status === "SUCCESS" ? "Підтверджено" : "Неуспішно"}</p>
                <h2>
                  {payment.currency} {payment.amount.toLocaleString("uk-UA")}
                </h2>
                <p className="muted">
                  {payment.method === "CASH" ? "Метод: готівка" : "Метод: картка"}
                </p>
                {payment.user ? (
                  <p className="muted">
                    {payment.user.first_name} {payment.user.last_name}
                  </p>
                ) : (
                  <p className="muted">Покупка абонемента</p>
                )}
                <p className="muted">{new Date(payment.created_at).toLocaleString("uk-UA")}</p>
              </article>
            ))
          ) : (
            <article className="schedule-item empty-card">
              <h2>Покупок ще немає</h2>
              <p className="muted">Після першого придбаного абонемента тут з’явиться історія оплат.</p>
            </article>
          )}
        </div>
      </section>
    </main>
  );
}
