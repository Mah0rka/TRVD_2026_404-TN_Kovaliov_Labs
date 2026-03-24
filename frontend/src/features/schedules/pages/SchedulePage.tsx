import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createBooking,
  createSchedule,
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
  const [form, setForm] = useState({
    title: "",
    type: "GROUP" as "GROUP" | "PERSONAL",
    startTime: "",
    endTime: "",
    capacity: 10,
    trainerId: ""
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
      setForm({ title: "", type: "GROUP", startTime: "", endTime: "", capacity: 10, trainerId: "" });
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

  const filteredSchedules = useMemo(() => {
    if (!schedulesQuery.data) {
      return [];
    }

    return schedulesQuery.data.filter((schedule) => filter === "ALL" || schedule.type === filter);
  }, [filter, schedulesQuery.data]);

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
                (isAdmin && !form.trainerId)
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

        <div className="schedule-grid">
          {filteredSchedules.length ? (
            filteredSchedules.map((schedule) => {
              const confirmedBookings = schedule.bookings.filter((booking) => booking.status === "CONFIRMED").length;
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
                      <button
                        className="secondary-button"
                        onClick={() => bookMutation.mutate(schedule.id)}
                        disabled={bookMutation.isPending}
                      >
                        {bookMutation.isPending ? "Бронювання..." : "Записатись"}
                      </button>
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
