import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createUser,
  deleteClientSubscription,
  getManagedSubscriptions,
  getPayments,
  getSubscriptionPlans,
  getUsers,
  issueClientSubscription,
  restoreClientSubscription,
  type CurrentUser,
  type MembershipPlan,
  type Subscription,
  type UserRole,
  updateClientSubscription,
  updateUser
} from "../../../shared/api";

const roles: UserRole[] = ["CLIENT", "TRAINER", "ADMIN", "OWNER"];

function getAccessLabel(role: UserRole): string {
  if (role === "CLIENT") return "Клієнт";
  if (role === "TRAINER") return "Тренер";
  if (role === "ADMIN") return "Адміністратор";
  return "Власник";
}

function getSubscriptionStatusLabel(status: Subscription["status"]): string {
  if (status === "ACTIVE") return "Активний";
  if (status === "FROZEN") return "На паузі";
  return "Завершений";
}

function getPlanTypeLabel(type: MembershipPlan["type"]): string {
  if (type === "MONTHLY") return "Місячний";
  if (type === "YEARLY") return "Річний";
  return "Разовий";
}

function getAuditLabel(subscription: Subscription): string {
  if (subscription.restored_by && subscription.restored_at) {
    return `Відновив ${subscription.restored_by.first_name} ${subscription.restored_by.last_name} · ${new Date(subscription.restored_at).toLocaleString("uk-UA")}`;
  }
  if (subscription.deleted_by && subscription.deleted_at) {
    return `Видалив ${subscription.deleted_by.first_name} ${subscription.deleted_by.last_name} · ${new Date(subscription.deleted_at).toLocaleString("uk-UA")}`;
  }
  if (subscription.last_modified_by && subscription.last_modified_at) {
    return `Редагував ${subscription.last_modified_by.first_name} ${subscription.last_modified_by.last_name} · ${new Date(subscription.last_modified_at).toLocaleString("uk-UA")}`;
  }
  return "Без змін менеджером";
}

function emptyCreateForm() {
  return {
    email: "",
    password: "Password123!",
    first_name: "",
    last_name: "",
    phone: "",
    role: "CLIENT" as UserRole,
    is_verified: true
  };
}

function emptyEditForm() {
  return {
    first_name: "",
    last_name: "",
    phone: "",
    role: "CLIENT" as UserRole,
    is_verified: true
  };
}

function emptyIssueForm() {
  return {
    plan_id: "",
    start_date: "",
    end_date: "",
    status: "ACTIVE" as Subscription["status"],
    total_visits: "",
    remaining_visits: ""
  };
}

function emptySubscriptionEditForm() {
  return {
    plan_id: "",
    start_date: "",
    end_date: "",
    status: "ACTIVE" as Subscription["status"],
    total_visits: "",
    remaining_visits: ""
  };
}

export function UsersPage() {
  const queryClient = useQueryClient();
  const [filterRole, setFilterRole] = useState<UserRole | "ALL">("ALL");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<CurrentUser | null>(null);
  const [editingSubscriptionId, setEditingSubscriptionId] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState(emptyCreateForm());
  const [editForm, setEditForm] = useState(emptyEditForm());
  const [issueForm, setIssueForm] = useState(emptyIssueForm());
  const [subscriptionEditForm, setSubscriptionEditForm] = useState(emptySubscriptionEditForm());

  const allUsersQuery = useQuery({
    queryKey: ["users", "all"],
    queryFn: () => getUsers()
  });

  const usersQuery = useQuery({
    queryKey: ["users", filterRole],
    queryFn: () => getUsers(filterRole === "ALL" ? undefined : filterRole)
  });

  const plansQuery = useQuery({
    queryKey: ["membership-plans"],
    queryFn: getSubscriptionPlans
  });

  const subscriptionsQuery = useQuery({
    queryKey: ["managed-subscriptions", selectedUser?.id],
    queryFn: () => getManagedSubscriptions({ userId: selectedUser?.id, includeDeleted: true }),
    enabled: Boolean(selectedUser?.id)
  });

  const paymentsQuery = useQuery({
    queryKey: ["payments-ledger", selectedUser?.id],
    queryFn: () => getPayments({ userId: selectedUser?.id }),
    enabled: Boolean(selectedUser?.id)
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setCreateForm(emptyCreateForm());
      setIsCreateOpen(false);
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, payload }: { userId: string; payload: Parameters<typeof updateUser>[1] }) =>
      updateUser(userId, payload),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setSelectedUser(user);
      setEditForm({
        first_name: user.first_name,
        last_name: user.last_name,
        phone: user.phone ?? "",
        role: user.role,
        is_verified: user.is_verified
      });
    }
  });

  const issueMutation = useMutation({
    mutationFn: issueClientSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-subscriptions", selectedUser?.id] });
      setIssueForm(emptyIssueForm());
    }
  });

  const updateSubscriptionMutation = useMutation({
    mutationFn: ({
      subscriptionId,
      payload
    }: {
      subscriptionId: string;
      payload: Parameters<typeof updateClientSubscription>[1];
    }) => updateClientSubscription(subscriptionId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-subscriptions", selectedUser?.id] });
      setEditingSubscriptionId(null);
      setSubscriptionEditForm(emptySubscriptionEditForm());
    }
  });

  const deleteSubscriptionMutation = useMutation({
    mutationFn: deleteClientSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-subscriptions", selectedUser?.id] });
    }
  });

  const restoreSubscriptionMutation = useMutation({
    mutationFn: restoreClientSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-subscriptions", selectedUser?.id] });
    }
  });

  const roleStats = useMemo(() => {
    const users = allUsersQuery.data ?? [];
    return roles.map((role) => ({
      role,
      count: users.filter((user) => user.role === role).length
    }));
  }, [allUsersQuery.data]);

  const activePlans = useMemo(
    () => (plansQuery.data ?? []).filter((plan) => plan.is_active),
    [plansQuery.data]
  );

  function selectUser(user: CurrentUser) {
    setSelectedUser(user);
    setEditForm({
      first_name: user.first_name,
      last_name: user.last_name,
      phone: user.phone ?? "",
      role: user.role,
      is_verified: user.is_verified
    });
    setEditingSubscriptionId(null);
    setIssueForm(emptyIssueForm());
    setSubscriptionEditForm(emptySubscriptionEditForm());
  }

  function startEditingSubscription(subscription: Subscription) {
    setEditingSubscriptionId(subscription.id);
    setSubscriptionEditForm({
      plan_id: subscription.plan_id ?? "",
      start_date: subscription.start_date.slice(0, 16),
      end_date: subscription.end_date.slice(0, 16),
      status: subscription.status,
      total_visits: subscription.total_visits === null ? "" : String(subscription.total_visits),
      remaining_visits: subscription.remaining_visits === null ? "" : String(subscription.remaining_visits)
    });
  }

  function buildIssuePayload() {
    return {
      user_id: selectedUser?.id ?? "",
      plan_id: issueForm.plan_id,
      start_date: issueForm.start_date ? new Date(issueForm.start_date).toISOString() : undefined,
      end_date: issueForm.end_date ? new Date(issueForm.end_date).toISOString() : undefined,
      status: issueForm.status,
      total_visits: issueForm.total_visits === "" ? null : Number(issueForm.total_visits),
      remaining_visits: issueForm.remaining_visits === "" ? null : Number(issueForm.remaining_visits)
    };
  }

  function buildSubscriptionUpdatePayload() {
    return {
      plan_id: subscriptionEditForm.plan_id || undefined,
      start_date: subscriptionEditForm.start_date
        ? new Date(subscriptionEditForm.start_date).toISOString()
        : undefined,
      end_date: subscriptionEditForm.end_date
        ? new Date(subscriptionEditForm.end_date).toISOString()
        : undefined,
      status: subscriptionEditForm.status,
      total_visits: subscriptionEditForm.total_visits === "" ? null : Number(subscriptionEditForm.total_visits),
      remaining_visits:
        subscriptionEditForm.remaining_visits === ""
          ? null
          : Number(subscriptionEditForm.remaining_visits)
    };
  }

  return (
    <section className="panel-stack">
      <div className="panel-heading">
        <p className="eyebrow">Users</p>
        <h2>Учасники клубу</h2>
        <p className="muted">
          Повна картка учасника, історія оплат, придбані абонементи та всі дії менеджера в одному місці.
        </p>
      </div>

      <div className="stats-grid">
        {roleStats.map((item) => (
          <article key={item.role} className="stat-card">
            <span className="stat-label">{getAccessLabel(item.role)}</span>
            <strong className="stat-value">{item.count}</strong>
          </article>
        ))}
      </div>

      <div className="surface-card create-user-card">
        <div className="heading-row">
          <div>
            <h3>Створити користувача</h3>
            <p className="muted">Новий акаунт створюється тільки коли це справді потрібно менеджеру.</p>
          </div>
          <button
            className="ghost-link create-user-toggle"
            type="button"
            aria-label={isCreateOpen ? "Сховати форму створення" : "Відкрити форму створення"}
            aria-expanded={isCreateOpen}
            aria-controls="create-user-panel"
            onClick={() => setIsCreateOpen((current) => !current)}
          >
            <span className={isCreateOpen ? "create-user-toggle-icon open" : "create-user-toggle-icon"}>&gt;</span>
          </button>
        </div>

        {isCreateOpen ? (
          <div id="create-user-panel" className="form-grid">
            <label>
              Email
              <input value={createForm.email} onChange={(event) => setCreateForm((current) => ({ ...current, email: event.target.value }))} />
            </label>
            <label>
              Пароль
              <input value={createForm.password} onChange={(event) => setCreateForm((current) => ({ ...current, password: event.target.value }))} />
            </label>
            <label>
              Ім'я
              <input value={createForm.first_name} onChange={(event) => setCreateForm((current) => ({ ...current, first_name: event.target.value }))} />
            </label>
            <label>
              Прізвище
              <input value={createForm.last_name} onChange={(event) => setCreateForm((current) => ({ ...current, last_name: event.target.value }))} />
            </label>
            <label>
              Телефон
              <input value={createForm.phone} onChange={(event) => setCreateForm((current) => ({ ...current, phone: event.target.value }))} />
            </label>
            <label>
              Доступ
              <select value={createForm.role} onChange={(event) => setCreateForm((current) => ({ ...current, role: event.target.value as UserRole }))}>
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {getAccessLabel(role)}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="secondary-button"
              type="button"
              disabled={!createForm.email || !createForm.first_name || !createForm.last_name || createMutation.isPending}
              onClick={() => createMutation.mutate(createForm)}
            >
              {createMutation.isPending ? "Створення..." : "Створити"}
            </button>
          </div>
        ) : null}
      </div>

      <div className="surface-card table-card">
        <div className="table-header">
          <h3>Список користувачів</h3>
          <div className="heading-row">
            <label>
              Фільтр списку
              <select value={filterRole} onChange={(event) => setFilterRole(event.target.value as UserRole | "ALL")}>
                <option value="ALL">Усі учасники</option>
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {getAccessLabel(role)}
                  </option>
                ))}
              </select>
            </label>
            <span className="muted">{usersQuery.data?.length ?? 0} записів</span>
          </div>
        </div>

        {usersQuery.isLoading ? <p className="muted">Завантаження користувачів...</p> : null}
        {usersQuery.isError ? <p className="error-banner">{usersQuery.error instanceof Error ? usersQuery.error.message : "Помилка"}</p> : null}

        <div className="management-table">
          <div className="management-table-head users-table-layout">
            <span>Учасник</span>
            <span>Контакти</span>
            <span>Доступ</span>
            <span>Статус</span>
            <span>Створено</span>
            <span>Дії</span>
          </div>
          {usersQuery.data?.map((user) => (
            <article key={user.id} className="management-table-row users-table-layout">
              <div className="management-table-cell">
                <strong>{user.first_name} {user.last_name}</strong>
                <span className="muted">ID: {user.id.slice(0, 8)}</span>
              </div>
              <div className="management-table-cell">
                <span>{user.email}</span>
                <span className="muted">{user.phone || "Телефон не вказано"}</span>
              </div>
              <div className="management-table-cell">
                <span>{getAccessLabel(user.role)}</span>
              </div>
              <div className="management-table-cell">
                <span className={user.is_verified ? "status-pill success" : "status-pill warning"}>
                  {user.is_verified ? "Підтверджено" : "Очікує"}
                </span>
              </div>
              <div className="management-table-cell">
                <span>{new Date(user.created_at).toLocaleDateString("uk-UA")}</span>
              </div>
              <div className="management-table-cell">
                <button className="ghost-link" onClick={() => selectUser(user)}>Редагувати</button>
              </div>
            </article>
          ))}
        </div>
      </div>

      {selectedUser ? (
        <div className="detail-layout">
          <div className="surface-card detail-panel">
            <div className="heading-row">
              <div>
                <h3>Профіль учасника</h3>
                <p className="muted">Повна інформація по {selectedUser.first_name} {selectedUser.last_name}.</p>
              </div>
              <button className="ghost-link" onClick={() => setSelectedUser(null)}>Закрити</button>
            </div>

            <div className="summary-grid">
              <div className="summary-item"><span className="stat-label">Ім'я</span><strong>{selectedUser.first_name} {selectedUser.last_name}</strong></div>
              <div className="summary-item"><span className="stat-label">Email</span><strong>{selectedUser.email}</strong></div>
              <div className="summary-item"><span className="stat-label">Телефон</span><strong>{selectedUser.phone || "Не вказано"}</strong></div>
              <div className="summary-item"><span className="stat-label">Доступ</span><strong>{getAccessLabel(selectedUser.role)}</strong></div>
              <div className="summary-item"><span className="stat-label">Статус</span><strong>{selectedUser.is_verified ? "Підтверджено" : "Не підтверджено"}</strong></div>
              <div className="summary-item"><span className="stat-label">Створено</span><strong>{new Date(selectedUser.created_at).toLocaleString("uk-UA")}</strong></div>
            </div>

            <div className="form-grid">
              <div className="heading-row"><h3>Редагування учасника</h3></div>
              <label>
                Ім'я
                <input value={editForm.first_name} onChange={(event) => setEditForm((current) => ({ ...current, first_name: event.target.value }))} />
              </label>
              <label>
                Прізвище
                <input value={editForm.last_name} onChange={(event) => setEditForm((current) => ({ ...current, last_name: event.target.value }))} />
              </label>
              <label>
                Телефон
                <input value={editForm.phone} onChange={(event) => setEditForm((current) => ({ ...current, phone: event.target.value }))} />
              </label>
              <label>
                Доступ
                <select value={editForm.role} onChange={(event) => setEditForm((current) => ({ ...current, role: event.target.value as UserRole }))}>
                  {roles.map((role) => (
                    <option key={role} value={role}>
                      {getAccessLabel(role)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="checkbox-line">
                <input type="checkbox" checked={editForm.is_verified} onChange={(event) => setEditForm((current) => ({ ...current, is_verified: event.target.checked }))} />
                Підтверджений користувач
              </label>
              <button
                className="secondary-button"
                type="button"
                disabled={updateMutation.isPending}
                onClick={() =>
                  updateMutation.mutate({
                    userId: selectedUser.id,
                    payload: {
                      first_name: editForm.first_name,
                      last_name: editForm.last_name,
                      phone: editForm.phone,
                      role: editForm.role,
                      is_verified: editForm.is_verified
                    }
                  })
                }
              >
                {updateMutation.isPending ? "Оновлення..." : "Зберегти зміни"}
              </button>
            </div>
          </div>

          <div className="surface-card detail-panel">
            <div className="heading-row">
              <div>
                <h3>Керування абонементами</h3>
                <p className="muted">Видача, редагування, видалення й відновлення абонементів цього учасника.</p>
              </div>
            </div>

            <div className="form-grid">
              <div className="heading-row"><h3>Видати абонемент</h3></div>
              <label>
                Абонемент для видачі
                <select value={issueForm.plan_id} onChange={(event) => setIssueForm((current) => ({ ...current, plan_id: event.target.value }))}>
                  <option value="">Оберіть план</option>
                  {activePlans.map((plan) => (
                    <option key={plan.id} value={plan.id}>
                      {plan.title} · {getPlanTypeLabel(plan.type)} · {plan.is_public ? "публічний" : "непублічний"}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Початок
                <input type="datetime-local" value={issueForm.start_date} onChange={(event) => setIssueForm((current) => ({ ...current, start_date: event.target.value }))} />
              </label>
              <label>
                Кінець
                <input type="datetime-local" value={issueForm.end_date} onChange={(event) => setIssueForm((current) => ({ ...current, end_date: event.target.value }))} />
              </label>
              <label>
                Статус для видачі
                <select value={issueForm.status} onChange={(event) => setIssueForm((current) => ({ ...current, status: event.target.value as Subscription["status"] }))}>
                  <option value="ACTIVE">Активний</option>
                  <option value="FROZEN">На паузі</option>
                  <option value="EXPIRED">Завершений</option>
                </select>
              </label>
              <label>
                Всього відвідувань
                <input type="number" min={0} value={issueForm.total_visits} onChange={(event) => setIssueForm((current) => ({ ...current, total_visits: event.target.value }))} />
              </label>
              <label>
                Залишилось відвідувань
                <input type="number" min={0} value={issueForm.remaining_visits} onChange={(event) => setIssueForm((current) => ({ ...current, remaining_visits: event.target.value }))} />
              </label>
              <button className="secondary-button" type="button" disabled={issueMutation.isPending || !issueForm.plan_id} onClick={() => issueMutation.mutate(buildIssuePayload())}>
                {issueMutation.isPending ? "Видача..." : "Видати абонемент"}
              </button>
            </div>

            <div className="stack-table-card">
              <div className="heading-row">
                <h3>Історія придбаних абонементів</h3>
                <span className="muted">{subscriptionsQuery.data?.length ?? 0} записів</span>
              </div>

              {subscriptionsQuery.isLoading ? <p className="muted">Завантаження абонементів...</p> : null}
              {subscriptionsQuery.isError ? <p className="error-banner">{subscriptionsQuery.error instanceof Error ? subscriptionsQuery.error.message : "Помилка"}</p> : null}

              <div className="management-table">
                <div className="management-table-head subscriptions-table-layout">
                  <span>Абонемент</span>
                  <span>Період</span>
                  <span>Статус</span>
                  <span>Відвідування</span>
                  <span>Аудит</span>
                  <span>Дії</span>
                </div>
                {subscriptionsQuery.data?.map((subscription) => (
                  <article key={subscription.id} className="management-table-row subscriptions-table-layout">
                    <div className="management-table-cell">
                      <strong>{subscription.plan?.title ?? subscription.type}</strong>
                      <span className="muted">
                        {subscription.plan
                          ? `${getPlanTypeLabel(subscription.plan.type)} · ${subscription.plan.currency} ${subscription.plan.price}`
                          : "План недоступний"}
                      </span>
                    </div>
                    <div className="management-table-cell">
                      <span>{new Date(subscription.start_date).toLocaleDateString("uk-UA")}</span>
                      <span className="muted">{new Date(subscription.end_date).toLocaleDateString("uk-UA")}</span>
                    </div>
                    <div className="management-table-cell">
                      <span className={subscription.deleted_at ? "status-pill warning" : "status-pill success"}>
                        {subscription.deleted_at ? "Видалений" : getSubscriptionStatusLabel(subscription.status)}
                      </span>
                    </div>
                    <div className="management-table-cell">
                      <span>{subscription.remaining_visits ?? "∞"} / {subscription.total_visits ?? "∞"}</span>
                    </div>
                    <div className="management-table-cell">
                      <span>{getAuditLabel(subscription)}</span>
                    </div>
                    <div className="management-table-cell stacked-actions">
                      {!subscription.deleted_at ? (
                        <>
                          <button className="ghost-link" onClick={() => startEditingSubscription(subscription)}>Редагувати абонемент</button>
                          <button className="danger-link" onClick={() => deleteSubscriptionMutation.mutate(subscription.id)} disabled={deleteSubscriptionMutation.isPending}>Видалити абонемент</button>
                        </>
                      ) : (
                        <button className="ghost-link" onClick={() => restoreSubscriptionMutation.mutate(subscription.id)} disabled={restoreSubscriptionMutation.isPending}>
                          Відновити абонемент
                        </button>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>

            {editingSubscriptionId ? (
              <div className="form-grid">
                <div className="heading-row">
                  <h3>Редагування абонемента</h3>
                  <button className="ghost-link" onClick={() => { setEditingSubscriptionId(null); setSubscriptionEditForm(emptySubscriptionEditForm()); }}>
                    Скасувати
                  </button>
                </div>
                <label>
                  План
                  <select value={subscriptionEditForm.plan_id} onChange={(event) => setSubscriptionEditForm((current) => ({ ...current, plan_id: event.target.value }))}>
                    <option value="">Без зміни плану</option>
                    {activePlans.map((plan) => (
                      <option key={plan.id} value={plan.id}>
                        {plan.title}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Початок
                  <input type="datetime-local" value={subscriptionEditForm.start_date} onChange={(event) => setSubscriptionEditForm((current) => ({ ...current, start_date: event.target.value }))} />
                </label>
                <label>
                  Кінець
                  <input type="datetime-local" value={subscriptionEditForm.end_date} onChange={(event) => setSubscriptionEditForm((current) => ({ ...current, end_date: event.target.value }))} />
                </label>
                <label>
                  Статус редагування
                  <select value={subscriptionEditForm.status} onChange={(event) => setSubscriptionEditForm((current) => ({ ...current, status: event.target.value as Subscription["status"] }))}>
                    <option value="ACTIVE">Активний</option>
                    <option value="FROZEN">На паузі</option>
                    <option value="EXPIRED">Завершений</option>
                  </select>
                </label>
                <label>
                  Всього відвідувань
                  <input type="number" min={0} value={subscriptionEditForm.total_visits} onChange={(event) => setSubscriptionEditForm((current) => ({ ...current, total_visits: event.target.value }))} />
                </label>
                <label>
                  Залишилось відвідувань
                  <input type="number" min={0} value={subscriptionEditForm.remaining_visits} onChange={(event) => setSubscriptionEditForm((current) => ({ ...current, remaining_visits: event.target.value }))} />
                </label>
                <button
                  className="secondary-button"
                  disabled={updateSubscriptionMutation.isPending}
                  onClick={() => updateSubscriptionMutation.mutate({ subscriptionId: editingSubscriptionId, payload: buildSubscriptionUpdatePayload() })}
                >
                  {updateSubscriptionMutation.isPending ? "Збереження..." : "Зберегти абонемент"}
                </button>
              </div>
            ) : null}

            <div className="stack-table-card">
              <div className="heading-row">
                <h3>Історія оплат учасника</h3>
                <span className="muted">{paymentsQuery.data?.length ?? 0} оплат</span>
              </div>
              {paymentsQuery.isLoading ? <p className="muted">Завантаження оплат...</p> : null}
              {paymentsQuery.isError ? <p className="error-banner">{paymentsQuery.error instanceof Error ? paymentsQuery.error.message : "Помилка"}</p> : null}

              <div className="management-table">
                <div className="management-table-head payments-table-layout">
                  <span>Сума</span>
                  <span>Метод</span>
                  <span>Статус</span>
                  <span>Дата</span>
                </div>
                {paymentsQuery.data?.map((payment) => (
                  <article key={payment.id} className="management-table-row payments-table-layout">
                    <div className="management-table-cell">
                      <strong>{payment.currency} {payment.amount.toLocaleString("uk-UA")}</strong>
                    </div>
                    <div className="management-table-cell">
                      <span>{payment.method === "CASH" ? "Готівка" : "Картка"}</span>
                    </div>
                    <div className="management-table-cell">
                      <span className={payment.status === "SUCCESS" ? "status-pill success" : "status-pill warning"}>
                        {payment.status === "SUCCESS" ? "Підтверджено" : "Неуспішно"}
                      </span>
                    </div>
                    <div className="management-table-cell">
                      <span>{new Date(payment.created_at).toLocaleString("uk-UA")}</span>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
