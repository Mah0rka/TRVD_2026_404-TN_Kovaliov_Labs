// Показує історію та статуси бронювань поточного користувача.

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { cancelBooking, getMyBookings, queryKeys } from "../../../shared/api";
import { hasSessionEnded } from "../../../shared/lib/sessionTime";

// Показує бронювання поточного користувача та їх статуси.
export function BookingsPage() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<"ACTIVE" | "HISTORY">("ACTIVE");

  const bookingsQuery = useQuery({
    queryKey: queryKeys.bookings.mine(),
    queryFn: getMyBookings
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBooking,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.bookings.mine() });
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.mine() });
    }
  });

  const visibleBookings = useMemo(() => {
    const bookings = bookingsQuery.data ?? [];

    if (view === "ACTIVE") {
      return bookings.filter(
        (booking) =>
          booking.status === "CONFIRMED" &&
          !hasSessionEnded(booking.workout_class.end_time)
      );
    }

    return bookings.filter(
      (booking) =>
        booking.status !== "CONFIRMED" ||
        hasSessionEnded(booking.workout_class.end_time)
    );
  }, [bookingsQuery.data, view]);

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <h1>Мої записи</h1>
          <p className="muted">
            {view === "ACTIVE"
              ? "Тут показані лише ваші актуальні записи на тренування."
              : "Тут зібрана історія скасованих і завершених записів."}
          </p>
        </div>

        <div className="chips">
          <button
            className={view === "ACTIVE" ? "chip active" : "chip"}
            onClick={() => setView("ACTIVE")}
          >
            Актуальні
          </button>
          <button
            className={view === "HISTORY" ? "chip active" : "chip"}
            onClick={() => setView("HISTORY")}
          >
            Історія
          </button>
        </div>

        {bookingsQuery.isLoading ? <p className="muted">Завантаження бронювань...</p> : null}
        {bookingsQuery.isError ? (
          <p className="error-banner">
            {bookingsQuery.error instanceof Error ? bookingsQuery.error.message : "Помилка"}
          </p>
        ) : null}

        <div className="schedule-grid">
          {visibleBookings.length ? (
            visibleBookings.map((booking) => (
              <article className="schedule-item" key={booking.id}>
                <p className="eyebrow">
                  {booking.status === "CONFIRMED"
                    ? "Підтверджено"
                    : booking.status === "CANCELLED"
                      ? "Скасовано"
                      : booking.status}
                </p>
                <h2>{booking.workout_class.title}</h2>
                <p className="muted">{new Date(booking.workout_class.start_time).toLocaleString("uk-UA")}</p>
                <p className="muted">
                  Тренер: {booking.workout_class.trainer.first_name} {booking.workout_class.trainer.last_name}
                </p>
                <p className="muted">
                  {booking.workout_class.is_paid_extra
                    ? `Додатково платне заняття · ${booking.workout_class.extra_price ?? 0} UAH`
                    : "Безкоштовне заняття в межах абонемента"}
                </p>
                {booking.status === "CONFIRMED" ? (
                  <>
                    <button
                      className="danger-link"
                      onClick={() => cancelMutation.mutate(booking.id)}
                      disabled={cancelMutation.isPending}
                    >
                      Скасувати
                    </button>
                    <p className="muted">
                      {booking.workout_class.is_paid_extra
                        ? "Скасування можливе не пізніше ніж за 2 години до початку."
                        : "Скасування можливе не пізніше ніж за 1 годину до початку."}
                    </p>
                  </>
                ) : null}
              </article>
            ))
          ) : (
            <article className="schedule-item empty-card">
              <h2>{view === "ACTIVE" ? "Поки що без активних записів" : "Історія ще порожня"}</h2>
              <p className="muted">
                {view === "ACTIVE"
                  ? "Оберіть заняття в розкладі, щоб створити перший запис."
                  : "Після скасування або завершення записів вони з’являться тут."}
              </p>
            </article>
          )}
        </div>
      </section>
    </main>
  );
}
