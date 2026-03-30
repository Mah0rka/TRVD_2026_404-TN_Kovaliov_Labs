// Показує тренеру або менеджменту актуальні заняття та їх історію.

import { useEffect, useMemo, useState } from "react";
import { hasSessionEnded } from "../../../shared/lib/sessionTime";
import { useAuthStore } from "../../auth";
import { useClassesPageData } from "../hooks/useClassesPageData";

function formatSessionPeriod(startTime: string, endTime: string): string {
  return `${new Date(startTime).toLocaleString("uk-UA")} - ${new Date(endTime).toLocaleString("uk-UA")}`;
}

// Сторінка поєднує три режими: активні заняття, очікування підтвердження і історію.
// Один компонент тут виправданий, бо всі режими працюють над тим самим dataset.
export function MyClassesPage() {
  const user = useAuthStore((state) => state.user);
  const isManagement = user?.role === "ADMIN" || user?.role === "OWNER";
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);
  const [view, setView] = useState<"ACTIVE" | "PENDING" | "HISTORY">("ACTIVE");
  const [completionComment, setCompletionComment] = useState("");

  const { classesQuery, attendeesQuery, completeMutation } = useClassesPageData({
    isManagement,
    selectedClassId
  });

  const visibleClasses = useMemo(() => {
    const classes = classesQuery.data ?? [];
    // Один і той самий набір занять розкладаємо на активні, очікувані та історичні списки.
    const activeClasses = classes
      .filter((item) => !hasSessionEnded(item.end_time))
      .sort((left, right) => +new Date(left.start_time) - +new Date(right.start_time));
    const pendingClasses = classes
      .filter((item) => hasSessionEnded(item.end_time) && !item.completed_at)
      .sort((left, right) => +new Date(right.end_time) - +new Date(left.end_time));
    const historyClasses = classes
      .filter((item) => hasSessionEnded(item.end_time) && (!isManagement || Boolean(item.completed_at)))
      .sort((left, right) => +new Date(right.end_time) - +new Date(left.end_time));

    if (view === "ACTIVE") {
      return activeClasses;
    }

    if (view === "PENDING") {
      return pendingClasses;
    }

    return historyClasses;
  }, [classesQuery.data, isManagement, view]);

  useEffect(() => {
    // Тримаємо вибір синхронним із поточним табом, щоб права панель не лишалась порожньою.
    if (!visibleClasses.length) {
      setSelectedClassId(null);
      return;
    }

    if (!selectedClassId || !visibleClasses.some((item) => item.id === selectedClassId)) {
      setSelectedClassId(visibleClasses[0].id);
    }
  }, [selectedClassId, visibleClasses]);

  const selectedClass = useMemo(
    () => visibleClasses.find((item) => item.id === selectedClassId) ?? null,
    [selectedClassId, visibleClasses]
  );

  useEffect(() => {
    // Коли змінюється вибране заняття, textarea має показувати актуальний коментар,
    // а не залишок від попередньо відкритого класу.
    setCompletionComment(selectedClass?.completion_comment ?? "");
  }, [selectedClass?.completion_comment, selectedClass?.id]);

  // Завершення можна підтверджувати лише після фактичного закінчення заняття.
  const canConfirmCompletion =
    Boolean(selectedClass) &&
    Boolean(user) &&
    hasSessionEnded(selectedClass!.end_time) &&
    (isManagement || selectedClass?.trainer_id === user?.id);

  const headingTitle = isManagement ? "Заняття клубу та історія" : "Мої заняття та учасники";
  const headingText = isManagement
    ? "Тут видно актуальні заняття клубу, історію завершених сесій та службові коментарі."
    : "Тут зібрані ваші актуальні заняття, історія завершених класів і список учасників.";

  return (
    <section className="panel-stack classes-page">
      <div className="panel-heading">
        <h2>{headingTitle}</h2>
        <p className="muted">{headingText}</p>
      </div>

      <div className="chips classes-tabs">
        <button
          className={view === "ACTIVE" ? "chip active" : "chip"}
          onClick={() => setView("ACTIVE")}
        >
          Актуальні
        </button>
        {isManagement ? (
          <button
            className={view === "PENDING" ? "chip active" : "chip"}
            onClick={() => setView("PENDING")}
          >
            Очікує підтвердження
          </button>
        ) : null}
        <button
          className={view === "HISTORY" ? "chip active" : "chip"}
          onClick={() => setView("HISTORY")}
        >
          Історія
        </button>
      </div>

      <div className="dual-grid classes-layout">
        <div className="surface-card classes-list-panel">
          <h3>
            {view === "ACTIVE"
              ? "Список занять"
              : view === "PENDING"
                ? "Заняття без підтвердження"
                : "Історія занять"}
          </h3>
          {classesQuery.isLoading ? <p className="muted">Завантаження занять...</p> : null}
          {classesQuery.isError ? (
            <p className="error-banner">
              {classesQuery.error instanceof Error ? classesQuery.error.message : "Помилка"}
            </p>
          ) : null}
          {visibleClasses.length ? (
            <div className="table-grid classes-list-grid">
              {visibleClasses.map((item) => {
                const confirmedCount = item.bookings.filter((booking) => booking.status === "CONFIRMED").length;
                const isCompleted = Boolean(item.completed_at);

                return (
                  <button
                    key={item.id}
                    className={selectedClassId === item.id ? "class-card classes-card active" : "class-card classes-card"}
                    onClick={() => setSelectedClassId(item.id)}
                  >
                    <strong>{item.title}</strong>
                    <span>{formatSessionPeriod(item.start_time, item.end_time)}</span>
                    {isManagement ? (
                      <span>
                        Тренер: {item.trainer.first_name} {item.trainer.last_name}
                      </span>
                    ) : null}
                    <span>
                      {confirmedCount}/{item.capacity} підтверджено
                    </span>
                    {view !== "ACTIVE" ? (
                      <span className={isCompleted ? "status-pill success" : "status-pill warning"}>
                        {isCompleted ? "Підтверджено" : "Очікує підтвердження"}
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="muted">
              {view === "ACTIVE"
                ? isManagement
                  ? "У клубі немає активних занять у цьому списку."
                  : "У вас зараз немає актуальних занять."
                : view === "PENDING"
                  ? "Усі завершені заняття вже підтверджені."
                  : "Історія занять поки порожня."}
            </p>
          )}
        </div>

        <div className="surface-card classes-detail-panel">
          {/* Права панель завжди працює від selectedClass: або показує учасників
              активного заняття, або підсумок/коментар для завершеного. */}
          <h3>{view === "ACTIVE" ? "Учасники заняття" : "Підсумок заняття"}</h3>
          {selectedClass ? (
            <div className="classes-detail-meta">
              <p className="muted">
                {selectedClass.title} · {formatSessionPeriod(selectedClass.start_time, selectedClass.end_time)}
              </p>
              <p className="muted">
                Тренер: {selectedClass.trainer.first_name} {selectedClass.trainer.last_name}
              </p>
            </div>
          ) : (
            <p className="muted">Оберіть заняття зліва, щоб побачити деталі.</p>
          )}

          {completeMutation.isError ? (
            <p className="error-banner">
              {completeMutation.error instanceof Error ? completeMutation.error.message : "Не вдалося підтвердити завершення заняття."}
            </p>
          ) : null}

          {selectedClass && view !== "ACTIVE" ? (
            <div className="panel-stack">
              <div className="surface-card detail-panel classes-summary-card">
                <p className="eyebrow">
                  {selectedClass.completed_at ? "Завершення підтверджено" : "Потрібне підтвердження"}
                </p>
                <h3>{selectedClass.completed_at ? "Підсумок збережено" : "Підтвердіть завершення заняття"}</h3>
                <p className="muted">
                  {selectedClass.completed_at
                    ? `Підтвердив(ла): ${selectedClass.completed_by?.first_name ?? ""} ${selectedClass.completed_by?.last_name ?? ""} · ${new Date(selectedClass.completed_at).toLocaleString("uk-UA")}`
                    : "Після завершення заняття тренер або відповідальний має зафіксувати факт проведення й залишити коментар."}
                </p>
                {selectedClass.completion_comment ? (
                  <p>{selectedClass.completion_comment}</p>
                ) : (
                  <p className="muted">Коментар ще не додано.</p>
                )}
              </div>

              {canConfirmCompletion ? (
                <div className="create-panel-field classes-completion-form">
                  <label htmlFor="completion-comment">Коментар після заняття</label>
                  <textarea
                    id="completion-comment"
                    rows={4}
                    value={completionComment}
                    onChange={(event) => setCompletionComment(event.target.value)}
                    placeholder="Наприклад: група відпрацювала програму повністю, були зауваження до техніки, клієнт запізнився тощо."
                  />
                  <div className="classes-completion-actions">
                    <button
                      className="secondary-button"
                      onClick={() =>
                        completeMutation.mutate({
                          classId: selectedClass.id,
                          comment: completionComment
                        })
                      }
                      disabled={completeMutation.isPending}
                    >
                      {completeMutation.isPending
                        ? "Збереження..."
                        : selectedClass.completed_at
                          ? "Оновити коментар"
                          : "Підтвердити завершення"}
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {attendeesQuery.isLoading ? <p className="muted">Завантаження учасників...</p> : null}
          {attendeesQuery.isError ? (
            <p className="error-banner">
              {attendeesQuery.error instanceof Error ? attendeesQuery.error.message : "Помилка"}
            </p>
          ) : null}

          <div className="table-grid classes-attendees-grid">
            {attendeesQuery.data?.map((attendee) => (
              <article key={attendee.id} className="table-row classes-attendee-row">
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
