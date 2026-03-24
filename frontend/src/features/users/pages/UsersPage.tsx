import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createUser,
  deleteUser,
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
import { useAuthStore } from "../../auth/model/store";

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

function getSubscriptionPriority(subscription: Subscription): number {
  if (subscription.deleted_at) return 0;
  if (subscription.status === "ACTIVE") return 4;
  if (subscription.status === "FROZEN") return 3;
  if (subscription.status === "EXPIRED") return 2;
  return 1;
}

function getUserSearchValue(user: CurrentUser): string {
  return [
    user.first_name,
    user.last_name,
    `${user.first_name} ${user.last_name}`,
    user.phone ?? ""
  ]
    .join(" ")
    .toLocaleLowerCase("uk-UA");
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

type DestructiveConfirmation =
  | { kind: "user"; user: CurrentUser }
  | { kind: "subscription"; subscription: Subscription };

export function UsersPage() {
  const queryClient = useQueryClient();
  const authUser = useAuthStore((state) => state.user);
  const isAuthReady = useAuthStore((state) => state.isReady);
  const [filterRole, setFilterRole] = useState<UserRole | "ALL">("ALL");
  const [userSearchTerm, setUserSearchTerm] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<CurrentUser | null>(null);
  const [editingSubscriptionId, setEditingSubscriptionId] = useState<string | null>(null);
  const [confirmationState, setConfirmationState] = useState<DestructiveConfirmation | null>(null);
  const [confirmationInput, setConfirmationInput] = useState("");
  const [createForm, setCreateForm] = useState(emptyCreateForm());
  const [editForm, setEditForm] = useState(emptyEditForm());
  const [issueForm, setIssueForm] = useState(emptyIssueForm());
  const [subscriptionEditForm, setSubscriptionEditForm] = useState(emptySubscriptionEditForm());
  const canLoadManagementData = Boolean(isAuthReady && authUser);

  const allUsersQuery = useQuery({
    queryKey: ["users", "all"],
    queryFn: () => getUsers(),
    enabled: canLoadManagementData
  });

  const usersQuery = useQuery({
    queryKey: ["users", filterRole],
    queryFn: () => getUsers(filterRole === "ALL" ? undefined : filterRole),
    enabled: canLoadManagementData
  });

  const plansQuery = useQuery({
    queryKey: ["membership-plans"],
    queryFn: getSubscriptionPlans,
    enabled: canLoadManagementData
  });

  const allSubscriptionsQuery = useQuery({
    queryKey: ["managed-subscriptions", "all-users"],
    queryFn: () => getManagedSubscriptions({ includeDeleted: true }),
    enabled: canLoadManagementData
  });

  const subscriptionsQuery = useQuery({
    queryKey: ["managed-subscriptions", selectedUser?.id],
    queryFn: () => getManagedSubscriptions({ userId: selectedUser?.id, includeDeleted: true }),
    enabled: Boolean(canLoadManagementData && selectedUser?.id)
  });

  const paymentsQuery = useQuery({
    queryKey: ["payments-ledger", selectedUser?.id],
    queryFn: () => getPayments({ userId: selectedUser?.id }),
    enabled: Boolean(canLoadManagementData && selectedUser?.id)
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
      queryClient.invalidateQueries({ queryKey: ["managed-subscriptions", "all-users"] });
      setConfirmationState(null);
      setConfirmationInput("");
    }
  });

  const restoreSubscriptionMutation = useMutation({
    mutationFn: restoreClientSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-subscriptions", selectedUser?.id] });
    }
  });

  const deleteUserMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: (_, deletedUserId) => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      queryClient.invalidateQueries({ queryKey: ["managed-subscriptions", "all-users"] });
      queryClient.invalidateQueries({ queryKey: ["payments-ledger"] });
      if (selectedUser?.id === deletedUserId) {
        setSelectedUser(null);
      }
      setConfirmationState(null);
      setConfirmationInput("");
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

  const subscriptionsByUser = useMemo(() => {
    const map = new Map<string, Subscription>();

    for (const subscription of allSubscriptionsQuery.data ?? []) {
      const current = map.get(subscription.user_id);
      if (!current) {
        map.set(subscription.user_id, subscription);
        continue;
      }

      const currentPriority = getSubscriptionPriority(current);
      const nextPriority = getSubscriptionPriority(subscription);

      if (
        nextPriority > currentPriority ||
        (nextPriority === currentPriority &&
          new Date(subscription.updated_at).getTime() > new Date(current.updated_at).getTime())
      ) {
        map.set(subscription.user_id, subscription);
      }
    }

    return map;
  }, [allSubscriptionsQuery.data]);

  const filteredUsers = useMemo(() => {
    const users = usersQuery.data ?? [];
    const normalizedQuery = userSearchTerm.trim().toLocaleLowerCase("uk-UA");

    if (!normalizedQuery) {
      return users;
    }

    return users.filter((user) => getUserSearchValue(user).includes(normalizedQuery));
  }, [userSearchTerm, usersQuery.data]);

  useEffect(() => {
    if (!selectedUser) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSelectedUser(null);
      }
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [selectedUser]);

  useEffect(() => {
    if (!authUser) {
      setSelectedUser(null);
      setEditingSubscriptionId(null);
      setConfirmationState(null);
      setConfirmationInput("");
    }
  }, [authUser]);

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

  function openUserDeleteConfirmation(user: CurrentUser) {
    setConfirmationInput("");
    setConfirmationState({ kind: "user", user });
  }

  function openSubscriptionDeleteConfirmation(subscription: Subscription) {
    setConfirmationInput("");
    setConfirmationState({ kind: "subscription", subscription });
  }

  function closeConfirmationModal() {
    setConfirmationState(null);
    setConfirmationInput("");
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

  const confirmationExpectedValue =
    confirmationState?.kind === "user"
      ? confirmationState.user.email
      : confirmationState
        ? "ВИДАЛИТИ"
        : "";

  const confirmationTitle =
    confirmationState?.kind === "user"
      ? "Видалення акаунта"
      : confirmationState
        ? "Видалення абонемента"
        : "";

  const confirmationDescription =
    confirmationState?.kind === "user"
      ? `Щоб видалити акаунт ${confirmationState.user.first_name} ${confirmationState.user.last_name}, введіть email ${confirmationState.user.email}.`
      : confirmationState
        ? "Щоб видалити абонемент, введіть слово ВИДАЛИТИ. Це захист від випадкового кліку."
        : "";

  const confirmationActionLabel =
    confirmationState?.kind === "user" ? "Видалити акаунт" : "Видалити абонемент";

  const confirmationMatches =
    confirmationState !== null && confirmationInput.trim() === confirmationExpectedValue;

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
          <div className="table-toolbar">
            <div className="table-toolbar-fields">
              <label className="toolbar-field">
                <span className="toolbar-label">Фільтр списку</span>
                <span className="toolbar-select-shell">
                  <select
                    className="toolbar-control"
                    aria-label="Фільтр списку"
                    value={filterRole}
                    onChange={(event) => setFilterRole(event.target.value as UserRole | "ALL")}
                  >
                    <option value="ALL">Усі учасники</option>
                    {roles.map((role) => (
                      <option key={role} value={role}>
                        {getAccessLabel(role)}
                      </option>
                    ))}
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
                    value={userSearchTerm}
                    onChange={(event) => setUserSearchTerm(event.target.value)}
                    placeholder="Ім'я, прізвище або телефон"
                  />
                </span>
              </label>
            </div>
            <span className="toolbar-count">{filteredUsers.length} записів</span>
          </div>
        </div>

        {usersQuery.isLoading ? <p className="muted">Завантаження користувачів...</p> : null}
        {usersQuery.isError ? <p className="error-banner">{usersQuery.error instanceof Error ? usersQuery.error.message : "Помилка"}</p> : null}

        <div className="management-table">
          <div className="management-table-head users-table-layout">
            <span>Учасник</span>
            <span>Контакти</span>
            <span>Абонемент</span>
            <span>Доступ</span>
            <span>Статус</span>
            <span>Створено</span>
            <span>Дії</span>
          </div>
          {filteredUsers.map((user) => {
            const userSubscription = subscriptionsByUser.get(user.id);

            return (
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
                  {userSubscription ? (
                    <>
                      <strong>{userSubscription.plan?.title ?? getSubscriptionStatusLabel(userSubscription.status)}</strong>
                      <span className="muted">
                        {userSubscription.deleted_at
                          ? "Видалений"
                          : getSubscriptionStatusLabel(userSubscription.status)}
                      </span>
                    </>
                  ) : (
                    <span className="muted">Немає абонемента</span>
                  )}
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
            );
          })}
        </div>
      </div>

      {selectedUser ? (
        <div className="modal-overlay" onClick={() => setSelectedUser(null)}>
          <div
            className="modal-panel participant-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="participant-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="participant-modal-toolbar">
              <div>
                <p className="eyebrow">Учасник</p>
                <h3 id="participant-modal-title">
                  {selectedUser.first_name} {selectedUser.last_name}
                </h3>
              </div>
              <button className="ghost-link" onClick={() => setSelectedUser(null)}>Закрити</button>
            </div>

            <div className="detail-layout detail-layout-modal">
              <div className="surface-card detail-panel participant-sidebar">
            <div className="heading-row">
              <div>
                <h3>Профіль учасника</h3>
                <p className="muted">Повна інформація по {selectedUser.first_name} {selectedUser.last_name}.</p>
              </div>
            </div>

            <div className="summary-grid">
              <div className="summary-item"><span className="stat-label">Ім'я</span><strong>{selectedUser.first_name} {selectedUser.last_name}</strong></div>
              <div className="summary-item"><span className="stat-label">Email</span><strong>{selectedUser.email}</strong></div>
              <div className="summary-item"><span className="stat-label">Телефон</span><strong>{selectedUser.phone || "Не вказано"}</strong></div>
              <div className="summary-item"><span className="stat-label">Доступ</span><strong>{getAccessLabel(selectedUser.role)}</strong></div>
              <div className="summary-item"><span className="stat-label">Статус</span><strong>{selectedUser.is_verified ? "Підтверджено" : "Не підтверджено"}</strong></div>
              <div className="summary-item"><span className="stat-label">Створено</span><strong>{new Date(selectedUser.created_at).toLocaleString("uk-UA")}</strong></div>
            </div>

            <div className="form-grid participant-form-grid">
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
              <button
                className="danger-link"
                type="button"
                disabled={selectedUser.id === authUser?.id || deleteUserMutation.isPending}
                onClick={() => openUserDeleteConfirmation(selectedUser)}
              >
                {selectedUser.id === authUser?.id
                  ? "Не можна видалити свій акаунт"
                  : deleteUserMutation.isPending
                    ? "Видалення..."
                    : "Видалити акаунт"}
              </button>
            </div>
              </div>

              <div className="surface-card detail-panel participant-main">
            <div className="heading-row">
              <div>
                <h3>Керування абонементами</h3>
                <p className="muted">Видача, редагування, видалення й відновлення абонементів цього учасника.</p>
              </div>
            </div>

            <div className="form-grid participant-form-grid">
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

              <div className="table-scroll-shell">
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
                          <button
                            className="danger-link"
                            onClick={() => openSubscriptionDeleteConfirmation(subscription)}
                            disabled={deleteSubscriptionMutation.isPending}
                          >
                            Видалити абонемент
                          </button>
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
            </div>

            {editingSubscriptionId ? (
              <div className="form-grid participant-form-grid">
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

              <div className="table-scroll-shell">
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
            </div>
          </div>
        </div>
      ) : null}

      {confirmationState ? (
        <div className="modal-overlay" onClick={closeConfirmationModal}>
          <div
            className="modal-panel confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirmation-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="participant-modal-toolbar">
              <div>
                <p className="eyebrow">Підтвердження</p>
                <h3 id="confirmation-modal-title">{confirmationTitle}</h3>
              </div>
              <button className="ghost-link" type="button" onClick={closeConfirmationModal}>
                Закрити
              </button>
            </div>

            <p className="muted">{confirmationDescription}</p>

            <label>
              {confirmationState.kind === "user" ? "Email для підтвердження" : "Підтвердження"}
              <input
                value={confirmationInput}
                onChange={(event) => setConfirmationInput(event.target.value)}
                placeholder={confirmationExpectedValue}
              />
            </label>

            <div className="confirm-modal-actions">
              <button className="ghost-link" type="button" onClick={closeConfirmationModal}>
                Скасувати
              </button>
              <button
                className="danger-link"
                type="button"
                disabled={
                  !confirmationMatches ||
                  deleteSubscriptionMutation.isPending ||
                  deleteUserMutation.isPending
                }
                onClick={() => {
                  if (confirmationState.kind === "user") {
                    deleteUserMutation.mutate(confirmationState.user.id);
                    return;
                  }
                  deleteSubscriptionMutation.mutate(confirmationState.subscription.id);
                }}
              >
                {deleteUserMutation.isPending || deleteSubscriptionMutation.isPending
                  ? "Виконуємо..."
                  : confirmationActionLabel}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
