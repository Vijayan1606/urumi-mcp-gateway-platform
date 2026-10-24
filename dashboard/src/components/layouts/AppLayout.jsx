import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { StatusBadge } from "../common/StatusBadge";
import { Button } from "../common/Button";

export function AppLayout({
  children,
  activePage,
  setActivePage,
  servers = [],
  connected = false,
  mobileMenuOpen,
  setMobileMenuOpen,
  gatewayProps,
}) {
  const {
    apiKey,
    keyInput,
    setKeyInput,
    connectGateway,
    loading,
    connectionStatus,
    apiError,
    onDisconnect,
  } = gatewayProps || {};

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        servers={servers}
        connected={connected}
        mobileOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />

      <main className="main-area">
        <Topbar
          activePage={activePage}
          mobileMenuOpen={mobileMenuOpen}
          setMobileMenuOpen={setMobileMenuOpen}
          connected={connected}
        />

        <div className="page-content">
          {/* Gateway connection panel */}
          <section className="panel gateway-connection-panel">
            <div className="panel-heading">
              <div className="gateway-panel-info">
                <h3>Gateway Connection</h3>
                <p className="muted">
                  Connect using your personal Urumi gateway API key to enable live MCP tool execution.
                </p>
              </div>

              <StatusBadge status={connectionStatus || (connected ? "Connected" : "Disconnected")} />
            </div>

            <form onSubmit={connectGateway} className="gateway-connect-form">
              <div className="gateway-input-wrap">
                <input
                  type="password"
                  className="search-input gateway-key-input"
                  placeholder="Paste your gateway API key (e.g. ug_live_...)"
                  value={keyInput || ""}
                  onChange={(e) => setKeyInput?.(e.target.value)}
                  autoComplete="off"
                />
              </div>

              <div className="gateway-btn-group">
                <Button
                  type="submit"
                  variant="primary"
                  loading={loading}
                  disabled={loading}
                >
                  {loading ? "Connecting..." : "Connect Gateway"}
                </Button>

                {apiKey && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={onDisconnect}
                  >
                    Disconnect
                  </Button>
                )}
              </div>
            </form>

            {apiError && (
              <div className="alert-banner alert-danger" role="alert">
                <span className="alert-icon">⚠</span>
                <span>{apiError}</span>
              </div>
            )}
          </section>

          {/* Main page content view */}
          <div className="page-view-container">{children}</div>
        </div>

        <footer className="footer">
          <div className="footer-left">
            <span>© 2026 Urumi</span>
            <span className="footer-dot">·</span>
            <span>MCP Gateway Workspace</span>
          </div>
          <div className="footer-right">
            <span>Development preview · v0.9.4</span>
          </div>
        </footer>
      </main>
    </div>
  );
}

export default AppLayout;
