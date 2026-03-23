import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getRevenueReport, getTrainerPopularity } from "../../../shared/api";

export function ReportsPage() {
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setMonth(date.getMonth() - 1);
    return date.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split("T")[0]);

  const revenueQuery = useQuery({
    queryKey: ["revenue", startDate, endDate],
    queryFn: () => getRevenueReport(startDate, endDate)
  });

  const trainersQuery = useQuery({
    queryKey: ["trainer-popularity"],
    queryFn: getTrainerPopularity
  });

  return (
    <main className="screen">
      <section className="card schedule-card">
        <div className="heading-group">
          <p className="eyebrow">Insights</p>
          <h1>Аналітика клубу</h1>
          <p className="muted">Тут видно виручку, динаміку оплат і найпопулярніші напрями тренувань.</p>
        </div>

        <div className="create-panel">
          <label>
            Від
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>
          <label>
            До
            <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>
        </div>

        {revenueQuery.isError ? (
          <p className="error-banner">
            {revenueQuery.error instanceof Error ? revenueQuery.error.message : "Помилка"}
          </p>
        ) : null}

        {revenueQuery.data ? (
          <div className="stats-grid">
            <article className="stat-card accent">
              <span className="stat-label">Виручка</span>
              <strong className="stat-value">
                {revenueQuery.data.currency} {revenueQuery.data.total_revenue.toLocaleString("uk-UA")}
              </strong>
            </article>
            <article className="stat-card">
              <span className="stat-label">Транзакцій</span>
              <strong className="stat-value">{revenueQuery.data.transactions_count}</strong>
            </article>
          </div>
        ) : null}

        <div className="schedule-grid">
          {trainersQuery.data?.map((trainer) => (
            <article className="schedule-item" key={trainer.trainer_id}>
              <p className="eyebrow">Coach</p>
              <h2>{trainer.name}</h2>
              <p className="muted">Відвідувань: {trainer.total_attendees}</p>
              <p className="muted">Занять: {trainer.classes_taught}</p>
              <p className="muted">Середнє: {trainer.average_attendees_per_class.toFixed(2)}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
