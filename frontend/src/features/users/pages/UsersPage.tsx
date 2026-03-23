import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createUser, getUsers, updateUser, type CurrentUser, type UserRole } from "../../../shared/api";

const roles: UserRole[] = ["CLIENT", "TRAINER", "ADMIN", "OWNER"];

function getAccessLabel(role: UserRole): string {
  if (role === "CLIENT") {
    return "Клієнт";
  }

  if (role === "TRAINER") {
    return "Тренер";
  }

  if (role === "ADMIN") {
    return "Адміністратор";
  }

  return "Власник";
}

export function UsersPage() {
  const [filterRole, setFilterRole] = useState<UserRole | "ALL">("ALL");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<CurrentUser | null>(null);
  const [createForm, setCreateForm] = useState({
    email: "",
    password: "Password123!",
    first_name: "",
    last_name: "",
    phone: "",
    role: "CLIENT" as UserRole,
    is_verified: true
  });
  const [editForm, setEditForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    role: "CLIENT" as UserRole,
    is_verified: true
  });
  const queryClient = useQueryClient();

  const usersQuery = useQuery({
    queryKey: ["users", filterRole],
    queryFn: () => getUsers(filterRole === "ALL" ? undefined : filterRole)
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setCreateForm({
        email: "",
        password: "Password123!",
        first_name: "",
        last_name: "",
        phone: "",
        role: "CLIENT",
        is_verified: true
      });
      setIsCreateOpen(false);
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, payload }: { userId: string; payload: Parameters<typeof updateUser>[1] }) =>
      updateUser(userId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setEditingUser(null);
    }
  });

  const roleStats = useMemo(() => {
    const users = usersQuery.data ?? [];
    return roles.map((role) => ({
      role,
      count: users.filter((user) => user.role === role).length
    }));
  }, [usersQuery.data]);

  function startEditing(user: CurrentUser) {
    setEditingUser(user);
    setEditForm({
      first_name: user.first_name,
      last_name: user.last_name,
      phone: user.phone ?? "",
      role: user.role,
      is_verified: user.is_verified
    });
  }

  return (
    <section className="panel-stack">
      <div className="panel-heading">
        <p className="eyebrow">Users</p>
        <h2>Учасники клубу</h2>
        <p className="muted">Керування акаунтами, контактами та рівнем доступу в клубі.</p>
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
            <p className="muted">
              Новий акаунт створюється тільки коли тобі це справді потрібно.
            </p>
          </div>
          <button
            className="ghost-link"
            type="button"
            aria-expanded={isCreateOpen}
            aria-controls="create-user-panel"
            onClick={() => setIsCreateOpen((current) => !current)}
          >
            {isCreateOpen ? "Сховати форму" : "Відкрити форму"}
          </button>
        </div>

        {isCreateOpen ? (
          <div id="create-user-panel" className="form-grid">
            <label>
              Email
              <input
                value={createForm.email}
                onChange={(event) => setCreateForm((current) => ({ ...current, email: event.target.value }))}
              />
            </label>
            <label>
              Пароль
              <input
                value={createForm.password}
                onChange={(event) => setCreateForm((current) => ({ ...current, password: event.target.value }))}
              />
            </label>
            <label>
              Ім'я
              <input
                value={createForm.first_name}
                onChange={(event) =>
                  setCreateForm((current) => ({ ...current, first_name: event.target.value }))
                }
              />
            </label>
            <label>
              Прізвище
              <input
                value={createForm.last_name}
                onChange={(event) =>
                  setCreateForm((current) => ({ ...current, last_name: event.target.value }))
                }
              />
            </label>
            <label>
              Телефон
              <input
                value={createForm.phone}
                onChange={(event) => setCreateForm((current) => ({ ...current, phone: event.target.value }))}
              />
            </label>
            <label>
              Доступ
              <select
                value={createForm.role}
                onChange={(event) =>
                  setCreateForm((current) => ({ ...current, role: event.target.value as UserRole }))
                }
              >
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

      {editingUser ? (
        <div className="surface-card form-grid">
          <div className="heading-row">
            <h3>Редагування користувача</h3>
            <button className="ghost-link" onClick={() => setEditingUser(null)}>
              Закрити
            </button>
          </div>
          <label>
            Ім'я
            <input
              value={editForm.first_name}
              onChange={(event) => setEditForm((current) => ({ ...current, first_name: event.target.value }))}
            />
          </label>
          <label>
            Прізвище
            <input
              value={editForm.last_name}
              onChange={(event) => setEditForm((current) => ({ ...current, last_name: event.target.value }))}
            />
          </label>
          <label>
            Телефон
            <input
              value={editForm.phone}
              onChange={(event) => setEditForm((current) => ({ ...current, phone: event.target.value }))}
            />
          </label>
          <label>
            Доступ
            <select
              value={editForm.role}
              onChange={(event) => setEditForm((current) => ({ ...current, role: event.target.value as UserRole }))}
            >
              {roles.map((role) => (
                <option key={role} value={role}>
                  {getAccessLabel(role)}
                </option>
              ))}
            </select>
          </label>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={editForm.is_verified}
              onChange={(event) =>
                setEditForm((current) => ({ ...current, is_verified: event.target.checked }))
              }
            />
            Підтверджений користувач
          </label>
          <button
            className="secondary-button"
            type="button"
            disabled={updateMutation.isPending}
            onClick={() =>
              updateMutation.mutate({
                userId: editingUser.id,
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
      ) : null}

      <div className="surface-card table-card">
        <div className="table-header">
          <h3>Список користувачів</h3>
          <div className="heading-row">
            <label>
              Фільтр списку
              <select
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
            </label>
            <span className="muted">{usersQuery.data?.length ?? 0} записів</span>
          </div>
        </div>

        {usersQuery.isLoading ? <p className="muted">Завантаження користувачів...</p> : null}
        {usersQuery.isError ? (
          <p className="error-banner">
            {usersQuery.error instanceof Error ? usersQuery.error.message : "Помилка"}
          </p>
        ) : null}

        <div className="table-grid">
          {usersQuery.data?.map((user) => (
            <article key={user.id} className="table-row">
              <div>
                <strong>
                  {user.first_name} {user.last_name}
                </strong>
                <p className="muted">{user.email}</p>
              </div>
              <div>
                <strong>{getAccessLabel(user.role)}</strong>
                <p className="muted">{user.phone || "—"}</p>
              </div>
              <div>
                <span className={user.is_verified ? "status-pill success" : "status-pill warning"}>
                  {user.is_verified ? "Підтверджено" : "Очікує"}
                </span>
              </div>
              <button className="ghost-link" onClick={() => startEditing(user)}>
                Редагувати
              </button>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
