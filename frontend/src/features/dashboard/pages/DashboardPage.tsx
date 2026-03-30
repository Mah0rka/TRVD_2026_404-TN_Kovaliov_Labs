import { Link } from "react-router-dom";

import { useAuthStore } from "../../auth";
import { useDashboardData } from "../hooks/useDashboardData";

// DashboardPage лишається thin renderer: він не знає, які query потрібні ролі,
// а лише рендерить уже зібрану view-model.
export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const { viewModel } = useDashboardData(user);

  return (
    <section className="panel-stack dashboard-page">
      {/* Hero і focus-card завжди будуються з однієї view-model, щоб тексти,
          CTA і метадані не розходились між ролями. */}
      <section className="dashboard-hero-panel">
        <article className="surface-card dashboard-hero-card">
          <p className="eyebrow">Добірка дня</p>
          <h2>{viewModel.heroTitle}</h2>
          <p className="muted">{viewModel.heroText}</p>

          <div className="dashboard-hero-actions">
            <Link className="secondary-button" to={viewModel.heroPrimary.to}>
              {viewModel.heroPrimary.label}
            </Link>
            <Link className="ghost-link" to={viewModel.heroSecondary.to}>
              {viewModel.heroSecondary.label}
            </Link>
          </div>
        </article>

        <article className="surface-card dashboard-focus-card">
          <p className="service-meta">{viewModel.focusLabel}</p>
          <h3>{viewModel.focusTitle}</h3>
          <p>{viewModel.focusText}</p>

          <div className="dashboard-focus-meta">
            {viewModel.focusMeta.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </article>
      </section>

      <div className="stats-grid dashboard-stats">
        {viewModel.stats.map((item, index) => {
          const value = String(item.value);

          return (
            <article
              key={item.label}
              className={
                index === 0
                  ? "stat-card dashboard-stat-card primary"
                  : "stat-card dashboard-stat-card"
              }
            >
              <span className="stat-label">{item.label}</span>
              {/* Довгі числа/рядки мають окремий клас, щоб картки не "ламалися"
                  при великій сумі виручки або довшому текстовому значенні. */}
              <strong className={value.length > 16 ? "stat-value small" : "stat-value"}>
                {value}
              </strong>
              <span className="dashboard-stat-note">{item.note}</span>
            </article>
          );
        })}
      </div>

      <div className="feature-grid dashboard-links">
        {viewModel.dashboardLinks.map((item) => (
          <Link
            key={item.to}
            className={`feature-card interactive-card dashboard-link-card ${item.tone}`}
            to={item.to}
          >
            <div className="dashboard-link-top">
              <p className="dashboard-link-eyebrow">{item.label}</p>
              <span className="dashboard-link-badge">{item.badge}</span>
            </div>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
