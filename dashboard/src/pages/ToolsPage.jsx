import { useState } from "react";
import { PageHeading } from "../components/common/PageHeading";
import { Icon } from "../components/common/Icon";

export function ToolsPage({ tools = [], apiKey = "" }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedServer, setSelectedServer] = useState("all");

  const serverNames = {
    woocommerce: "WooCommerce",
    inventory: "Inventory",
    customer_support: "Customer Support",
  };

  // Get unique servers
  const availableServers = Array.from(
    new Set(tools.map((t) => t.server).filter(Boolean)),
  );

  const filteredTools = tools.filter((tool) => {
    const matchesSearch =
      String(tool.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(tool.description || "").toLowerCase().includes(searchTerm.toLowerCase());

    const matchesServer =
      selectedServer === "all" || tool.server === selectedServer;

    return matchesSearch && matchesServer;
  });

  return (
    <div className="page-view animate-fade-in">
      <PageHeading
        eyebrow="DISCOVERY"
        title="Available Tools"
        subtitle="Tools automatically discovered and exposed by your registered MCP servers."
      />

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Registered MCP Tools</h3>
            <p className="muted">Functions executable by the AI assistant and API clients</p>
          </div>
          <span className="count-badge">{filteredTools.length} tools available</span>
        </div>

        {/* Filter bar */}
        <div className="tools-filter-bar">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              className="search-input"
              placeholder="Filter tools by function name or description..."
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

          <div className="filter-pill-group">
            <button
              type="button"
              className={`filter-pill ${selectedServer === "all" ? "active" : ""}`}
              onClick={() => setSelectedServer("all")}
            >
              All ({tools.length})
            </button>
            {availableServers.map((serverKey) => (
              <button
                type="button"
                key={serverKey}
                className={`filter-pill ${selectedServer === serverKey ? "active" : ""}`}
                onClick={() => setSelectedServer(serverKey)}
              >
                {serverNames[serverKey] || serverKey}
              </button>
            ))}
          </div>
        </div>

        {filteredTools.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Icon name="tools" size={24} />
            </div>
            <h3>No tools found</h3>
            <p>
              {apiKey
                ? "No registered tools matched your criteria."
                : "Connect your gateway API key to discover live MCP tools from your upstreams."}
            </p>
          </div>
        ) : (
          <div className="tool-list">
            {filteredTools.map((tool) => (
              <div
                className="tool-row tool-row-card"
                key={`${tool.server}-${tool.name}`}
              >
                <div className="tool-icon">
                  <Icon name="tools" size={18} />
                </div>

                <div className="tool-details">
                  <div className="tool-name-row">
                    <strong className="tool-name-code">{tool.name}</strong>
                    <span className="server-tag">
                      {serverNames[tool.server] || tool.server || "mcp"}
                    </span>
                  </div>
                  <span className="tool-desc">{tool.description || "No description provided."}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="demo-notice" style={{ marginTop: 20 }}>
          <span className="notice-icon">ℹ</span>
          <span>
            {apiKey
              ? "Tools are dynamically registered into Gemini AI function-calling schemas."
              : "Connect your gateway API key above to load live tools."}
          </span>
        </div>
      </section>
    </div>
  );
}

export default ToolsPage;
