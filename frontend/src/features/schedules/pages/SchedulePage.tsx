import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  confirmPaidBooking,
  createBooking,
  createPaidBookingCheckout,
  createSchedule,
  getMyPayments,
  getScheduleAttendees,
  getSchedules,
  getUsers,
  removeSchedule
} from "../../../shared/api";
import { useAuthStore } from "../../auth";

const classTypes = ["ALL", "GROUP", "PERSONAL"] as const;

export function SchedulePage() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === "ADMIN" || user?.role === "OWNER";
  const isClient = user?.role === "CLIENT";
  const canViewAttendees = user?.role === "TRAINER" || isAdmin;
  const [filter, setFilter] = useState<(typeof classTypes)[number]>("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [selectedAttendeesClassId, setSelectedAttendeesClassId] = useState<string | null>(null);
  const [pendingCheckout, setPendingCheckout] = useState<Record<string, { paymentId: string; amount: number }>>({});
  const [form, setForm] = useState({
    title: "",
    type: "GROUP" as "GROUP" | "PERSONAL",
    startTime: "",
    endTime: "",
    capacity: 10,
    trainerId: "",
    isPaidExtra: false,
    extraPrice: 0
  });

  const schedulesQuery = useQuery({
    queryKey: ["schedules"],
    queryFn: getSchedules
  });

  const attendeesQuery = useQuery({
    queryKey: ["schedule-attendees", selectedAttendeesClassId],
    queryFn: () => getScheduleAttendees(selectedAttendeesClassId as string),
    enabled: Boolean(selectedAttendeesClassId)
  });

  const myPaymentsQuery = useQuery({
    queryKey: ["my-payments"],
    queryFn: getMyPayments,
    enabled: isClient
  });

  const trainersQuery = useQuery({
    queryKey: ["schedule-trainers"],
    queryFn: () => getUsers("TRAINER"),
    enabled: isAdmin
  });

  const createMutation = useMutation({
    mutationFn: createSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
      setShowCreate(false);
      setForm({
        title: "",
        type: "GROUP",
        startTime: "",
        endTime: "",
        capacity: 10,
        trainerId: "",
        isPaidExtra: false,
        extraPrice: 0
      });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: removeSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
      queryClient.invalidateQueries({ queryKey: ["my-classes"] });
    }
  });

  const bookMutation = useMutation({
    mutationFn: createBooking,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
      queryClient.invalidateQueries({ queryKey: ["my-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["my-subscriptions"] });
    }
  });

  const paidCheckoutMutation = useMutation({
    mutationFn: createPaidBookingCheckout,
    onSuccess: (payment, classId) => {
      setPendingCheckout((current) => ({
        ...current,
        [classId]: {
          paymentId: payment.id,
          amount: payment.amount
        }
      }));
      queryClient.invalidateQueries({ queryKey: ["my-payments"] });
    }
  });

  const confirmPaidMutation = useMutation({
    mutationFn: confirmPaidBooking,
    onSuccess: (booking) => {
      setPendingCheckout((current) => {
        const next = { ...current };
        delete next[booking.class_id];
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ["schedules"] });
      queryClient.invalidateQueries({ queryKey: ["my-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["my-subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["my-payments"] });
    }
  });

  const filteredSchedules = useMemo(() => {
    if (!schedulesQuery.data) {
      return [];
    }

    return schedulesQuery.data.filter((schedule) => filter === "ALL" || schedule.type === filter);
  }, [filter, schedulesQuery.data]);

  const pendingCheckoutMap = useMemo(() => {
    const persistedPending = (myPaymentsQuery.data ?? []).reduce<Record<string, { paymentId: string; amount: number }>>(
      (accumulator, payment) => {
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
      },
      {}
    );

    return {
      ...persistedPending,
      ...pendingCheckout
    };
  }, [myPaymentsQuery.data, pendingCheckout]);

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-row">
          <div className="heading-group">
            <p className="eyebrow">Schedules</p>
            <h1>Розклад занять</h1>
            <p className="muted">Один контур розкладу для клієнта, тренера і адміністрації.</p>
          </div>
          {isAdmin ? (
            <button className="secondary-button" onClick={() => setShowCreate((value) => !value)}>
              {showCreate ? "Сховати форму" : "Додати заняття"}
            </button>
          ) : null}
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

        {showCreate ? (
          <div className="create-panel schedule-create-panel">
            <label className="create-panel-field">
              Назва
              <input
                value={form.title}
                onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              />
            </label>
            <label className="create-panel-field">
              Тип
              <select
                value={form.type}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    type: event.target.value as "GROUP" | "PERSONAL"
                  }))
                }
              >
                <option value="GROUP">GROUP</option>
                <option value="PERSONAL">PERSONAL</option>
              </select>
            </label>
            <label className="create-panel-field">
              Початок
              <input
                type="datetime-local"
                value={form.startTime}
                onChange={(event) => setForm((current) => ({ ...current, startTime: event.target.value }))}
              />
            </label>
            <label className="create-panel-field">
              Кінець
              <input
                type="datetime-local"
                value={form.endTime}
                onChange={(event) => setForm((current) => ({ ...current, endTime: event.target.value }))}
              />
            </label>
            <label className="create-panel-field">
              Кількість місць
              <input
                type="number"
                min={1}
                max={100}
                value={form.capacity}
                onChange={(event) =>
                  setForm((current) => ({ ...current, capacity: Number(event.target.value) }))
                }
              />
            </label>
            <label className="create-panel-field">
              Формат оплати
              <select
                value={form.isPaidExtra ? "PAID_EXTRA" : "FREE"}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    isPaidExtra: event.target.value === "PAID_EXTRA",
                    extraPrice: event.target.value === "PAID_EXTRA" ? current.extraPrice || 0 : 0
                  }))
                }
              >
                <option value="FREE">Входить в абонемент</option>
                <option value="PAID_EXTRA">Платне додатково до абонемента</option>
              </select>
            </label>
            {form.isPaidExtra ? (
              <label className="create-panel-field">
                Додаткова вартість
                <input
                  type="number"
                  min={1}
                  step="0.01"
                  value={form.extraPrice}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, extraPrice: Number(event.target.value) }))
                  }
                />
              </label>
            ) : null}
            {isAdmin ? (
              <label className="create-panel-field">
                Тренер
                <select
                  value={form.trainerId}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, trainerId: event.target.value }))
                  }
                >
                  <option value="">Оберіть тренера</option>
                  {trainersQuery.data?.map((trainer) => (
                    <option key={trainer.id} value={trainer.id}>
                      {trainer.first_name} {trainer.last_name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <button
              className="secondary-button create-panel-action"
              onClick={() => createMutation.mutate(form)}
              disabled={
              !form.title ||
              !form.startTime ||
              !form.endTime ||
              createMutation.isPending ||
              (isAdmin && !form.trainerId) ||
              (form.isPaidExtra && form.extraPrice <= 0)
            }
          >
            {createMutation.isPending ? "Створення..." : "Створити заняття"}
            </button>
          </div>
        ) : null}

        {schedulesQuery.isLoading ? <p className="muted">Завантаження розкладу...</p> : null}
        {schedulesQuery.isError ? (
          <p className="error-banner">
            {schedulesQuery.error instanceof Error ? schedulesQuery.error.message : "Не вдалося завантажити розклад."}
          </p>
        ) : null}
        {bookMutation.isError ? (
          <p className="error-banner">
            {bookMutation.error instanceof Error ? bookMutation.error.message : "Не вдалося записатися на заняття."}
          </p>
        ) : null}
        {paidCheckoutMutation.isError ? (
          <p className="error-banner">
            {paidCheckoutMutation.error instanceof Error ? paidCheckoutMutation.error.message : "Не вдалося створити доплату."}
          </p>
        ) : null}
        {confirmPaidMutation.isError ? (
          <p className="error-banner">
            {confirmPaidMutation.error instanceof Error ? confirmPaidMutation.error.message : "Не вдалося підтвердити оплату заняття."}
          </p>
        ) : null}

        <div className="schedule-grid">
          {filteredSchedules.length ? (
            filteredSchedules.map((schedule) => {
              const confirmedBookings = schedule.bookings.filter((booking) => booking.status === "CONFIRMED").length;
              const pendingPayment = pendingCheckoutMap[schedule.id];
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
                    {isAdmin ? (
                      <button
                        className="danger-link"
                        onClick={() => deleteMutation.mutate(schedule.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Видалити
                      </button>
                    ) : null}
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
                  <div className="actions-row">
                    {isClient ? (
                      isAlreadyBooked ? (
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
                      )
                    ) : null}
                    {canViewAttendees && confirmedBookings > 0 ? (
                      <button
                        className="ghost-link"
                        onClick={() =>
                          setSelectedAttendeesClassId((current) => (current === schedule.id ? null : schedule.id))
                        }
                      >
                        {selectedAttendeesClassId === schedule.id ? "Сховати учасників" : "Учасники"}
                      </button>
                    ) : null}
                  </div>
                  {schedule.type === "PERSONAL" ? (
                    <p className="muted">Персональне заняття з тренером {schedule.is_paid_extra ? "оплачується додатково до абонемента." : "входить в абонемент."}</p>
                  ) : null}
                  {schedule.is_paid_extra && pendingPayment ? (
                    <div className="surface-card schedule-payment-card">
                      <p className="eyebrow">Доплата створена</p>
                      <h3>Крок 2. Підтвердьте оплату</h3>
                      <p className="muted">
                        Сума доплати: UAH {pendingPayment.amount.toLocaleString("uk-UA")}. Після підтвердження оплати вас буде остаточно записано на заняття.
                      </p>
                      <div className="actions-row">
                        <button
                          className="secondary-button"
                          onClick={() => confirmPaidMutation.mutate(pendingPayment.paymentId)}
                          disabled={confirmPaidMutation.isPending}
                        >
                          {confirmPaidMutation.isPending ? "Підтвердження..." : "Підтвердити оплату і запис"}
                        </button>
                      </div>
                    </div>
                  ) : null}

                  {selectedAttendeesClassId === schedule.id ? (
                    <div className="attendees-list">
                      {attendeesQuery.isLoading ? <p className="muted">Завантаження учасників...</p> : null}
                      {attendeesQuery.data?.map((attendee) => (
                        <div key={attendee.id} className="attendee-row">
                          <strong>
                            {attendee.user.first_name} {attendee.user.last_name}
                          </strong>
                          <span className="muted">{attendee.user.email}</span>
                        </div>
                      ))}
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
