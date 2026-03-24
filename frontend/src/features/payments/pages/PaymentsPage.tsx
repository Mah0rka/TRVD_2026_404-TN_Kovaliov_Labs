import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { useAuthStore } from "../../auth";
import { getMyPayments, getPayments } from "../../../shared/api";

export function PaymentsPage() {
  const user = useAuthStore((state) => state.user);
  const isManagement = user?.role === "ADMIN" || user?.role === "OWNER";
  const [statusFilter, setStatusFilter] = useState("");
  const [methodFilter, setMethodFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const paymentsQuery = useQuery({
    queryKey: isManagement ? ["payments-ledger", statusFilter, methodFilter] : ["my-payments"],
    queryFn: () =>
      isManagement
        ? getPayments({ status: statusFilter || undefined, method: methodFilter || undefined })
        : getMyPayments()
  });

  const paymentSummary = useMemo(() => {
    const payments = paymentsQuery.data ?? [];
    return {
      total: payments.length,
      success: payments.filter((payment) => payment.status === "SUCCESS").length,
      revenue: payments
        .filter((payment) => payment.status === "SUCCESS")
        .reduce((sum, payment) => sum + payment.amount, 0)
    };
  }, [paymentsQuery.data]);

  const filteredPayments = useMemo(() => {
    const payments = paymentsQuery.data ?? [];
    const normalizedQuery = searchTerm.trim().toLocaleLowerCase("uk-UA");

    if (!normalizedQuery) {
      return payments;
    }

    return payments.filter((payment) => {
      const searchableValue = payment.user
        ? [
            payment.user.first_name,
            payment.user.last_name,
            `${payment.user.first_name} ${payment.user.last_name}`,
            payment.user.phone ?? ""
          ]
            .join(" ")
            .toLocaleLowerCase("uk-UA")
        : "";

      return searchableValue.includes(normalizedQuery);
    });
  }, [paymentsQuery.data, searchTerm]);

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <p className="eyebrow">Покупки</p>
          <h1>{isManagement ? "Історія оплат клубу" : "Історія покупок"}</h1>
          <p className="muted">
            {isManagement
              ? "Усі оплати за абонементи зібрані в одному табличному журналі."
              : "Тут видно всі ваші придбані абонементи та дату кожної покупки."}
          </p>
        </div>

        <div className="stats-grid compact-stats-grid">
          <article className="stat-card">
            <span className="stat-label">Усього оплат</span>
            <strong className="stat-value">{paymentSummary.total}</strong>
          </article>
          <article className="stat-card">
            <span className="stat-label">Підтверджено</span>
            <strong className="stat-value">{paymentSummary.success}</strong>
          </article>
          <article className="stat-card">
            <span className="stat-label">Сума підтверджених</span>
            <strong className="stat-value">UAH {paymentSummary.revenue.toLocaleString("uk-UA")}</strong>
          </article>
        </div>

        {isManagement ? (
          <div className="surface-card filter-toolbar-card">
            <div className="table-toolbar table-toolbar-wide">
              <div className="table-toolbar-fields">
                <label className="toolbar-field">
                  <span className="toolbar-label">Статус</span>
                  <span className="toolbar-select-shell">
                    <select
                      className="toolbar-control"
                      aria-label="Статус"
                      value={statusFilter}
                      onChange={(event) => setStatusFilter(event.target.value)}
                    >
                      <option value="">Усі</option>
                      <option value="SUCCESS">Підтверджено</option>
                      <option value="FAILED">Неуспішно</option>
                    </select>
                    <span className="toolbar-select-caret" aria-hidden="true">
                      ▾
                    </span>
                  </span>
                </label>
                <label className="toolbar-field">
                  <span className="toolbar-label">Метод</span>
                  <span className="toolbar-select-shell">
                    <select
                      className="toolbar-control"
                      aria-label="Метод"
                      value={methodFilter}
                      onChange={(event) => setMethodFilter(event.target.value)}
                    >
                      <option value="">Усі</option>
                      <option value="CARD">Картка</option>
                      <option value="CASH">Готівка</option>
                    </select>
                    <span className="toolbar-select-caret" aria-hidden="true">
                      ▾
                    </span>
                  </span>
                </label>
                <label className="toolbar-field toolbar-field-search">
                  <span className="toolbar-label">Пошук</span>
                  <span className="toolbar-search-shell">
                    <span className="toolbar-search-icon" aria-hidden="true">
                      ⌕
                    </span>
                    <input
                      className="toolbar-control toolbar-search-input"
                      aria-label="Пошук"
                      value={searchTerm}
                      onChange={(event) => setSearchTerm(event.target.value)}
                      placeholder="Ім'я, прізвище або телефон"
                    />
                  </span>
                </label>
              </div>
              <span className="toolbar-count">{filteredPayments.length} оплат</span>
            </div>
          </div>
        ) : (
          <div className="surface-card dashboard-focus-card">
            <p className="service-meta">Тільки абонементи</p>
            <h3>Нові покупки робляться зі сторінки абонементів</h3>
            <p>Тут лишається історія всіх уже оформлених покупок, а не касова форма.</p>
            <div className="dashboard-hero-actions">
              <Link className="secondary-button" to="/dashboard/subscriptions">
                Відкрити абонементи
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

        <div className="surface-card table-card">
          <div className="management-table">
            <div className="management-table-head payments-table-layout">
              <span>Сума</span>
              <span>Метод</span>
              <span>Статус</span>
              <span>{isManagement ? "Учасник" : "Призначення"}</span>
              <span>Дата</span>
            </div>

            {filteredPayments.length ? (
              filteredPayments.map((payment) => (
                <article key={payment.id} className="management-table-row payments-table-layout">
                  <div className="management-table-cell" data-label="Сума">
                    <strong>
                      {payment.currency} {payment.amount.toLocaleString("uk-UA")}
                    </strong>
                  </div>
                  <div className="management-table-cell" data-label="Метод">
                    <span>{payment.method === "CASH" ? "Готівка" : "Картка"}</span>
                  </div>
                  <div className="management-table-cell" data-label="Статус">
                    <span className={payment.status === "SUCCESS" ? "status-pill success" : "status-pill warning"}>
                      {payment.status === "SUCCESS" ? "Підтверджено" : "Неуспішно"}
                    </span>
                  </div>
                  <div className="management-table-cell" data-label={isManagement ? "Учасник" : "Призначення"}>
                    {payment.user ? (
                      <>
                        <strong>
                          {payment.user.first_name} {payment.user.last_name}
                        </strong>
                        <span className="muted">
                          {payment.user.phone ? `${payment.user.email} · ${payment.user.phone}` : payment.user.email}
                        </span>
                      </>
                    ) : (
                      <span>Покупка абонемента</span>
                    )}
                  </div>
                  <div className="management-table-cell" data-label="Дата">
                    <span>{new Date(payment.created_at).toLocaleString("uk-UA")}</span>
                  </div>
                </article>
              ))
            ) : (
              <article className="management-table-empty">
                <h3>Покупок ще немає</h3>
                <p className="muted">Після першого придбаного абонемента тут з’явиться історія оплат.</p>
              </article>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
