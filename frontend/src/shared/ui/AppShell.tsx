import type { PropsWithChildren } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore, userHasRole } from "../../features/auth";
import { navigationItems } from "../../features/navigation/config";
import { logout } from "../api";

export function AppShell({ children }: PropsWithChildren) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  const visibleItems = navigationItems.filter((item) => userHasRole(user, item.roles));
  const currentItem = visibleItems.find((item) => item.to === location.pathname);
  const formattedDate = new Intl.DateTimeFormat("uk-UA", {
    day: "numeric",
    month: "long"
  }).format(new Date());

  async function handleLogout() {
    await logout().catch(() => undefined);
    clearAuth();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-badge">ML</div>
          <div>
            <div className="brand-title">MotionLab</div>
            <div className="brand-subtitle">клубний кабінет</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="profile-card">
            <div className="profile-avatar">
              {user?.first_name?.[0]}
              {user?.last_name?.[0]}
            </div>
            <div>
              <div className="profile-name">
                {user?.first_name} {user?.last_name}
              </div>
              <div className="profile-email">{user?.email}</div>
            </div>
          </div>
          <button className="secondary-button wide-button" onClick={handleLogout}>
            Вийти
          </button>
        </div>
      </aside>

      <div className="shell-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Клубний простір</p>
            <h1>{currentItem?.label ?? "Клубний кабінет"}</h1>
          </div>
          <div className="topbar-actions">
            <Link className="ghost-link topbar-home-link" to="/">
              Сайт клубу
            </Link>
            <div className="topbar-badge">{formattedDate}</div>
          </div>
        </header>
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
