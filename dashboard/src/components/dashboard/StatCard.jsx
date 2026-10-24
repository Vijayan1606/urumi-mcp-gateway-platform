export function StatCard({ label, value, note, icon, trend = null, className = "" }) {
  return (
    <article className={`stat-card ${className}`}>
      <div className="stat-top">
        <span className="stat-label">{label}</span>
        {icon && <span className="stat-icon">{icon}</span>}
      </div>
      <div className="stat-main">
        <strong className="stat-value">{value}</strong>
        {trend && (
          <span className={`stat-trend stat-trend-${trend.type || "up"}`}>
            {trend.value}
          </span>
        )}
      </div>
      {note && <span className="stat-note">{note}</span>}
    </article>
  );
}

export default StatCard;
