export function StatusBadge({ status, className = "" }) {
  const norm = String(status || "").toLowerCase();

  let variant = "disabled";
  if (["connected", "healthy", "active", "enabled", "success"].includes(norm)) {
    variant = "connected";
  } else if (["unreachable", "failure", "revoked", "error"].includes(norm)) {
    variant = "danger";
  } else if (["degraded", "not checked", "unknown", "pending"].includes(norm)) {
    variant = "warning";
  }

  return (
    <span className={`status-badge status-${variant} ${className}`}>
      <span className={`status-dot status-dot-${variant}`} />
      <span className="status-text">{status || "Unknown"}</span>
    </span>
  );
}

export default StatusBadge;
