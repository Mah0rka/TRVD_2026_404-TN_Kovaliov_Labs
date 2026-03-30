// SchedulePage є лише role-switch, а не окремим важким екраном.
// Увесь справжній UI винесений у дві незалежні реалізації:
// клієнтську карткову і staff-календарну.

import { lazy, Suspense } from "react";

import { useAuthStore } from "../../auth";
import { ClientScheduleView } from "../views/ClientScheduleView";

// Staff-режим підвантажує FullCalendar лише за потреби, щоб клієнтський список не тягнув важкий chunk.
const StaffScheduleView = lazy(async () => {
  const module = await import("../views/StaffScheduleView");
  return { default: module.StaffScheduleView };
});

function StaffScheduleFallback() {
  return (
    <main className="screen">
      <section className="card schedule-card schedule-calendar-card">
        <div className="heading-group">
          <h1>Календар занять</h1>
          <p className="muted">Підготовка календаря...</p>
        </div>
      </section>
    </main>
  );
}

// Такий split дозволяє не змішувати два дуже різні UX-сценарії в одному файлі
// і не тягнути FullCalendar у клієнтський шлях без потреби.
export function SchedulePage() {
  const user = useAuthStore((state) => state.user);

  if (user?.role === "CLIENT") {
    return <ClientScheduleView />;
  }

  return (
    // Suspense потрібен лише staff-гілці, бо саме вона завантажується lazy.
    <Suspense fallback={<StaffScheduleFallback />}>
      <StaffScheduleView />
    </Suspense>
  );
}
