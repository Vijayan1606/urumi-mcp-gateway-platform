import { PageHeading } from "../components/common/PageHeading";
import { StatCard } from "../components/dashboard/StatCard";
import { ServerTable } from "../components/dashboard/ServerTable";
import { AuditTable } from "../components/dashboard/AuditTable";
import { Button } from "../components/common/Button";
import { Icon } from "../components/common/Icon";

export function OverviewPage({
  servers = [],
  tools = [],
  auditLogs = [],
  upstreamHealth = [],
  apiKey = "",
  setActivePage,
}) {
  const healthyCount = apiKey
    ? upstreamHealth.filter(
        (server) => server.enabled && server.status === "healthy",
      ).length
    : 0;

  return (
    <div className="page-view animate-fade-in">
      <PageHeading
        eyebrow="WORKSPACE OVERVIEW"
        title="Your MCP Workspace"
        subtitle="Monitor servers, registered tools, and live gateway activity in real-time."
        actions={
          <div className="heading-action-group">
            <Button
              variant="secondary"
              onClick={() => setActivePage("AI Assistant")}
              icon={<Icon name="sparkles" size={15} />}
            >
              Open AI Chat
            </Button>
            <Button
              variant="primary"
              onClick={() => setActivePage("MCP Servers")}
              icon={<Icon name="server" size={15} />}
            >
              + Manage Servers
            </Button>
          </div>
        }
      />

      <div className="stats-grid">
        <StatCard
          label="MCP Servers"
          value={servers.length}
          note="Registered upstreams"
          icon={<Icon name="server" size={18} />}
          trend={{ type: "neutral", value: `${servers.length} total` }}
        />
        <StatCard
          label="Healthy Servers"
          value={healthyCount}
          note={apiKey ? "Active and responding" : "Connect to check health"}
          icon={<Icon name="network" size={18} />}
          trend={{
            type: healthyCount > 0 ? "up" : "neutral",
            value: apiKey ? `${healthyCount}/${servers.length} live` : "Offline",
          }}
        />
        <StatCard
          label="Available Tools"
          value={tools.length}
          note={apiKey ? "Loaded from MCP servers" : "Connect to discover tools"}
          icon={<Icon name="tools" size={18} />}
          trend={{ type: "up", value: "Ready" }}
        />
        <StatCard
          label="Gateway Session"
          value={apiKey ? "Connected" : "Disconnected"}
          note={apiKey ? "Authenticated Bearer token" : "Enter API key above"}
          icon={<Icon name="key" size={18} />}
          trend={{
            type: apiKey ? "up" : "down",
            value: apiKey ? "Online" : "Pending",
          }}
        />
      </div>

      <section className="panel section-servers-preview">
        <div className="panel-heading">
          <div>
            <h3>Registered MCP Servers</h3>
            <p className="muted">Upstream services currently connected to your gateway</p>
          </div>
          <button
            type="button"
            className="text-button"
            onClick={() => setActivePage("MCP Servers")}
          >
            View all servers →
          </button>
        </div>

        <ServerTable servers={servers.slice(0, 3)} />
      </section>

      <section className="panel section-activity-preview">
        <div className="panel-heading">
          <div>
            <h3>Recent Gateway Activity</h3>
            <p className="muted">Audit trail of authenticated tool invocations</p>
          </div>
          <button
            type="button"
            className="text-button"
            onClick={() => setActivePage("Audit Logs")}
          >
            View audit logs →
          </button>
        </div>

        <AuditTable logs={auditLogs.slice(0, 3)} />

        <div className="demo-notice">
          <span className="notice-icon">ℹ</span>
          <span>
            {apiKey
              ? "Live activity streamed from your Urumi MCP gateway instance."
              : "Connect your gateway API key to stream live telemetry and audit logs."}
          </span>
        </div>
      </section>
    </div>
  );
}

export default OverviewPage;
