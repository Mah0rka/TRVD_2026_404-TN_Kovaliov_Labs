// Коротко: сторінка відображає інтерфейс для модуля профілю користувача.

import { useEffect, useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";

import { useAuthStore } from "../../auth";
import { updateMyProfile } from "../../../shared/api";
import { getFieldErrors } from "../../../shared/lib/forms";

const profileSchema = z.object({
  first_name: z.string().min(2, "Мінімум 2 символи"),
  last_name: z.string().min(2, "Мінімум 2 символи"),
  phone: z.string()
});

type ProfileForm = z.infer<typeof profileSchema>;

export function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [formValues, setFormValues] = useState<ProfileForm>({
    first_name: user?.first_name ?? "",
    last_name: user?.last_name ?? "",
    phone: user?.phone ?? ""
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setFormValues({
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
      phone: user?.phone ?? ""
    });
  }, [user]);

  const mutation = useMutation({
    mutationFn: updateMyProfile,
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
    }
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const parsed = profileSchema.safeParse(formValues);
    if (!parsed.success) {
      setFieldErrors(getFieldErrors(parsed.error));
      return;
    }

    setFieldErrors({});
    mutation.mutate(parsed.data);
  }

  return (
    <section className="panel-stack">
      <div className="panel-heading">
        <p className="eyebrow">Profile</p>
        <h2>Мій профіль</h2>
        <p className="muted">Тут зібрані ваші контакти та особисті дані для клубного кабінету.</p>
      </div>

      <div className="stats-grid">
        <article className="stat-card accent">
          <span className="stat-label">Ім'я</span>
          <strong className="stat-value">
            {user?.first_name} {user?.last_name}
          </strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Email</span>
          <strong className="stat-value small">{user?.email}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Телефон</span>
          <strong className="stat-value small">{user?.phone || "ще не додано"}</strong>
        </article>
      </div>

      <form
        className="form-grid surface-card"
        onSubmit={handleSubmit}
      >
        <label>
          Ім'я
          <input
            type="text"
            value={formValues.first_name}
            onChange={(event) =>
              setFormValues((current) => ({ ...current, first_name: event.target.value }))
            }
          />
          <span>{fieldErrors.first_name}</span>
        </label>
        <label>
          Прізвище
          <input
            type="text"
            value={formValues.last_name}
            onChange={(event) =>
              setFormValues((current) => ({ ...current, last_name: event.target.value }))
            }
          />
          <span>{fieldErrors.last_name}</span>
        </label>
        <label>
          Телефон
          <input
            type="text"
            value={formValues.phone}
            onChange={(event) =>
              setFormValues((current) => ({ ...current, phone: event.target.value }))
            }
          />
          <span>{fieldErrors.phone}</span>
        </label>
        <button className="secondary-button" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Збереження..." : "Зберегти профіль"}
        </button>
        {mutation.isError ? (
          <p className="error-banner">{mutation.error instanceof Error ? mutation.error.message : "Помилка"}</p>
        ) : null}
      </form>
    </section>
  );
}
