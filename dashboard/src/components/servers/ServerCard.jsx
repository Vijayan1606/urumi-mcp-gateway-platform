import { Icon } from "../common/Icon";
import { StatusBadge } from "../common/StatusBadge";

export function ServerCard({ server, onToggle }) {
  const isEnabled = Boolean(server.enabled);

  return (
    <article className={`server-card ${isEnabled ? "server-card-active" : "server-card-disabled"}`}>
      <div className="server-card-top">
        <div className="server-icon">
          <Icon name="server" size={21} />
        </div>
        <StatusBadge status={server.status} />
      </div>

      <div className="server-card-body">
        <h3>{server.name}</h3>
        <p className="muted">{server.description}</p>
      </div>

      <div className="server-card-footer">
        <div className="server-tools-stat">
          <span className="count-badge">{server.tools} tools</span>
          <span className="server-type-pill">Streamable HTTP</span>
        </div>

        <button
          type="button"
          className={`toggle-switch-btn ${isEnabled ? "active" : ""}`}
          onClick={() => onToggle?.(server.name)}
          title={isEnabled ? "Click to disable server" : "Click to enable server"}
          aria-pressed={isEnabled}
        >
          <span className="toggle-switch-track">
            <span className="toggle-switch-thumb" />
          </span>
          <span className="toggle-label">{isEnabled ? "Enabled" : "Disabled"}</span>
        </button>
      </div>
    </article>
  );
}

export default ServerCard;
