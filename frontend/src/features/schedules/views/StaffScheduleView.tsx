import { useMemo, useRef, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import type { DateSelectArg, DatesSetArg, EventClickArg } from "@fullcalendar/core";
import interactionPlugin from "@fullcalendar/interaction";
import ukLocale from "@fullcalendar/core/locales/uk";
import rrulePlugin from "@fullcalendar/rrule";
import timeGridPlugin from "@fullcalendar/timegrid";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createSchedule,
  getScheduleAttendees,
  getSchedules,
  getUsers,
  queryKeys,
  removeSchedule,
  updateSchedule
} from "../../../shared/api";
import type { RecurrenceScope, Schedule } from "../../../shared/api";
import { useAuthStore } from "../../auth";
import {
  buildRecurrencePayload,
  classTypes,
  createDefaultForm,
  createFormFromSchedule,
  getFormValidationError,
  getInitialCalendarRange,
  getInitialStaffView,
  renderCalendarEventContent,
  toCalendarRange,
  toIsoString,
  type ClassTypeFilter,
  type EditorState,
  type ScheduleFormState,
  type StaffView
} from "../lib/scheduleShared";
import { ScheduleEditorModal } from "../ui/ScheduleEditorModal";

// StaffScheduleView концентрує весь "операційний" schedule-flow:
// - календар клубу;
// - фільтри за типом і тренером;
// - створення/редагування recurring та разових занять;
// - перегляд учасників активного слоту.
export function StaffScheduleView() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const isManagement = user?.role === "ADMIN" || user?.role === "OWNER";
  const isTrainer = user?.role === "TRAINER";
  // FullCalendar API доступний через ref для навігації кнопками shell-а.
  const calendarRef = useRef<FullCalendar | null>(null);
  const [calendarView, setCalendarView] = useState<StaffView>(getInitialStaffView);
  const [calendarTitle, setCalendarTitle] = useState("");
  const [range, setRange] = useState(getInitialCalendarRange);
  const [filter, setFilter] = useState<ClassTypeFilter>("ALL");
  const [showMineOnly, setShowMineOnly] = useState(Boolean(isTrainer));
  const [selectedTrainerId, setSelectedTrainerId] = useState("ALL");
  const [editorState, setEditorState] = useState<EditorState | null>(null);

  const schedulesQuery = useQuery({
    queryKey: queryKeys.schedules.calendar(range.from, range.to),
    // Підтягуємо лише потрібний видимий діапазон календаря, а не весь масив занять.
    queryFn: () => getSchedules(range)
  });

  const trainersQuery = useQuery({
    queryKey: queryKeys.schedules.trainers(),
    queryFn: () => getUsers("TRAINER"),
    enabled: isManagement
  });

  const canViewActiveAttendees = Boolean(
    editorState?.schedule && (isManagement || editorState.schedule.trainer_id === user?.id)
  );

  const attendeesQuery = useQuery({
    queryKey: queryKeys.schedules.attendees(editorState?.schedule?.id),
    queryFn: () => getScheduleAttendees(editorState?.schedule?.id as string),
    // Список учасників відкриваємо лише для активного schedule у modal
    // і лише якщо в поточного користувача є право його бачити.
    enabled: canViewActiveAttendees
  });

  const createMutation = useMutation({
    mutationFn: createSchedule,
    onSuccess: () => {
      // Після створення заняття оновлюємо і календар, і surfaces тренера,
      // які читають ті самі заняття через інші query namespace-и.
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.classes.mine() });
      setEditorState(null);
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      input
    }: {
      id: string;
      input: Parameters<typeof updateSchedule>[1];
    }) => updateSchedule(id, input),
    onSuccess: () => {
      // Та сама invalidation policy потрібна і для редагування, бо змінитися
      // можуть час, тренер, recurring-зв'язок і видимість у кількох екранах.
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.classes.mine() });
      setEditorState(null);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: ({ id, scope }: { id: string; scope: RecurrenceScope }) =>
      removeSchedule(id, scope),
    onSuccess: () => {
      // Видалення recurrence може вплинути не на один слот, тому найнадійніше
      // просто перевитягнути всі пов'язані schedule/class datasets.
      queryClient.invalidateQueries({ queryKey: queryKeys.schedules.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.classes.mine() });
      setEditorState(null);
    }
  });

  const visibleSchedules = useMemo(() => {
    // Усі role/filter обмеження зібрані тут, щоб FullCalendar отримував уже готовий набір подій.
    return (schedulesQuery.data ?? []).filter((schedule) => {
      if (filter !== "ALL" && schedule.type !== filter) {
        return false;
      }

      if (isManagement && selectedTrainerId !== "ALL" && schedule.trainer_id !== selectedTrainerId) {
        return false;
      }

      if (isTrainer && showMineOnly && schedule.trainer_id !== user?.id) {
        return false;
      }

      return true;
    });
  }, [filter, isManagement, isTrainer, schedulesQuery.data, selectedTrainerId, showMineOnly, user?.id]);

  const calendarEvents = useMemo(
    () =>
      // FullCalendar працює зі своїм event shape, тому конвертацію виносимо
      // в окремий useMemo і не тягнемо сирий backend DTO напряму в компонент бібліотеки.
      visibleSchedules.map((schedule) => ({
        id: schedule.id,
        title: schedule.title,
        start: schedule.start_time,
        end: schedule.end_time,
        classNames: [
          "staff-calendar-slot",
          schedule.type === "PERSONAL"
            ? "staff-calendar-slot-personal"
            : "staff-calendar-slot-group",
          schedule.series_id ? "staff-calendar-slot-recurring" : "",
          schedule.trainer_id === user?.id ? "staff-calendar-slot-owned" : ""
        ].filter(Boolean),
        extendedProps: {
          schedule
        }
      })),
    [user?.id, visibleSchedules]
  );

  const activeSchedule = editorState?.schedule;
  const canEditActiveSchedule = Boolean(
    activeSchedule && (isManagement || (isTrainer && activeSchedule.trainer_id === user?.id))
  );
  const canDeleteActiveSchedule = Boolean(activeSchedule && isManagement);
  const editorValidationError = editorState
    ? getFormValidationError(editorState.form, isManagement)
    : null;

  function changeCalendarView(nextView: StaffView) {
    // Тримаємо React-state і imperative FullCalendar API синхронними,
    // щоб активний чип і реальний вигляд календаря не розходилися.
    setCalendarView(nextView);
    calendarRef.current?.getApi().changeView(nextView);
  }

  function openCreateEditor(start?: Date, end?: Date) {
    // Створення нових занять доступне лише менеджменту. Тренер у цьому інтерфейсі
    // працює переважно як оператор власного розкладу, а не як автор нових слотів.
    if (!isManagement) {
      return;
    }

    setEditorState({
      mode: "create",
      schedule: null,
      form: createDefaultForm(start, end, selectedTrainerId !== "ALL" ? selectedTrainerId : "")
    });
  }

  function openEditEditor(schedule: Schedule) {
    // Для edit-mode form одразу заповнюємо з бекендового schedule,
    // включно з recurrence-параметрами та scope за замовчуванням.
    setEditorState({
      mode: "edit",
      schedule,
      form: createFormFromSchedule(schedule)
    });
  }

  function handleCalendarDatesSet(info: DatesSetArg) {
    setCalendarTitle(info.view.title);
    setRange(toCalendarRange(info));
  }

  function handleCalendarSelect(info: DateSelectArg) {
    openCreateEditor(info.start, info.end);
  }

  function handleEventClick(info: EventClickArg) {
    const schedule = (info.event.extendedProps as { schedule: Schedule }).schedule;
    openEditEditor(schedule);
  }

  function resetModal() {
    setEditorState(null);
  }

  function updateForm(update: Partial<ScheduleFormState>) {
    setEditorState((current) =>
      current
        ? {
            ...current,
            form: {
              ...current.form,
              ...update
            }
          }
        : current
    );
  }

  async function handleSave() {
    if (!editorState) {
      return;
    }

    // Тут ми збираємо payload у форму, очікувану API. Модалка працює
    // з локальним form-state, а бекенд — з нормалізованими ISO/number значеннями.
    const recurrence = buildRecurrencePayload(editorState.form);
    const payload = {
      title: editorState.form.title.trim(),
      type: editorState.form.type,
      startTime: toIsoString(editorState.form.startTime),
      endTime: toIsoString(editorState.form.endTime),
      capacity: Number(editorState.form.capacity),
      trainerId: isManagement ? editorState.form.trainerId || undefined : undefined,
      isPaidExtra: editorState.form.isPaidExtra,
      extraPrice: editorState.form.isPaidExtra ? Number(editorState.form.extraPrice) : null,
      recurrence
    };

    if (editorState.mode === "create") {
      await createMutation.mutateAsync(payload);
      return;
    }

    // Для edit flow обов'язково передаємо scope, щоб API зрозумів,
    // чи правка стосується occurrence, following або всієї series.
    await updateMutation.mutateAsync({
      id: editorState.schedule!.id,
      input: {
        ...payload,
        scope: editorState.form.scope
      }
    });
  }

  async function handleDelete() {
    if (!editorState?.schedule) {
      return;
    }

    // Видалення також залежить від recurrence scope і не завжди означає
    // фізичне видалення лише одного запису.
    await deleteMutation.mutateAsync({
      id: editorState.schedule.id,
      scope: editorState.form.scope
    });
  }

  const mutationError =
    createMutation.error ?? updateMutation.error ?? deleteMutation.error ?? attendeesQuery.error;

  return (
    <main className="screen">
      <section className="card schedule-card schedule-calendar-card">
        <div className="heading-row schedule-calendar-header">
          <div className="heading-group">
            <h1>Календар занять</h1>
            <p className="muted">
              Робочий week/day-календар для тренерів, адміністрації та власника клубу.
            </p>
          </div>
          <div className="schedule-calendar-toolbar-actions">
            {isTrainer ? (
              <div className="schedule-calendar-trainer-toggle" aria-label="Фільтр тренера">
                <button
                  className={showMineOnly ? "chip active" : "chip"}
                  type="button"
                  onClick={() => setShowMineOnly(true)}
                >
                  Мої заняття
                </button>
                <button
                  className={!showMineOnly ? "chip active" : "chip"}
                  type="button"
                  onClick={() => setShowMineOnly(false)}
                >
                  Увесь клуб
                </button>
              </div>
            ) : null}
            {isManagement ? (
              <button className="secondary-button" type="button" onClick={() => openCreateEditor()}>
                Додати заняття
              </button>
            ) : null}
          </div>
        </div>

        <div className="schedule-calendar-toolbar">
          <div className="schedule-calendar-nav">
            <button
              className="ghost-link"
              type="button"
              aria-label="Попередній період"
              onClick={() => calendarRef.current?.getApi().prev()}
            >
              ←
            </button>
            <button
              className="ghost-link"
              type="button"
              aria-label="Наступний період"
              onClick={() => calendarRef.current?.getApi().next()}
            >
              →
            </button>
            <button
              className="ghost-link"
              type="button"
              onClick={() => calendarRef.current?.getApi().today()}
            >
              Сьогодні
            </button>
          </div>

          <div className="schedule-calendar-view-switch">
            <button
              className={calendarView === "timeGridWeek" ? "chip active" : "chip"}
              type="button"
              onClick={() => changeCalendarView("timeGridWeek")}
            >
              Тиждень
            </button>
            <button
              className={calendarView === "timeGridDay" ? "chip active" : "chip"}
              type="button"
              onClick={() => changeCalendarView("timeGridDay")}
            >
              День
            </button>
          </div>

          <div className="schedule-calendar-period">
            <strong>{calendarTitle}</strong>
          </div>
        </div>

        <div className="schedule-calendar-filters">
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

          {isManagement ? (
            <label className="schedule-inline-filter">
              Фільтр тренера
              <select
                aria-label="Фільтр тренера"
                value={selectedTrainerId}
                onChange={(event) => setSelectedTrainerId(event.target.value)}
              >
                <option value="ALL">Усі тренери</option>
                {trainersQuery.data?.map((trainer) => (
                  <option key={trainer.id} value={trainer.id}>
                    {trainer.first_name} {trainer.last_name}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
        </div>

        {schedulesQuery.isLoading ? <p className="muted">Завантаження календаря...</p> : null}
        {mutationError ? (
          <p className="error-banner">
            {mutationError instanceof Error
              ? mutationError.message
              : "Не вдалося виконати операцію з розкладом."}
          </p>
        ) : null}

        <div className="schedule-calendar-shell">
          <FullCalendar
            ref={calendarRef}
            plugins={[timeGridPlugin, interactionPlugin, rrulePlugin]}
            locale={ukLocale}
            headerToolbar={false}
            initialView={calendarView}
            allDaySlot={false}
            height="auto"
            slotMinTime="06:00:00"
            slotMaxTime="23:00:00"
            slotDuration="01:00:00"
            selectable={isManagement}
            unselectAuto
            nowIndicator
            selectMirror={isManagement}
            select={handleCalendarSelect}
            datesSet={handleCalendarDatesSet}
            eventClick={handleEventClick}
            events={calendarEvents}
            eventContent={renderCalendarEventContent}
            eventMinHeight={40}
            slotLabelFormat={{ hour: "2-digit", minute: "2-digit", hour12: false }}
            eventTimeFormat={{ hour: "2-digit", minute: "2-digit", hour12: false }}
            dayHeaderFormat={{ weekday: "short", day: "numeric", month: "short" }}
          />
        </div>
      </section>

      {editorState ? (
        <ScheduleEditorModal
          editorState={editorState}
          attendees={attendeesQuery.data ?? []}
          isAttendeesLoading={attendeesQuery.isLoading}
          canDelete={canDeleteActiveSchedule}
          canEdit={editorState.mode === "create" || canEditActiveSchedule}
          canViewAttendees={canViewActiveAttendees}
          isManagement={isManagement}
          createPending={createMutation.isPending}
          updatePending={updateMutation.isPending}
          deletePending={deleteMutation.isPending}
          trainers={trainersQuery.data ?? []}
          validationError={editorValidationError}
          onClose={resetModal}
          onDelete={handleDelete}
          onFormChange={updateForm}
          onSave={handleSave}
        />
      ) : null}
    </main>
  );
}
