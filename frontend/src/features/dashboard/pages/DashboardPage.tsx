// Збирає основні показники й персональні дані на дашборді.

import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  getMyBookings,
  getMyClasses,
  getMyPayments,
  getRevenueReport,
  getSchedules,
  getSubscriptions
} from "../../../shared/api";
import { useAuthStore } from "../../auth";

// Форматує дату для відображення в дашборді.
function formatSessionDate(iso: string): string {
  return new Intl.DateTimeFormat("uk-UA", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(iso));
}

// Повертає коротку назву типу абонемента для UI.
function getSubscriptionLabel(type: "MONTHLY" | "YEARLY" | "PAY_AS_YOU_GO"): string {
  if (type === "MONTHLY") {
    return "місячний";
  }

  if (type === "YEARLY") {
    return "річний";
  }

  return "поразовий";
}

// Показує оглядові віджети, профіль і найближчі активності користувача.
export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const role = user?.role;
  const isClient = role === "CLIENT";
  const isTrainer = role === "TRAINER";
  const isManagement = role === "ADMIN" || role === "OWNER";

  const now = new Date();
  const weekAhead = new Date(now);
  weekAhead.setDate(weekAhead.getDate() + 7);

  const schedulesQuery = useQuery({
    queryKey: ["dashboard-schedules"],
    queryFn: getSchedules
  });

  const bookingsQuery = useQuery({
    queryKey: ["dashboard-bookings"],
    queryFn: getMyBookings,
    enabled: isClient
  });

  const subscriptionsQuery = useQuery({
    queryKey: ["dashboard-subscriptions"],
    queryFn: getSubscriptions,
    enabled: isClient
  });

  const paymentsQuery = useQuery({
    queryKey: ["dashboard-payments"],
    queryFn: getMyPayments,
    enabled: isClient
  });

  const myClassesQuery = useQuery({
    queryKey: ["dashboard-my-classes"],
    queryFn: getMyClasses,
    enabled: isTrainer
  });

  const revenueQuery = useQuery({
    queryKey: ["dashboard-revenue"],
    queryFn: () => getRevenueReport(),
    enabled: isManagement
  });

  const schedules = schedulesQuery.data ?? [];
  const upcomingSchedules = schedules
    .filter((item) => new Date(item.start_time) > now)
    .sort((left, right) => +new Date(left.start_time) - +new Date(right.start_time));

  const thisWeekSchedules = upcomingSchedules.filter(
    (item) => new Date(item.start_time) <= weekAhead
  );

  const confirmedBookings = (bookingsQuery.data ?? []).filter((booking) => booking.status === "CONFIRMED");
  const upcomingBookings = confirmedBookings
    .filter((booking) => new Date(booking.workout_class.start_time) > now)
    .sort(
      (left, right) =>
        +new Date(left.workout_class.start_time) - +new Date(right.workout_class.start_time)
    );

  const subscriptions = subscriptionsQuery.data ?? [];
  const activeSubscription = subscriptions.find((subscription) => subscription.status === "ACTIVE");

  const myClasses = myClassesQuery.data ?? [];
  const upcomingMyClasses = myClasses
    .filter((item) => new Date(item.start_time) > now)
    .sort((left, right) => +new Date(left.start_time) - +new Date(right.start_time));
  const trainerAttendance = myClasses.reduce(
    (total, item) => total + item.bookings.filter((booking) => booking.status === "CONFIRMED").length,
    0
  );

  const nextClientSession = upcomingBookings[0]?.workout_class;
  const nextTrainerSession = upcomingMyClasses[0];
  const nextClubSession = upcomingSchedules[0];

  const heroTitle = isClient
    ? "Твій ритм уже зібраний в одному місці"
    : isTrainer
      ? "Сьогоднішній графік і команда вже під рукою"
      : "Усе, що потрібно для живого ритму клубу";

  const heroText = isClient
    ? "Швидко перевіряй записи, тримай під контролем абонемент і не губи наступне тренування."
    : isTrainer
      ? "Дивись свої класи, учасників і найближчі слоти без переходів по зайвих екранах."
      : "Розклад, оплати, учасники й аналітика зібрані в одному спокійному робочому просторі.";

  const heroPrimary = isClient
    ? { to: "/dashboard/schedule", label: "Відкрити розклад" }
    : isTrainer
      ? { to: "/dashboard/my-classes", label: "Мої класи" }
      : { to: "/dashboard/reports", label: "Відкрити аналітику" };

  const heroSecondary = isClient
    ? { to: "/dashboard/bookings", label: "Мої записи" }
    : isTrainer
      ? { to: "/dashboard/schedule", label: "Увесь розклад" }
      : { to: "/dashboard/users", label: "Учасники клубу" };

  const focusLabel = isClient
    ? nextClientSession
      ? "Наступне тренування"
      : "Час обрати заняття"
    : isTrainer
      ? nextTrainerSession
        ? "Найближчий клас"
        : "Розклад на тиждень"
      : nextClubSession
        ? "Найближчий слот"
        : "Ритм клубу";

  const focusTitle = isClient
    ? nextClientSession
      ? nextClientSession.title
      : "У розкладі вже є нові слоти"
    : isTrainer
      ? nextTrainerSession
        ? nextTrainerSession.title
        : "Підготуй новий тиждень"
      : nextClubSession
        ? nextClubSession.title
        : "День можна починати зі спокою";

  const focusText = isClient
    ? nextClientSession
      ? `${formatSessionDate(nextClientSession.start_time)} з ${nextClientSession.trainer.first_name} ${nextClientSession.trainer.last_name}`
      : "Подивись доступні класи і забронюй наступне тренування без зайвих кроків."
    : isTrainer
      ? nextTrainerSession
        ? `${formatSessionDate(nextTrainerSession.start_time)} · ${nextTrainerSession.bookings.filter((booking) => booking.status === "CONFIRMED").length} учасників`
        : "Увесь графік уже в кабінеті: переглядай класи та працюй з учасниками в одному просторі."
      : nextClubSession
        ? `${formatSessionDate(nextClubSession.start_time)} · ${nextClubSession.bookings.filter((booking) => booking.status === "CONFIRMED").length}/${nextClubSession.capacity} записів`
        : "Сьогодні можна швидко перевірити розклад, оплати та команду без технічного шуму.";

  const focusMeta = isClient
    ? [
        activeSubscription
          ? `Абонемент: ${getSubscriptionLabel(activeSubscription.type)}`
          : "Абонемент ще не обрано",
        `${upcomingBookings.length} записів попереду`
      ]
    : isTrainer
      ? [`${upcomingMyClasses.length} класів попереду`, `${trainerAttendance} відвідувань у роботі`]
      : [
          `${thisWeekSchedules.length} занять цього тижня`,
          `₴${revenueQuery.data?.total_revenue.toLocaleString("uk-UA") ?? "0"} за 30 днів`
        ];

  const stats = isClient
    ? [
        {
          label: "Записів попереду",
          value: upcomingBookings.length,
          note: "усі найближчі тренування"
        },
        {
          label: "Класів цього тижня",
          value: thisWeekSchedules.length,
          note: "можна обрати у розкладі"
        },
        {
          label: "Активний план",
          value: activeSubscription ? getSubscriptionLabel(activeSubscription.type) : "ще не обрано",
          note: activeSubscription ? "готовий до використання" : "можна активувати сьогодні"
        },
        {
          label: "Історія оплат",
          value: paymentsQuery.data?.length ?? 0,
          note: "усі покупки в одному місці"
        }
      ]
    : isTrainer
      ? [
          {
            label: "Класів попереду",
            value: upcomingMyClasses.length,
            note: "найближчі слоти в роботі"
          },
          {
            label: "Учасників загалом",
            value: trainerAttendance,
            note: "підтверджені записи"
          },
          {
            label: "У розкладі цього тижня",
            value: thisWeekSchedules.length,
            note: "загальний темп клубу"
          },
          {
            label: "Найближчий старт",
            value: nextTrainerSession ? formatSessionDate(nextTrainerSession.start_time) : "ще немає",
            note: "час наступного класу"
          }
        ]
      : [
          {
            label: "Занять цього тижня",
            value: thisWeekSchedules.length,
            note: "усі відкриті слоти"
          },
          {
            label: "Попереду в розкладі",
            value: upcomingSchedules.length,
            note: "найближчі активності"
          },
          {
            label: "Дохід за 30 днів",
            value: `₴${revenueQuery.data?.total_revenue.toLocaleString("uk-UA") ?? "0"}`,
            note: "видно одразу з кабінету"
          },
          {
            label: "Транзакцій",
            value: revenueQuery.data?.transactions_count ?? 0,
            note: "за обраний період"
          }
        ];

  const dashboardLinks = isClient
    ? [
        {
          label: "Твій ритм",
          title: "Мої записи",
          description: "Перевіряй найближчі тренування та тримай усе в одному списку.",
          to: "/dashboard/bookings",
          badge: `${upcomingBookings.length} попереду`,
          tone: "accent"
        },
        {
          label: "Розклад клубу",
          title: "Розклад",
          description: "Нові слоти, тренери й час для наступного тренування.",
          to: "/dashboard/schedule",
          badge: `${thisWeekSchedules.length} цього тижня`,
          tone: "dark"
        },
        {
          label: "Твій план",
          title: "Абонементи",
          description: activeSubscription
            ? `Зараз активний ${getSubscriptionLabel(activeSubscription.type)} план.`
            : "Підбери план під свій темп без зайвих кроків.",
          to: "/dashboard/subscriptions",
          badge: activeSubscription ? "активний" : "обрати",
          tone: "light"
        },
        {
          label: "Покупки",
          title: "Історія оплат",
          description: "Усі покупки абонементів і останні оплати в одному місці.",
          to: "/dashboard/payments",
          badge: `${paymentsQuery.data?.length ?? 0} записів`,
          tone: "light"
        }
      ]
    : isTrainer
      ? [
        {
          label: "Тренерський день",
          title: "Мої класи",
          description: "Учасники, час і фокус на найближчі заняття без зайвої метушні.",
          to: "/dashboard/my-classes",
            badge: `${upcomingMyClasses.length} попереду`,
            tone: "accent"
          },
        {
          label: "Тижневий огляд",
          title: "Розклад",
          description: "Зручний огляд усіх занять, щоб тримати тиждень у полі зору.",
          to: "/dashboard/schedule",
            badge: `${thisWeekSchedules.length} цього тижня`,
            tone: "dark"
          },
        {
          label: "Особисті дані",
          title: "Профіль",
          description: "Контакти, базова інформація та персональний простір тренера.",
          to: "/dashboard/profile",
          badge: "оновити",
          tone: "light"
        }
      ]
    : [
        {
          label: "Ритм клубу",
          title: "Розклад",
          description: "Швидкий погляд на весь темп клубу, слоти й найближчі активності.",
          to: "/dashboard/schedule",
            badge: `${upcomingSchedules.length} попереду`,
            tone: "accent"
          },
        {
          label: "Команда і клієнти",
          title: "Учасники",
          description: "Команда, клієнти та базове керування профілями в одному місці.",
          to: "/dashboard/users",
          badge: "склад клубу",
          tone: "dark"
        },
        {
          label: "Показники",
          title: "Аналітика",
          description: "Виручка, популярність тренерів і жива картина руху клубу.",
          to: "/dashboard/reports",
          badge: "оновлюється",
          tone: "light"
        },
        {
          label: "Продажі",
          title: "Історія оплат",
          description: "Грошовий потік і транзакції під рукою без технічних панелей.",
          to: "/dashboard/payments",
            badge: `${revenueQuery.data?.transactions_count ?? 0} транзакцій`,
            tone: "light"
          }
        ];

  return (
    <section className="panel-stack dashboard-page">
      <section className="dashboard-hero-panel">
        <article className="surface-card dashboard-hero-card">
          <p className="eyebrow">Добірка дня</p>
          <h2>{heroTitle}</h2>
          <p className="muted">{heroText}</p>

          <div className="dashboard-hero-actions">
            <Link className="secondary-button" to={heroPrimary.to}>
              {heroPrimary.label}
            </Link>
            <Link className="ghost-link" to={heroSecondary.to}>
              {heroSecondary.label}
            </Link>
          </div>
        </article>

        <article className="surface-card dashboard-focus-card">
          <p className="service-meta">{focusLabel}</p>
          <h3>{focusTitle}</h3>
          <p>{focusText}</p>

          <div className="dashboard-focus-meta">
            {focusMeta.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </article>
      </section>

      <div className="stats-grid dashboard-stats">
        {stats.map((item, index) => {
          const value = String(item.value);

          return (
            <article
              key={item.label}
              className={index === 0 ? "stat-card dashboard-stat-card primary" : "stat-card dashboard-stat-card"}
            >
              <span className="stat-label">{item.label}</span>
              <strong className={value.length > 16 ? "stat-value small" : "stat-value"}>{value}</strong>
              <span className="dashboard-stat-note">{item.note}</span>
            </article>
          );
        })}
      </div>

      <div className="feature-grid dashboard-links">
        {dashboardLinks.map((item) => (
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
