// Клієнтський екран розкладу навмисно не використовує календарний UI.
// Для клієнта важливіше швидко відфільтрувати доступні заняття, побачити
// стан запису та пройти booking/payment flow без перевантаження інтерфейсу.

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  confirmPaidBooking,
  createBooking,
  createPaidBookingCheckout,
  getMyPayments,
  getSchedules,
  queryKeys
} from "../../../shared/api";
import { hasSessionStarted } from "../../../shared/lib/sessionTime";
import { useAuthStore } from "../../auth";
import { classTypes, getScheduleStats, type ClassTypeFilter } from "../lib/scheduleShared";

export function ClientScheduleView() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const [filter, setFilter] = useState<ClassTypeFilter>("ALL");
  // Локальний кеш щойно створених доплат потрібен, щоб UI миттєво показав
  // "крок 2" навіть до завершення наступного refetch.
  const [pendingCheckout, setPendingCheckout] = useState<
    Record<string, { paymentId: string; amount: number }>
  >({});

  const schedulesQuery = useQuery({
    queryKey: queryKeys.schedules.clientList(),
    queryFn: () => getSchedules()
  });

  const myPaymentsQuery = useQuery({
    queryKey: queryKeys.payments.mine(),
    queryFn: getMyPayments
  });

  const bookMutation = useMutation({
    mutationFn: createBooking,
    onSuccess: () => {
      // Бронювання змінює доступність місць, список моїх записів і потенційно
      // використання абонемента, тому оновлюємо всі пов'язані surface-и.
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.bookings.mine() });
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.mine() });
    }
  });

  const paidCheckoutMutation = useMutation({
    mutationFn: createPaidBookingCheckout,
    onSuccess: (payment, classId) => {
      // Після створення pending payment одразу запам'ятовуємо його локально,
      // щоб користувач міг підтвердити оплату без повторного відкриття картки.
      setPendingCheckout((current) => ({
        ...current,
        [classId]: {
          paymentId: payment.id,
          amount: payment.amount
        }
      }));
      queryClient.invalidateQueries({ queryKey: queryKeys.payments.mine() });
    }
  });

  const confirmPaidMutation = useMutation({
    mutationFn: confirmPaidBooking,
    onSuccess: (booking) => {
      // Коли booking підтверджено, локальний pending стан більше не потрібен:
      // джерелом правди стають уже оновлені schedules/bookings/payments запити.
      setPendingCheckout((current) => {
        const next = { ...current };
        delete next[booking.class_id];
        return next;
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.bookings.mine() });
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions.mine() });
      queryClient.invalidateQueries({ queryKey: queryKeys.payments.mine() });
    }
  });

  const filteredSchedules = useMemo(
    () =>
      // На клієнтському екрані показуємо лише майбутні сесії, на які ще можна
      // встигнути записатися. Історичні заняття тут не несуть цінності.
      (schedulesQuery.data ?? []).filter(
        (schedule) =>
          !hasSessionStarted(schedule.start_time) &&
          (filter === "ALL" || schedule.type === filter)
      ),
    [filter, schedulesQuery.data]
  );

  const pendingCheckoutMap = useMemo(() => {
    // Зливає локально створену доплату з already-persisted pending payment, щоб UI переживав refetch.
    const persistedPending = (myPaymentsQuery.data ?? []).reduce<
      Record<string, { paymentId: string; amount: number }>
    >((accumulator, payment) => {
      if (
        payment.purpose === "BOOKING_EXTRA" &&
        payment.status === "PENDING" &&
        payment.booking_class_id
      ) {
        accumulator[payment.booking_class_id] = {
          paymentId: payment.id,
          amount: Number(payment.amount)
        };
      }
      return accumulator;
    }, {});

    return {
      ...persistedPending,
      ...pendingCheckout
    };
  }, [myPaymentsQuery.data, pendingCheckout]);

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <h1>Розклад занять</h1>
          <p className="muted">Клієнтський список доступних занять і бронювань.</p>
        </div>

        <div className="chips">
          {classTypes.map((classType) => (
            <button
              key={classType}
              className={filter === classType ? "chip active" : "chip"}
              onClick={() => setFilter(classType)}
            >
              {classType === "ALL" ? "Усі" : classType}
            </button>
          ))}
        </div>

        {schedulesQuery.isLoading ? <p className="muted">Завантаження розкладу...</p> : null}
        {schedulesQuery.isError ? (
          <p className="error-banner">
            {schedulesQuery.error instanceof Error
              ? schedulesQuery.error.message
              : "Не вдалося завантажити розклад."}
          </p>
        ) : null}
        {bookMutation.isError ? (
          <p className="error-banner">
            {bookMutation.error instanceof Error
              ? bookMutation.error.message
              : "Не вдалося записатися на заняття."}
          </p>
        ) : null}
        {paidCheckoutMutation.isError ? (
          <p className="error-banner">
            {paidCheckoutMutation.error instanceof Error
              ? paidCheckoutMutation.error.message
              : "Не вдалося створити доплату."}
          </p>
        ) : null}
        {confirmPaidMutation.isError ? (
          <p className="error-banner">
            {confirmPaidMutation.error instanceof Error
              ? confirmPaidMutation.error.message
              : "Не вдалося підтвердити оплату заняття."}
          </p>
        ) : null}

        <div className="schedule-grid">
          {filteredSchedules.length ? (
            filteredSchedules.map((schedule) => {
              const { confirmedBookings } = getScheduleStats(schedule);
              const pendingPayment = pendingCheckoutMap[schedule.id];
              // Для кнопки важливо відрізняти "вже підтверджено" від "ще є pending оплата".
              const isAlreadyBooked = schedule.bookings.some(
                (booking) => booking.user_id === user?.id && booking.status === "CONFIRMED"
              );

              return (
                <article className="schedule-item" key={schedule.id}>
                  <div className="schedule-item-header">
                    <div>
                      <p className="eyebrow">{schedule.type}</p>
                      <h2>{schedule.title}</h2>
                    </div>
                  </div>
                  <p className="muted">
                    {new Date(schedule.start_time).toLocaleString("uk-UA")} -{" "}
                    {new Date(schedule.end_time).toLocaleString("uk-UA")}
                  </p>
                  <p className="muted">
                    {schedule.is_paid_extra
                      ? `Додатково платне заняття · ${schedule.extra_price ?? 0} UAH`
                      : "Входить у дію абонемента"}
                  </p>
                  <dl className="details compact-details">
                    <div>
                      <dt>Тренер</dt>
                      <dd>
                        {schedule.trainer.first_name} {schedule.trainer.last_name}
                      </dd>
                    </div>
                    <div>
                      <dt>Записи</dt>
                      <dd>
                        {confirmedBookings}/{schedule.capacity}
                      </dd>
                    </div>
                  </dl>
                  {schedule.recurrence ? <p className="muted">{schedule.recurrence.summary}</p> : null}
                  <div className="actions-row">
                    {isAlreadyBooked ? (
                      <button className="secondary-button" disabled>
                        Ви записані
                      </button>
                    ) : schedule.is_paid_extra ? (
                      <button
                        className="secondary-button"
                        onClick={() => paidCheckoutMutation.mutate(schedule.id)}
                        disabled={paidCheckoutMutation.isPending || Boolean(pendingPayment)}
                      >
                        {paidCheckoutMutation.isPending
                          ? "Створення доплати..."
                          : pendingPayment
                            ? "Доплату створено"
                            : "Створити доплату"}
                      </button>
                    ) : (
                      <button
                        className="secondary-button"
                        onClick={() => bookMutation.mutate(schedule.id)}
                        disabled={bookMutation.isPending}
                      >
                        {bookMutation.isPending ? "Бронювання..." : "Записатись"}
                      </button>
                    )}
                  </div>
                  {schedule.is_paid_extra && pendingPayment ? (
                    <div className="surface-card schedule-payment-card">
                      <p className="eyebrow">Доплата створена</p>
                      <h3>Крок 2. Підтвердьте оплату</h3>
                      <p className="muted">
                        Сума доплати: UAH {pendingPayment.amount.toLocaleString("uk-UA")}. Після
                        підтвердження оплати вас буде остаточно записано на заняття.
                      </p>
                      <div className="actions-row">
                        <button
                          className="secondary-button"
                          onClick={() => confirmPaidMutation.mutate(pendingPayment.paymentId)}
                          disabled={confirmPaidMutation.isPending}
                        >
                          {confirmPaidMutation.isPending
                            ? "Підтвердження..."
                            : "Підтвердити оплату і запис"}
                        </button>
                      </div>
                    </div>
                  ) : null}
                </article>
              );
            })
          ) : (
            <article className="schedule-item empty-card">
              <h2>Заняття ще не створені</h2>
              <p className="muted">Додайте перші заняття або дочекайтесь завантаження даних.</p>
            </article>
          )}
        </div>
      </section>
    </main>
  );
}
