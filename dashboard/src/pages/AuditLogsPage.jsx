import { useState } from "react";
import { PageHeading } from "../components/common/PageHeading";
import { AuditTable } from "../components/dashboard/AuditTable";

export function AuditLogsPage({ auditLogs = [], apiKey = "" }) {
  const [outcomeFilter, setOutcomeFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredLogs = auditLogs.filter((log) => {
    const isSuccess = String(log.outcome || "").toLowerCase() === "success";
    const matchesOutcome =
      outcomeFilter === "all" ||
      (outcomeFilter === "success" && isSuccess) ||
      (outcomeFilter === "failure" && !isSuccess);

    const term = searchTerm.toLowerCase();
    const matchesSearch =
      String(log.tool || "")
        .toLowerCase()
        .includes(term) ||
      String(log.server || "")
        .toLowerCase()
        .includes(term) ||
      String(log.user || log.user_id || "")
        .toLowerCase()
        .includes(term) ||
      String(log.user_id != null ? `User #${log.user_id}` : "")
        .toLowerCase()
        .includes(term);

    return matchesOutcome && matchesSearch;
  });

  return (
    <div className="page-view animate-fade-in">
      <PageHeading
        eyebrow="OBSERVABILITY"
        title="Audit Logs"
        subtitle="Review security events, tool calls, and telemetry dispatched by your gateway."
      />

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Gateway Event Stream</h3>
            <p className="muted">
              Detailed log of executed tools and response times
            </p>
          </div>
          <span className="count-badge">
            {filteredLogs.length} events logged
          </span>
        </div>

        {/* Filter toolbar */}
        <div className="tools-filter-bar">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              className="search-input"
              placeholder="Filter by tool, server name, or user..."
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
              className={`filter-pill ${outcomeFilter === "all" ? "active" : ""}`}
              onClick={() => setOutcomeFilter("all")}
            >
              All Events ({auditLogs.length})
            </button>
            <button
              type="button"
              className={`filter-pill ${outcomeFilter === "success" ? "active" : ""}`}
              onClick={() => setOutcomeFilter("success")}
            >
              ✓ Success Only
            </button>
            <button
              type="button"
              className={`filter-pill ${outcomeFilter === "failure" ? "active" : ""}`}
              onClick={() => setOutcomeFilter("failure")}
            >
              ✗ Failures Only
            </button>
          </div>
        </div>

        <AuditTable logs={filteredLogs} />

        <div className="demo-notice" style={{ marginTop: 22 }}>
          <span className="notice-icon">📊</span>
          <span>
            {apiKey
              ? "Events are captured in real time with high-precision timestamping."
              : "Connect your gateway API key above to stream live audit events."}
          </span>
        </div>
      </section>
    </div>
  );
}

export default AuditLogsPage;
