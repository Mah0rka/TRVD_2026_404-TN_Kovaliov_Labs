import type { DatesSetArg, EventContentArg } from "@fullcalendar/core";

import type { RecurrenceScope, RecurrenceWeekday, Schedule } from "../../../shared/api";

// Цей модуль збирає всі чисті helper-и для schedule-flow, щоб компоненти вище
// не були перевантажені date/recurrence/form трансформаціями.

export const classTypes = ["ALL", "GROUP", "PERSONAL"] as const;
export const weekdayOptions: Array<{ code: RecurrenceWeekday; label: string }> = [
  { code: "MO", label: "Пн" },
  { code: "TU", label: "Вт" },
  { code: "WE", label: "Ср" },
  { code: "TH", label: "Чт" },
  { code: "FR", label: "Пт" },
  { code: "SA", label: "Сб" },
  { code: "SU", label: "Нд" }
];

export type ClassTypeFilter = (typeof classTypes)[number];
export type StaffView = "timeGridWeek" | "timeGridDay";
export type RecurrenceEndMode = "NEVER" | "UNTIL" | "COUNT";
export type EditorMode = "create" | "edit";

export type ScheduleFormState = {
  title: string;
  type: "GROUP" | "PERSONAL";
  startTime: string;
  endTime: string;
  capacity: number;
  trainerId: string;
  isPaidExtra: boolean;
  extraPrice: number;
  recurrenceEnabled: boolean;
  recurrenceFrequency: "DAILY" | "WEEKLY" | "MONTHLY";
  recurrenceInterval: number;
  recurrenceByWeekday: RecurrenceWeekday[];
  recurrenceEndMode: RecurrenceEndMode;
  recurrenceUntil: string;
  recurrenceCount: number;
  scope: RecurrenceScope;
};

export type EditorState = {
  mode: EditorMode;
  schedule: Schedule | null;
  form: ScheduleFormState;
};

const CLUB_OPEN_HOUR = 6;
const CLUB_CLOSE_HOUR = 22;

export function getInitialStaffView(): StaffView {
  // На вузькому екрані day-view значно читабельніший за week-view.
  if (typeof window !== "undefined" && window.innerWidth < 900) {
    return "timeGridDay";
  }

  return "timeGridWeek";
}

export function toCalendarRange(info: DatesSetArg) {
  return {
    // FullCalendar повертає end як exclusive boundary, а бекенд працює
    // з inclusive фільтром, тому віднімаємо 1 секунду.
    from: info.start.toISOString(),
    to: new Date(info.end.getTime() - 1000).toISOString()
  };
}

export function getInitialCalendarRange() {
  // На старті беремо невелике вікно "вчора -> +8 днів", щоб календар відразу
  // показав актуальний тиждень і захопив сусідні слоти для навігації.
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - 1);
  const end = new Date(now);
  end.setDate(end.getDate() + 8);
  end.setHours(23, 59, 59, 999);

  return {
    from: start.toISOString(),
    to: end.toISOString()
  };
}

export function getRoundedSlot(hoursFromNow = 1) {
  // Нове заняття за замовчуванням створюється на рівну годину вперед,
  // щоб менеджеру не доводилося вручну виправляти випадкові хвилини/секунди.
  const value = new Date();
  value.setMinutes(0, 0, 0);
  value.setHours(value.getHours() + hoursFromNow);
  return value;
}

export function toLocalInputValue(isoString: string): string {
  // datetime-local працює без timezone suffix, тому перед відображенням
  // компенсуємо timezone offset браузера.
  const date = new Date(isoString);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export function toIsoString(localValue: string): string {
  // Зворотня операція для відправки local form values назад у backend API.
  return new Date(localValue).toISOString();
}

export function formatCalendarDate(isoString: string): string {
  return new Date(isoString).toLocaleString("uk-UA", {
    day: "2-digit",
    month: "long",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function getDefaultWeekday(startTime: string): RecurrenceWeekday[] {
  const date = new Date(startTime);
  const codes: RecurrenceWeekday[] = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"];
  return [codes[date.getDay()]];
}

export function formatEventTimeLabel(isoString: string): string {
  return new Date(isoString).toLocaleTimeString("uk-UA", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function formatEventTimeRange(schedule: Schedule): string {
  return `${formatEventTimeLabel(schedule.start_time)} - ${formatEventTimeLabel(schedule.end_time)}`;
}

export function isFormWithinClubHours(form: ScheduleFormState): boolean {
  const start = new Date(form.startTime);
  const end = new Date(form.endTime);
  const sameDay =
    start.getFullYear() === end.getFullYear() &&
    start.getMonth() === end.getMonth() &&
    start.getDate() === end.getDate();

  if (!sameDay || end <= start) {
    return false;
  }

  const startMinutes = start.getHours() * 60 + start.getMinutes();
  const endMinutes = end.getHours() * 60 + end.getMinutes();

  // Правило навмисно вимагає повного потрапляння в клубні години, а не
  // лише старту в цьому діапазоні.
  return startMinutes >= CLUB_OPEN_HOUR * 60 && endMinutes <= CLUB_CLOSE_HOUR * 60;
}

export function getFormValidationError(
  form: ScheduleFormState,
  isManagement: boolean
): string | null {
  // Валідатор повертає одне повідомлення для верхнього banner-а модалки.
  // Тут немає field-level error map, бо форма відносно компактна і лінійна.
  if (!form.title.trim() || !form.startTime || !form.endTime) {
    return "Заповніть назву та часовий інтервал заняття.";
  }

  const start = new Date(form.startTime);
  const end = new Date(form.endTime);
  if (end <= start) {
    return "Час завершення має бути пізніше за час початку.";
  }

  if (!isFormWithinClubHours(form)) {
    return "Клуб працює з 06:00 до 22:00, тому заняття має повністю вкладатися в цей інтервал.";
  }

  if (isManagement && !form.trainerId) {
    return "Оберіть тренера для заняття.";
  }

  if (form.isPaidExtra && form.extraPrice <= 0) {
    return "Для платного заняття потрібно вказати додаткову вартість.";
  }

  if (
    form.recurrenceEnabled &&
    form.recurrenceFrequency === "WEEKLY" &&
    form.recurrenceByWeekday.length === 0
  ) {
    return "Для weekly-повторення оберіть хоча б один день тижня.";
  }

  return null;
}

export function createDefaultForm(start?: Date, end?: Date, trainerId = ""): ScheduleFormState {
  const defaultStart = start ?? getRoundedSlot(1);
  const defaultEnd = end ?? new Date(defaultStart.getTime() + 60 * 60 * 1000);

  // Тут живуть усі UI-дефолти для create-mode. Один helper важливий, щоб
  // modal і календарний select не роз'їжджались у початкових значеннях.
  return {
    title: "",
    type: "GROUP",
    startTime: toLocalInputValue(defaultStart.toISOString()),
    endTime: toLocalInputValue(defaultEnd.toISOString()),
    capacity: 10,
    trainerId,
    isPaidExtra: false,
    extraPrice: 0,
    recurrenceEnabled: false,
    recurrenceFrequency: "WEEKLY",
    recurrenceInterval: 1,
    recurrenceByWeekday: getDefaultWeekday(defaultStart.toISOString()),
    recurrenceEndMode: "NEVER",
    recurrenceUntil: "",
    recurrenceCount: 8,
    scope: "OCCURRENCE"
  };
}

export function createFormFromSchedule(schedule: Schedule): ScheduleFormState {
  const recurrence = schedule.recurrence;

  // Edit-mode форма віддзеркалює бекендовий schedule, але з локальним форматом
  // дат для input[type=datetime-local].
  return {
    title: schedule.title,
    type: schedule.type,
    startTime: toLocalInputValue(schedule.start_time),
    endTime: toLocalInputValue(schedule.end_time),
    capacity: schedule.capacity,
    trainerId: schedule.trainer_id,
    isPaidExtra: schedule.is_paid_extra,
    extraPrice: Number(schedule.extra_price ?? 0),
    recurrenceEnabled: Boolean(recurrence),
    recurrenceFrequency: recurrence?.frequency ?? "WEEKLY",
    recurrenceInterval: recurrence?.interval ?? 1,
    recurrenceByWeekday:
      recurrence?.byWeekday?.length ? recurrence.byWeekday : getDefaultWeekday(schedule.start_time),
    recurrenceEndMode: recurrence?.count ? "COUNT" : recurrence?.until ? "UNTIL" : "NEVER",
    recurrenceUntil: recurrence?.until ? toLocalInputValue(recurrence.until) : "",
    recurrenceCount: recurrence?.count ?? 8,
    scope: "OCCURRENCE"
  };
}

export function buildRecurrencePayload(form: ScheduleFormState) {
  if (!form.recurrenceEnabled) {
    return undefined;
  }

  // Повертаємо лише ті поля, які backend очікує в recurrence payload.
  // Якщо weekly-дні не обрані вручну, fallback-имо до weekday стартового часу.
  return {
    frequency: form.recurrenceFrequency,
    interval: form.recurrenceInterval,
    byWeekday:
      form.recurrenceFrequency === "WEEKLY"
        ? form.recurrenceByWeekday.length
          ? form.recurrenceByWeekday
          : getDefaultWeekday(toIsoString(form.startTime))
        : [],
    count: form.recurrenceEndMode === "COUNT" ? form.recurrenceCount : null,
    until:
      form.recurrenceEndMode === "UNTIL" && form.recurrenceUntil
        ? toIsoString(form.recurrenceUntil)
        : null
  };
}

export function getScheduleStats(schedule: Schedule) {
  return {
    // Наразі для UI потрібна лише кількість підтверджених бронювань,
    // але helper залишає місце для майбутнього розширення метрик.
    confirmedBookings: schedule.bookings.filter((booking) => booking.status === "CONFIRMED")
      .length
  };
}

export function renderCalendarEventContent(arg: EventContentArg) {
  const schedule = (arg.event.extendedProps as { schedule: Schedule }).schedule;
  const { confirmedBookings } = getScheduleStats(schedule);

  // Власний renderer дає контроль над щільним виглядом картки слоту в календарі.
  return (
    <div className="staff-calendar-event">
      <span className="staff-calendar-event-title">{schedule.title}</span>
      <span className="staff-calendar-event-meta">
        {formatEventTimeRange(schedule)} · {confirmedBookings}/{schedule.capacity}
      </span>
    </div>
  );
}
