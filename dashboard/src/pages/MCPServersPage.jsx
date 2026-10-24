import { useState } from "react";
import { PageHeading } from "../components/common/PageHeading";
import { ServerCard } from "../components/servers/ServerCard";
import { Icon } from "../components/common/Icon";

export function MCPServersPage({
  servers = [],
  onToggleServer,
  apiKey = "",
}) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredServers = servers.filter((server) => {
    const term = searchTerm.toLowerCase();
    return (
      String(server.name || "").toLowerCase().includes(term) ||
      String(server.description || "").toLowerCase().includes(term)
    );
  });

  return (
    <div className="page-view animate-fade-in">
      <PageHeading
        eyebrow="INTEGRATIONS"
        title="MCP Servers"
        subtitle="View and manage connected Model Context Protocol upstreams."
      />

      <div className="toolbar">
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            className="search-input"
            placeholder="Search servers by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button
              type="button"
              className="search-clear-btn"
              onClick={() => setSearchTerm("")}
            >
              ✕
            </button>
          )}
        </div>

        <span className="results-badge">
          {filteredServers.length} of {servers.length} servers
        </span>
      </div>

      {filteredServers.length === 0 ? (
        <div className="empty-state panel">
          <div className="empty-icon">
            <Icon name="server" size={24} />
          </div>
          <h3>No matching servers</h3>
          <p>No MCP servers match &quot;{searchTerm}&quot;. Try a different search term.</p>
        </div>
      ) : (
        <div className="server-cards">
          {filteredServers.map((server) => (
            <ServerCard
              key={server.name}
              server={server}
              onToggle={onToggleServer}
            />
          ))}
        </div>
      )}

      <div className="demo-notice" style={{ marginTop: 24 }}>
        <span className="notice-icon">⚡</span>
        <span>
          {apiKey
            ? "Server state changes immediately propagate to the Urumi gateway router."
            : "Connect to the gateway above to manage upstream MCP connections in real time."}
        </span>
      </div>
    </div>
  );
}

export default MCPServersPage;
