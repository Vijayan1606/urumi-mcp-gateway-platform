import { Icon } from "../common/Icon";
import { StatusBadge } from "../common/StatusBadge";

export function ServerTable({ servers = [], onToggle }) {
  if (!servers.length) {
    return (
      <div className="empty-state">
        <div className="empty-icon">
          <Icon name="server" size={24} />
        </div>
        <h3>No MCP servers found</h3>
        <p>No upstream servers are registered in this workspace.</p>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>SERVER</th>
            <th>STATE</th>
            <th>TOOLS</th>
            <th>TYPE</th>
            {onToggle && <th>ACTION</th>}
          </tr>
        </thead>
        <tbody>
          {servers.map((server) => (
            <tr key={server.name} className="table-row-interactive">
              <td>
                <div className="table-server">
                  <div className="small-server-icon">
                    <Icon name="server" size={17} />
                  </div>
                  <div>
                    <strong>{server.name}</strong>
                    <span>{server.description}</span>
                  </div>
                </div>
              </td>
              <td>
                <StatusBadge status={server.status} />
              </td>
              <td>
                <span className="count-pill">{server.tools}</span>
              </td>
              <td>
                <span className="server-tag">Streamable HTTP</span>
              </td>
              {onToggle && (
                <td>
                  <button
                    type="button"
                    className="secondary-button btn-sm"
                    onClick={() => onToggle(server.name)}
                  >
                    {server.enabled ? "Disable" : "Enable"}
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ServerTable;
