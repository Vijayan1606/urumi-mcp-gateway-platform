import { Icon } from "../common/Icon";

export function AuditTable({ logs = [] }) {
  if (!logs.length) {
    return (
      <div className="empty-state">
        <div className="empty-icon">
          <Icon name="activity" size={24} />
        </div>
        <h3>No audit events recorded</h3>
        <p>Tool calls, authentication attempts, and errors will appear here.</p>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>USER</th>
            <th>SERVER / TOOL</th>
            <th>OUTCOME</th>
            <th>DURATION</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => {
            const isSuccess = String(log.outcome || "").toLowerCase() === "success";
            return (
              <tr key={log.id} className="table-row-interactive">
                <td>
                  <div className="table-user-cell">
                    <span className="user-dot" />
                    <span>{log.user || "anonymous"}</span>
                  </div>
                </td>
                <td>
                  <div className="audit-tool">
                    <strong>{log.tool}</strong>
                    <span>{log.server}</span>
                  </div>
                </td>
                <td>
                  <span className={`outcome ${isSuccess ? "success" : "failure"}`}>
                    <span className="outcome-icon">{isSuccess ? "✓" : "✗"}</span>
                    {log.outcome}
                  </span>
                </td>
                <td>
                  <span className="duration-tag">{log.duration || "—"}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default AuditTable;
