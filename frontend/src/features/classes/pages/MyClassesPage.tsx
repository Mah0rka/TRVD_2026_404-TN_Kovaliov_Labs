// Коротко: сторінка відображає інтерфейс для модуля занять тренера.

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getMyClasses, getScheduleAttendees } from "../../../shared/api";

export function MyClassesPage() {
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);

  const classesQuery = useQuery({
    queryKey: ["my-classes"],
    queryFn: getMyClasses
  });

  const attendeesQuery = useQuery({
    queryKey: ["class-attendees", selectedClassId],
    queryFn: () => getScheduleAttendees(selectedClassId as string),
    enabled: Boolean(selectedClassId)
  });

  const selectedClass = useMemo(
    () => classesQuery.data?.find((item) => item.id === selectedClassId),
    [classesQuery.data, selectedClassId]
  );

  return (
    <section className="panel-stack">
      <div className="panel-heading">
        <p className="eyebrow">Coach</p>
        <h2>Мої заняття та учасники</h2>
        <p className="muted">Тут зібрані класи на тиждень і список учасників для кожного заняття.</p>
      </div>

      <div className="dual-grid">
        <div className="surface-card">
          <h3>Мій графік</h3>
          {classesQuery.isLoading ? <p className="muted">Завантаження занять...</p> : null}
          {classesQuery.data?.length ? (
            <div className="table-grid">
              {classesQuery.data.map((item) => (
                <button
                  key={item.id}
                  className={selectedClassId === item.id ? "class-card active" : "class-card"}
                  onClick={() => setSelectedClassId(item.id)}
                >
                  <strong>{item.title}</strong>
                  <span>{new Date(item.start_time).toLocaleString("uk-UA")}</span>
                  <span>
                    {item.bookings.filter((booking) => booking.status === "CONFIRMED").length}/{item.capacity}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="muted">У тренера ще немає призначених занять.</p>
          )}
        </div>

        <div className="surface-card">
          <h3>Учасники заняття</h3>
          {selectedClass ? (
            <p className="muted">
              {selectedClass.title} · {new Date(selectedClass.start_time).toLocaleString("uk-UA")}
            </p>
          ) : (
            <p className="muted">Оберіть заняття зліва, щоб побачити список клієнтів.</p>
          )}

          {attendeesQuery.isLoading ? <p className="muted">Завантаження учасників...</p> : null}
          {attendeesQuery.isError ? (
            <p className="error-banner">
              {attendeesQuery.error instanceof Error ? attendeesQuery.error.message : "Помилка"}
            </p>
          ) : null}

          <div className="table-grid">
            {attendeesQuery.data?.map((attendee) => (
              <article key={attendee.id} className="table-row">
                <div>
                  <strong>
                    {attendee.user.first_name} {attendee.user.last_name}
                  </strong>
                  <p className="muted">{attendee.user.email}</p>
                </div>
                <span className="status-pill success">Підтверджено</span>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
