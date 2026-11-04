import { useState } from "react";

const formatDay = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });

const plural = (count) => `${count} submission${count === 1 ? "" : "s"}`;

/** Submissions per day: one series, so one hue, a hover/focus tooltip, and a table for screen readers. */
export default function ActivityChart({ days }) {
  const [active, setActive] = useState(null);
  const max = Math.max(1, ...days.map((day) => day.submissions));
  const total = days.reduce((sum, day) => sum + day.submissions, 0);
  const current = active === null ? null : days[active];

  return (
    <figure className="activity">
      <figcaption className="activity-caption">
        <span>{plural(total)} in the last {days.length} days</span>
        <span className="muted small" aria-live="polite">
          {current ? `${formatDay(current.date)}: ${plural(current.submissions)}` : "Hover a bar for details"}
        </span>
      </figcaption>
      <div className="activity-plot" aria-hidden="true">
        <span className="activity-max">{max}</span>
        {days.map((day, index) => (
          <div
            key={day.date}
            className={`activity-slot ${index === active ? "active" : ""}`}
            onMouseEnter={() => setActive(index)}
            onMouseLeave={() => setActive(null)}
          >
            {day.submissions > 0 ? (
              <div className="activity-bar" style={{ height: `${(day.submissions / max) * 100}%` }} />
            ) : (
              <div className="activity-empty" />
            )}
          </div>
        ))}
      </div>
      <div className="activity-axis muted small" aria-hidden="true">
        <span>{formatDay(days[0].date)}</span>
        <span>Today</span>
      </div>
      <table className="sr-only">
        <caption>Submissions per day</caption>
        <thead>
          <tr>
            <th>Day</th>
            <th>Submissions</th>
          </tr>
        </thead>
        <tbody>
          {days.map((day) => (
            <tr key={day.date}>
              <td>{formatDay(day.date)}</td>
              <td>{day.submissions}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
