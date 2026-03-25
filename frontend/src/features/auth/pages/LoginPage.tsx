// Коротко: сторінка відображає інтерфейс для модуля входу користувача.

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  loginSchema,
  registerSchema,
  type LoginFormValues,
  type RegisterFormValues,
  useAuthStore
} from "..";
import { login, register } from "../../../shared/api";
import { getFieldErrors } from "../../../shared/lib/forms";

export function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginValues, setLoginValues] = useState<LoginFormValues>({
    email: "",
    password: ""
  });
  const [registerValues, setRegisterValues] = useState<RegisterFormValues>({
    first_name: "",
    last_name: "",
    email: "",
    password: ""
  });
  const [loginErrors, setLoginErrors] = useState<Record<string, string>>({});
  const [registerErrors, setRegisterErrors] = useState<Record<string, string>>({});
  const navigate = useNavigate();
  const setUser = useAuthStore((state) => state.setUser);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const parsed = loginSchema.safeParse(loginValues);

    if (!parsed.success) {
      setLoginErrors(getFieldErrors(parsed.error));
      return;
    }

    setLoginErrors({});
    setIsSubmitting(true);

    try {
      const user = await login(parsed.data.email, parsed.data.password);
      setUser(user);
      navigate("/dashboard");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Помилка авторизації");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const parsed = registerSchema.safeParse(registerValues);

    if (!parsed.success) {
      setRegisterErrors(getFieldErrors(parsed.error));
      return;
    }

    setRegisterErrors({});
    setIsSubmitting(true);

    try {
      const user = await register(parsed.data);
      setUser(user);
      navigate("/dashboard");
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Помилка реєстрації");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="screen">
      <section className="card auth-card">
        <div className="heading-group">
          <p className="eyebrow">Club login</p>
          <h1>Вхід до кабінету</h1>
          <p className="muted">Записи, абонементи, оплати й ваш ритм тренувань в одному місці.</p>
        </div>

        <Link className="ghost-link" to="/">
          На публічну сторінку
        </Link>

        <div className="tabs">
          <button className={mode === "login" ? "tab active" : "tab"} onClick={() => setMode("login")}>
            Вхід
          </button>
          <button className={mode === "register" ? "tab active" : "tab"} onClick={() => setMode("register")}>
            Реєстрація
          </button>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}

        {mode === "login" ? (
          <form className="form" onSubmit={handleLogin}>
            <label>
              Email
              <input
                type="email"
                value={loginValues.email}
                onChange={(event) =>
                  setLoginValues((current) => ({ ...current, email: event.target.value }))
                }
              />
              <span>{loginErrors.email}</span>
            </label>
            <label>
              Пароль
              <input
                type="password"
                value={loginValues.password}
                onChange={(event) =>
                  setLoginValues((current) => ({ ...current, password: event.target.value }))
                }
              />
              <span>{loginErrors.password}</span>
            </label>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Входимо..." : "Увійти"}
            </button>
          </form>
        ) : (
          <form className="form" onSubmit={handleRegister}>
            <label>
              Ім'я
              <input
                type="text"
                value={registerValues.first_name}
                onChange={(event) =>
                  setRegisterValues((current) => ({ ...current, first_name: event.target.value }))
                }
              />
              <span>{registerErrors.first_name}</span>
            </label>
            <label>
              Прізвище
              <input
                type="text"
                value={registerValues.last_name}
                onChange={(event) =>
                  setRegisterValues((current) => ({ ...current, last_name: event.target.value }))
                }
              />
              <span>{registerErrors.last_name}</span>
            </label>
            <label>
              Email
              <input
                type="email"
                value={registerValues.email}
                onChange={(event) =>
                  setRegisterValues((current) => ({ ...current, email: event.target.value }))
                }
              />
              <span>{registerErrors.email}</span>
            </label>
            <label>
              Пароль
              <input
                type="password"
                value={registerValues.password}
                onChange={(event) =>
                  setRegisterValues((current) => ({ ...current, password: event.target.value }))
                }
              />
              <span>{registerErrors.password}</span>
            </label>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Створюємо..." : "Створити акаунт"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
