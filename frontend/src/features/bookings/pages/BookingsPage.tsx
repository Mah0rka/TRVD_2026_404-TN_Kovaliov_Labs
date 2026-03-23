import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { cancelBooking, getMyBookings } from "../../../shared/api";

export function BookingsPage() {
  const queryClient = useQueryClient();

  const bookingsQuery = useQuery({
    queryKey: ["my-bookings"],
    queryFn: getMyBookings
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBooking,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
      queryClient.invalidateQueries({ queryKey: ["my-subscriptions"] });
    }
  });

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <p className="eyebrow">Bookings</p>
          <h1>Мої бронювання</h1>
          <p className="muted">Усі поточні й минулі записи клієнта на тренування.</p>
        </div>

        {bookingsQuery.isLoading ? <p className="muted">Завантаження бронювань...</p> : null}
        {bookingsQuery.isError ? (
          <p className="error-banner">
            {bookingsQuery.error instanceof Error ? bookingsQuery.error.message : "Помилка"}
          </p>
        ) : null}

        <div className="schedule-grid">
          {bookingsQuery.data?.length ? (
            bookingsQuery.data.map((booking) => (
              <article className="schedule-item" key={booking.id}>
                <p className="eyebrow">{booking.status}</p>
                <h2>{booking.workout_class.title}</h2>
                <p className="muted">{new Date(booking.workout_class.start_time).toLocaleString("uk-UA")}</p>
                <p className="muted">
                  Тренер: {booking.workout_class.trainer.first_name} {booking.workout_class.trainer.last_name}
                </p>
                {booking.status === "CONFIRMED" ? (
                  <button
                    className="danger-link"
                    onClick={() => cancelMutation.mutate(booking.id)}
                    disabled={cancelMutation.isPending}
                  >
                    Скасувати
                  </button>
                ) : null}
              </article>
            ))
          ) : (
            <article className="schedule-item empty-card">
              <h2>Поки що без бронювань</h2>
              <p className="muted">Оберіть заняття в розкладі, щоб створити перший запис.</p>
            </article>
          )}
        </div>
      </section>
    </main>
  );
}
