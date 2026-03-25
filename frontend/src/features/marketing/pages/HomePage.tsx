// Коротко: сторінка відображає інтерфейс для модуля головної сторінки.

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { useAuthStore } from "../../auth";
import { getClubStats, getPublicMembershipPlans } from "../../../shared/api";

const zones = [
  {
    title: "Open gym",
    note: "силова зона · кардіо",
    image:
      "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1400&q=80"
  },
  {
    title: "Studio",
    note: "HIIT · cycle · mobility",
    image:
      "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?auto=format&fit=crop&w=1400&q=80"
  },
  {
    title: "Recovery",
    note: "stretch · reset",
    image:
      "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1400&q=80"
  }
];

const classes = [
  {
    title: "Strength",
    meta: "вільні ваги",
    note: "база, сила, техніка"
  },
  {
    title: "HIIT",
    meta: "високий темп",
    note: "коротко, інтенсивно, енергійно"
  },
  {
    title: "Mobility",
    meta: "відновлення",
    note: "гнучкість і легкість руху"
  },
  {
    title: "Personal",
    meta: "1:1 формат",
    note: "індивідуальний супровід"
  }
];

const trainers = [
  {
    name: "Марія Коваленко",
    role: "Strength coach",
    focus: "Базові рухи та безпечний прогрес",
    image:
      "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?auto=format&fit=crop&w=900&q=80"
  },
  {
    name: "Данило Мельник",
    role: "HIIT coach",
    focus: "Витривалість, ритм, функціональний рух",
    image:
      "https://images.unsplash.com/photo-1594737625785-a6cbdabd333c?auto=format&fit=crop&w=900&q=80"
  },
  {
    name: "Софія Гнатюк",
    role: "Mobility coach",
    focus: "Гнучкість, відновлення, контроль тіла",
    image:
      "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80"
  }
];

const reviews = [
  {
    quote: "Сильний зал, чисто, зручно записуватись. Реально хочеться тримати режим.",
    author: "Ірина"
  },
  {
    quote: "Тренери не для галочки. Є увага до техніки і нормальна енергія клубу.",
    author: "Андрій"
  },
  {
    quote: "Після роботи можна просто відкрити кабінет, записатись і прийти без хаосу.",
    author: "Олена"
  }
];

const convenience = [
  "центр міста",
  "ранкові й вечірні слоти",
  "онлайн-запис без дзвінків"
];

export function HomePage() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const statsQuery = useQuery({
    queryKey: ["club-stats"],
    queryFn: getClubStats
  });
  const publicPlansQuery = useQuery({
    queryKey: ["public-membership-plans"],
    queryFn: getPublicMembershipPlans
  });
  const primaryTarget = isAuthenticated ? "/dashboard" : "/login";
  const primaryLabel = isAuthenticated ? "Відкрити кабінет" : "Записатися на пробне";
  const secondaryLabel = isAuthenticated ? "Мій кабінет" : "Увійти";
  const greetingLabel = user?.first_name ? `Привіт, ${user.first_name}` : "Мій кабінет";
  const stats = statsQuery.data;
  const publicPlans = publicPlansQuery.data ?? [];
  const heroStats = [
    { value: stats ? String(stats.clients_count) : "—", label: "учасників клубу" },
    { value: stats ? String(stats.trainers_count) : "—", label: "тренерів у команді" },
    { value: stats ? String(stats.classes_next_7_days) : "—", label: "занять у найближчі 7 днів" },
    {
      value: stats ? String(stats.active_subscriptions_count) : "—",
      label: "активних абонементів"
    }
  ];

  useEffect(() => {
    if (!isMenuOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMenuOpen]);

  function closeMenu() {
    setIsMenuOpen(false);
  }

  return (
    <div className="marketing-page">
      <header className="marketing-header">
        <div className="brand-lockup">
          <div className="brand-badge">ML</div>
          <div>
            <div className="brand-title">MotionLab</div>
            <div className="brand-subtitle">fitness club</div>
          </div>
        </div>

        <nav className="marketing-nav" aria-label="Основна навігація">
          <a className="nav-pill" href="#classes" onClick={closeMenu}>
            Classes
          </a>
          <a className="nav-pill" href="#coaches" onClick={closeMenu}>
            Coaches
          </a>
          <a className="nav-pill" href="#membership" onClick={closeMenu}>
            Membership
          </a>
          <a className="nav-pill" href="#location" onClick={closeMenu}>
            Location
          </a>
        </nav>

        <div className="marketing-actions">
          {isAuthenticated ? (
            <Link className="session-pill session-pill-link" to={primaryTarget}>
              <span className="session-pill-dot" />
              <span>{greetingLabel}</span>
            </Link>
          ) : (
            <>
              <Link className="login-link" to={primaryTarget}>
                {secondaryLabel}
              </Link>
              <Link className="primary-cta button-link" to={primaryTarget}>
                {primaryLabel}
              </Link>
            </>
          )}
          <button
            className="ghost-link marketing-menu-button"
            type="button"
            aria-label="Відкрити меню"
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen(true)}
          >
            ☰
          </button>
        </div>
      </header>

      {isMenuOpen ? (
        <div className="marketing-drawer-overlay" role="presentation" onClick={closeMenu}>
          <div className="marketing-drawer" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="marketing-drawer-header">
              <div className="brand-lockup">
                <div className="brand-badge">ML</div>
                <div>
                  <div className="brand-title">MotionLab</div>
                  <div className="brand-subtitle">fitness club</div>
                </div>
              </div>
              <button className="ghost-link mobile-close-button" type="button" aria-label="Закрити меню" onClick={closeMenu}>
                ✕
              </button>
            </div>
            <nav className="marketing-drawer-nav" aria-label="Мобільна навігація">
              <a className="nav-pill" href="#classes" onClick={closeMenu}>
                Classes
              </a>
              <a className="nav-pill" href="#coaches" onClick={closeMenu}>
                Coaches
              </a>
              <a className="nav-pill" href="#membership" onClick={closeMenu}>
                Membership
              </a>
              <a className="nav-pill" href="#location" onClick={closeMenu}>
                Location
              </a>
            </nav>
            <div className="marketing-drawer-actions">
              {isAuthenticated ? (
                <Link className="session-pill session-pill-link" to={primaryTarget} onClick={closeMenu}>
                  <span className="session-pill-dot" />
                  <span>{greetingLabel}</span>
                </Link>
              ) : (
                <>
                  <Link className="login-link" to={primaryTarget} onClick={closeMenu}>
                    {secondaryLabel}
                  </Link>
                  <Link className="primary-cta button-link" to={primaryTarget} onClick={closeMenu}>
                    {primaryLabel}
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      ) : null}

      <section className="hero-section">
        <div className="hero-copy">
          <p className="hero-kicker">Fitness club</p>
          <h1 className="hero-title">Тренуйся там, куди хочеться повертатись.</h1>
          <p className="hero-summary">
            Силова зона, групові класи, персональні тренери та атмосфера, яка тримає
            в русі.
          </p>

          <div className="hero-proof">
            {heroStats.map((item) => (
              <div key={item.label} className="hero-proof-item">
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="hero-stage">
          <article className="hero-main-shot">
            <img
              src="https://images.unsplash.com/photo-1540497077202-7c8a3999166f?auto=format&fit=crop&w=1500&q=80"
              alt="Сучасний зал із кардіо та силовою зоною"
            />
            <div className="hero-badge">
              {stats ? `${stats.classes_next_7_days} занять у найближчі 7 днів` : "Живий розклад клубу"}
            </div>
          </article>

          <div className="hero-side-stack">
            <article className="hero-side-shot">
              <img
                src="https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=900&q=80"
                alt="Групове функціональне тренування"
                loading="lazy"
              />
            </article>
            <article className="hero-side-shot">
              <img
                src="https://images.unsplash.com/photo-1518310383802-640c2de311b2?auto=format&fit=crop&w=900&q=80"
                alt="Персональна робота з тренером"
                loading="lazy"
              />
            </article>
          </div>
        </div>

        <div className="hero-actions-row">
          <Link className="primary-cta button-link hero-primary" to={primaryTarget}>
            {primaryLabel}
          </Link>
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <p className="eyebrow">Why our gym</p>
          <h2>Атмосфера клубу, яку видно без довгих пояснень</h2>
        </div>

        <div className="zone-grid">
          {zones.map((zone) => (
            <article key={zone.title} className="zone-card">
              <img src={zone.image} alt={zone.title} loading="lazy" />
              <div className="zone-copy">
                <p className="service-meta">{zone.note}</p>
                <h3>{zone.title}</h3>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block" id="classes">
        <div className="section-heading">
          <p className="eyebrow">Classes</p>
          <h2>Обери свій формат руху</h2>
        </div>

        <div className="class-menu">
          {classes.map((item) => (
            <article key={item.title} className="class-tile">
              <p className="service-meta">{item.meta}</p>
              <h3>{item.title}</h3>
              <p>{item.note}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block" id="coaches">
        <div className="section-heading">
          <p className="eyebrow">Coaches</p>
          <h2>Реальні тренери. Реальна довіра.</h2>
        </div>

        <div className="trainer-grid">
          {trainers.map((trainer) => (
            <article key={trainer.name} className="trainer-card">
              <img
                src={trainer.image}
                alt={trainer.name}
                className="trainer-photo"
                loading="lazy"
              />
              <div className="trainer-copy">
                <p className="service-meta">{trainer.role}</p>
                <h3>{trainer.name}</h3>
                <p>{trainer.focus}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <p className="eyebrow">Reviews</p>
          <h2>Що кажуть ті, хто вже тримає темп з нами</h2>
        </div>

        <div className="review-strip">
          {reviews.map((review) => (
            <article key={review.author} className="review-card">
              <div className="review-stars">★★★★★</div>
              <p>{review.quote}</p>
              <strong>{review.author}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block" id="membership">
        <div className="section-heading">
          <p className="eyebrow">Membership</p>
          <h2>Абонементи без зайвої складності</h2>
        </div>

        <div className="pricing-showcase">
          {publicPlans.slice(0, 3).map((plan, index) => (
            <article
              key={plan.id}
              className={index === 1 ? "pricing-panel featured" : "pricing-panel"}
            >
              <p className="service-meta">
                {plan.visits_limit ? `${plan.visits_limit} занять` : "безліміт"} · {plan.duration_days} днів
              </p>
              <h3>{plan.title}</h3>
              <div className="price-line">
                <strong>
                  {plan.currency === "UAH" ? "₴" : `${plan.currency} `}
                  {plan.price}
                </strong>
                <span>/ план</span>
              </div>
              <ul className="plan-list">
                <li>{plan.description ?? "Абонемент клубу з реальної системи."}</li>
                <li>{plan.is_active ? "доступний до покупки" : "тимчасово недоступний"}</li>
              </ul>
              <Link className="primary-cta button-link" to={primaryTarget}>
                {primaryLabel}
              </Link>
            </article>
          ))}
          {!publicPlans.length ? (
            <article className="pricing-panel">
              <p className="service-meta">membership</p>
              <h3>Абонементи скоро з’являться</h3>
              <p>Менеджер клубу ще не відкрив публічні плани для сайту.</p>
            </article>
          ) : null}
        </div>
      </section>

      <section className="location-panel" id="location">
        <div className="location-copy">
          <p className="eyebrow">Location</p>
          <h2>Клуб, у який зручно заїхати до роботи або після неї</h2>
          <p className="location-text">
            Один зрозумілий крок: обираєш пробне, приходиш у клуб і відчуваєш ритм на
            власному тренуванні.
          </p>
          <div className="location-list">
            {convenience.map((item) => (
              <span key={item} className="location-item">
                {item}
              </span>
            ))}
          </div>
        </div>

        <div className="cta-cluster">
          <Link className="primary-cta button-link" to={primaryTarget}>
            {primaryLabel}
          </Link>
          <Link className="login-link light" to={primaryTarget}>
            {isAuthenticated ? "Повернутись у кабінет" : "Увійти в кабінет"}
          </Link>
        </div>
      </section>
    </div>
  );
}
