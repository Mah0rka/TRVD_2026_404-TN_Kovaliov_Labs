// DashboardShell відповідає лише за chrome/dashboard-обгортку:
// sidebar, topbar, mobile drawer і місце для дочірніх сторінок.
// Бізнес-логіка конкретних екранів сюди не потрапляє.

import { useEffect, useState, type PropsWithChildren } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";

import { logout } from "../../../shared/api";
import { BrandSignature } from "../../../shared/ui/BrandSignature";
import { useAuthStore, userHasRole } from "../../auth";
import { navigationItems } from "../config";

// Спільна оболонка дає єдину навігацію для всіх protected-сторінок
// і тримає mobile/desktop поведінку в одному місці.
export function DashboardShell({ children }: PropsWithChildren) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  // Schedule-екран має щільніший workspace, тому для нього вмикаємо ширшу колонку контенту.
  const isWideWorkspace = location.pathname === "/dashboard/schedule";

  // Пункти навігації фільтруються один раз на рівні shell, щоб сторінки не дублювали
  // рольову логіку лише заради того, щоб приховати лінк у sidebar.
  const visibleItems = navigationItems.filter((item) => userHasRole(user, item.roles));
  const formattedDate = new Intl.DateTimeFormat("uk-UA", {
    day: "numeric",
    month: "long"
  }).format(new Date());

  useEffect(() => {
    // Після будь-якої навігації мобільне меню має закриватися, щоб новий екран
    // не лишався прихованим під drawer-ом.
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!isMobileMenuOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    // Drawer поводиться як modal overlay: блокуємо прокрутку body і даємо Escape
    // як стандартний спосіб закриття.
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsMobileMenuOpen(false);
      }
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMobileMenuOpen]);

  async function handleLogout() {
    // Навіть якщо /logout не відповість, локальний auth-state все одно очищаємо,
    // щоб користувач не застряг у shell після втрати сесії.
    await logout().catch(() => undefined);
    clearAuth();
    navigate("/login", { replace: true });
  }

  function renderNavigationContent(isMobile = false) {
    // Один renderer використовується і для desktop sidebar, і для mobile drawer.
    // Так список посилань, профіль і logout-панель не роз'їжджаються між двома копіями JSX.
    return (
      <>
        <div className={isMobile ? "brand-lockup sidebar-mobile-brand" : "brand-lockup"}>
          <BrandSignature subtitle="клубний кабінет" />
          {isMobile ? (
            <button
              className="ghost-link mobile-close-button"
              type="button"
              aria-label="Закрити меню"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              ✕
            </button>
          ) : null}
        </div>

        <nav className="sidebar-nav">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
              onClick={() => {
                if (isMobile) {
                  setIsMobileMenuOpen(false);
                }
              }}
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
      </>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar sidebar-desktop">{renderNavigationContent()}</aside>

      {isMobileMenuOpen ? (
        <div
          className="sidebar-overlay"
          role="presentation"
          onClick={() => setIsMobileMenuOpen(false)}
        >
          <aside
            className="sidebar sidebar-mobile-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Навігація кабінету"
            onClick={(event) => event.stopPropagation()}
          >
            {renderNavigationContent(true)}
          </aside>
        </div>
      ) : null}

      <div className="shell-main">
        <header className="topbar">
          <div className="topbar-title-group">
            <button
              className="ghost-link mobile-menu-button"
              type="button"
              aria-label="Відкрити меню"
              aria-expanded={isMobileMenuOpen}
              onClick={() => setIsMobileMenuOpen(true)}
            >
              ☰
            </button>
          </div>
          <div className="topbar-actions">
            <Link className="ghost-link topbar-home-link" to="/">
              Сайт клубу
            </Link>
            <div className="topbar-badge">{formattedDate}</div>
          </div>
        </header>
        <main className={isWideWorkspace ? "content-area content-area-wide" : "content-area"}>
          {children}
        </main>
      </div>
    </div>
  );
}
