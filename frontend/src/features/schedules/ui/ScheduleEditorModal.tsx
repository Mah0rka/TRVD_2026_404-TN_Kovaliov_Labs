import { Link } from "react-router-dom";

import type { RecurrenceScope, ScheduleAttendee } from "../../../shared/api";
import {
  formatCalendarDate,
  getDefaultWeekday,
  getScheduleStats,
  toIsoString,
  type EditorState,
  type RecurrenceEndMode,
  type ScheduleFormState,
  weekdayOptions
} from "../lib/scheduleShared";

type ScheduleEditorModalProps = {
  editorState: EditorState;
  attendees: ScheduleAttendee[];
  isAttendeesLoading: boolean;
  canDelete: boolean;
  canEdit: boolean;
  canViewAttendees: boolean;
  isManagement: boolean;
  createPending: boolean;
  updatePending: boolean;
  deletePending: boolean;
  validationError: string | null;
  trainers: Array<{
    id: string;
    first_name: string;
    last_name: string;
  }>;
  onClose: () => void;
  onDelete: () => void;
  onFormChange: (update: Partial<ScheduleFormState>) => void;
  onSave: () => void;
};

export function ScheduleEditorModal({
  editorState,
  attendees,
  isAttendeesLoading,
  canDelete,
  canEdit,
  canViewAttendees,
  isManagement,
  createPending,
  updatePending,
  deletePending,
  validationError,
  trainers,
  onClose,
  onDelete,
  onFormChange,
  onSave
}: ScheduleEditorModalProps) {
  const schedule = editorState.schedule;
  // Для create-mode статистика не потрібна, але в edit-mode показуємо заповненість слоту
  // прямо в боковій колонці, щоб редактор не існував відірвано від фактичних даних.
  const stats = schedule ? getScheduleStats(schedule) : null;

  return (
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <section
        className="modal-panel schedule-editor-modal"
        role="dialog"
        aria-modal="true"
        aria-label={editorState.mode === "create" ? "Створення заняття" : "Редагування заняття"}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="participant-modal-toolbar schedule-editor-toolbar">
          <div className="heading-group">
            <p className="eyebrow">
              {editorState.mode === "create" ? "Нове заняття" : "Заняття календаря"}
            </p>
            <h3>{editorState.mode === "create" ? "Створити заняття" : schedule?.title}</h3>
            {schedule ? (
              <p className="muted">
                {formatCalendarDate(schedule.start_time)} - {formatCalendarDate(schedule.end_time)}
              </p>
            ) : (
              <p className="muted">
                {/* Користувач часто відкриває модалку зі select у календарі,
                    тому підказка пояснює, чому час уже частково заповнений. */}
                Клік по порожньому слоту відкриває форму створення в потрібний час.
              </p>
            )}
          </div>
          <button className="ghost-link" type="button" onClick={onClose}>
            Закрити
          </button>
        </div>

        <div className="detail-layout-modal schedule-editor-layout">
          <div className="surface-card detail-panel schedule-editor-sidebar">
            <div className="summary-grid">
              <div className="summary-item">
                <span className="muted">Тренер</span>
                <strong>
                  {schedule
                    ? `${schedule.trainer.first_name} ${schedule.trainer.last_name}`
                    : "Буде призначено під час створення"}
                </strong>
              </div>
              <div className="summary-item">
                <span className="muted">Записи</span>
                <strong>{schedule ? `${stats?.confirmedBookings}/${schedule.capacity}` : "0/0"}</strong>
              </div>
            </div>

            {schedule?.recurrence ? (
              <div className="stack-table-card">
                <h3>Recurring</h3>
                {/* Бекенд повертає людський summary recurrence, тому UI не
                    відтворює правило вручну з byWeekday/count/until. */}
                <p className="muted">{schedule.recurrence.summary}</p>
                {schedule.is_series_exception ? (
                  <p className="muted">Це окремо змінена occurrence всередині серії.</p>
                ) : null}
              </div>
            ) : null}

            {canViewAttendees ? (
              <div className="stack-table-card">
                <h3>Учасники</h3>
                {isAttendeesLoading ? <p className="muted">Завантаження...</p> : null}
                {!isAttendeesLoading && !attendees.length ? (
                  <p className="muted">Поки без підтверджених записів.</p>
                ) : null}
                {attendees.map((attendee) => (
                  <div key={attendee.id} className="attendee-row">
                    <strong>
                      {attendee.user.first_name} {attendee.user.last_name}
                    </strong>
                    <span className="muted">{attendee.user.email}</span>
                  </div>
                ))}
                <Link className="ghost-link" to="/dashboard/my-classes">
                  Відкрити Класи
                </Link>
              </div>
            ) : schedule ? (
              <div className="stack-table-card">
                <h3>Учасники</h3>
                <p className="muted">
                  Деталі учасників доступні лише менеджменту або тренеру цього заняття.
                </p>
              </div>
            ) : null}
          </div>

          <div className="surface-card detail-panel schedule-editor-main">
            <div className="form-grid participant-form-grid">
              <label>
                Назва
                <input
                  aria-label="Назва"
                  value={editorState.form.title}
                  onChange={(event) => onFormChange({ title: event.target.value })}
                />
              </label>

              <label>
                Тип
                <select
                  aria-label="Тип"
                  value={editorState.form.type}
                  onChange={(event) =>
                    onFormChange({ type: event.target.value as "GROUP" | "PERSONAL" })
                  }
                >
                  <option value="GROUP">GROUP</option>
                  <option value="PERSONAL">PERSONAL</option>
                </select>
              </label>

              <label>
                Початок
                <input
                  aria-label="Початок"
                  type="datetime-local"
                  value={editorState.form.startTime}
                  onChange={(event) => {
                    const nextStartTime = event.target.value;
                    onFormChange({
                      // Для weekly recurrence тримаємо weekday синхронним із новим стартом,
                      // щоб freshly-created series не отримала порожній або хибний день.
                      startTime: nextStartTime,
                      recurrenceByWeekday:
                        editorState.form.recurrenceFrequency === "WEEKLY" &&
                        editorState.mode === "create"
                          ? getDefaultWeekday(toIsoString(nextStartTime))
                          : editorState.form.recurrenceByWeekday
                    });
                  }}
                />
              </label>

              <label>
                Кінець
                <input
                  aria-label="Кінець"
                  type="datetime-local"
                  value={editorState.form.endTime}
                  onChange={(event) => onFormChange({ endTime: event.target.value })}
                />
              </label>

              <label>
                Кількість місць
                <input
                  aria-label="Кількість місць"
                  type="number"
                  min={1}
                  max={100}
                  value={editorState.form.capacity}
                  onChange={(event) => onFormChange({ capacity: Number(event.target.value) })}
                />
              </label>

              {isManagement ? (
                <label>
                  Тренер
                  <select
                    aria-label="Тренер"
                    value={editorState.form.trainerId}
                    onChange={(event) => onFormChange({ trainerId: event.target.value })}
                  >
                    <option value="">Оберіть тренера</option>
                    {trainers.map((trainer) => (
                      <option key={trainer.id} value={trainer.id}>
                        {trainer.first_name} {trainer.last_name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              <label>
                Формат оплати
                <select
                  aria-label="Формат оплати"
                  value={editorState.form.isPaidExtra ? "PAID_EXTRA" : "FREE"}
                  onChange={(event) =>
                    onFormChange({
                      isPaidExtra: event.target.value === "PAID_EXTRA",
                      extraPrice:
                        event.target.value === "PAID_EXTRA"
                          ? editorState.form.extraPrice || 450
                          : 0
                    })
                  }
                >
                  <option value="FREE">Входить в абонемент</option>
                  <option value="PAID_EXTRA">Платне додатково</option>
                </select>
              </label>

              {editorState.form.isPaidExtra ? (
                <label>
                  Додаткова вартість
                  <input
                    aria-label="Додаткова вартість"
                    type="number"
                    min={1}
                    step="0.01"
                    value={editorState.form.extraPrice}
                    onChange={(event) => onFormChange({ extraPrice: Number(event.target.value) })}
                  />
                </label>
              ) : null}

              {editorState.mode === "create" || schedule?.series_id ? (
                <div className="stack-table-card schedule-recurring-card">
                  <div className="heading-row">
                    <div className="heading-group">
                      <h3>Recurring-серія</h3>
                      <p className="muted">
                        Підтримуються daily, weekly та monthly правила.
                      </p>
                    </div>
                    {editorState.mode === "create" ? (
                      <button
                        className={editorState.form.recurrenceEnabled ? "chip active" : "chip"}
                        type="button"
                        onClick={() =>
                          onFormChange({
                            // Просте toggle-перемикання важливе для UX: форма не
                            // створює окремий складний wizard для recurring flow.
                            recurrenceEnabled: !editorState.form.recurrenceEnabled
                          })
                        }
                      >
                        {editorState.form.recurrenceEnabled ? "Повторюється" : "Разове"}
                      </button>
                    ) : (
                      <span className="status-pill warning">Серія</span>
                    )}
                  </div>

                  {editorState.form.recurrenceEnabled ? (
                    <div className="form-grid compact-filter-panel">
                      <label>
                        Частота
                        <select
                          aria-label="Частота"
                          value={editorState.form.recurrenceFrequency}
                          onChange={(event) =>
                            onFormChange({
                              recurrenceFrequency: event.target.value as
                                | "DAILY"
                                | "WEEKLY"
                                | "MONTHLY"
                            })
                          }
                        >
                          <option value="DAILY">Щодня</option>
                          <option value="WEEKLY">Щотижня</option>
                          <option value="MONTHLY">Щомісяця</option>
                        </select>
                      </label>

                      <label>
                        Інтервал
                        <input
                          aria-label="Інтервал"
                          type="number"
                          min={1}
                          max={52}
                          value={editorState.form.recurrenceInterval}
                          onChange={(event) =>
                            onFormChange({ recurrenceInterval: Number(event.target.value) })
                          }
                        />
                      </label>

                      {editorState.form.recurrenceFrequency === "WEEKLY" ? (
                        <div className="schedule-weekday-picker">
                          {weekdayOptions.map((weekday) => {
                            const isActive = editorState.form.recurrenceByWeekday.includes(
                              weekday.code
                            );
                            return (
                              <button
                                key={weekday.code}
                                className={isActive ? "chip active" : "chip"}
                                type="button"
                                onClick={() =>
                                  onFormChange({
                                    // Weekday picker працює як multi-select набору RRULE BYDAY.
                                    recurrenceByWeekday: isActive
                                      ? editorState.form.recurrenceByWeekday.filter(
                                          (item) => item !== weekday.code
                                        )
                                      : [...editorState.form.recurrenceByWeekday, weekday.code]
                                  })
                                }
                              >
                                {weekday.label}
                              </button>
                            );
                          })}
                        </div>
                      ) : null}

                      <label>
                        Завершення
                        <select
                          aria-label="Завершення"
                          value={editorState.form.recurrenceEndMode}
                          onChange={(event) =>
                            onFormChange({
                              recurrenceEndMode: event.target.value as RecurrenceEndMode
                            })
                          }
                        >
                          <option value="NEVER">Без дати завершення</option>
                          <option value="UNTIL">До дати</option>
                          <option value="COUNT">За кількістю занять</option>
                        </select>
                      </label>

                      {editorState.form.recurrenceEndMode === "UNTIL" ? (
                        <label>
                          До дати
                          <input
                            aria-label="До дати"
                            type="datetime-local"
                            value={editorState.form.recurrenceUntil}
                            onChange={(event) =>
                              onFormChange({ recurrenceUntil: event.target.value })
                            }
                          />
                        </label>
                      ) : null}

                      {editorState.form.recurrenceEndMode === "COUNT" ? (
                        <label>
                          Кількість занять
                          <input
                            aria-label="Кількість занять"
                            type="number"
                            min={1}
                            max={365}
                            value={editorState.form.recurrenceCount}
                            onChange={(event) =>
                              onFormChange({ recurrenceCount: Number(event.target.value) })
                            }
                          />
                        </label>
                      ) : null}
                    </div>
                  ) : (
                    <p className="muted">
                      Увімкніть repeating only для створення серії з recurring-правилом.
                    </p>
                  )}
                </div>
              ) : null}

              {schedule?.series_id ? (
                <label>
                  {/* Scope показує API-рівень наслідків правки для recurring series. */}
                  Застосувати зміни до
                  <select
                    aria-label="Застосувати зміни до"
                    value={editorState.form.scope}
                    onChange={(event) =>
                      onFormChange({ scope: event.target.value as RecurrenceScope })
                    }
                  >
                    <option value="OCCURRENCE">Лише це заняття</option>
                    <option value="FOLLOWING">Це і всі наступні</option>
                    <option value="SERIES">Уся майбутня серія</option>
                  </select>
                </label>
              ) : null}
            </div>

            <div className="confirm-modal-actions schedule-editor-actions">
              {validationError ? (
                <p className="error-banner schedule-editor-error">{validationError}</p>
              ) : null}

              {canDelete ? (
                <button
                  className="danger-link"
                  type="button"
                  onClick={onDelete}
                  disabled={deletePending}
                >
                  {deletePending ? "Видалення..." : "Видалити"}
                </button>
              ) : null}

              <button className="ghost-link" type="button" onClick={onClose}>
                Скасувати
              </button>

              {canEdit ? (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={onSave}
                  disabled={Boolean(validationError) || createPending || updatePending}
                >
                  {createPending || updatePending
                    ? "Збереження..."
                    : editorState.mode === "create"
                      ? "Створити заняття"
                      : "Зберегти зміни"}
                </button>
              ) : (
                <p className="muted">
                  Це заняття можна переглядати, але не редагувати з цього акаунта.
                </p>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
