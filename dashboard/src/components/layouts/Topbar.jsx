export function Topbar({
  activePage,
  mobileMenuOpen,
  setMobileMenuOpen,
  connected = false,
  onHelpClick,
}) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className={`mobile-menu-button ${mobileMenuOpen ? "active" : ""}`}
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>

        <div className="breadcrumbs">
          <span className="breadcrumb-root">Workspace</span>
          <span className="breadcrumb-separator">/</span>
          <strong className="breadcrumb-current">{activePage}</strong>
        </div>
      </div>

      <div className="topbar-actions">
        <div className="environment-badge">
          <span
            className={`status-dot ${connected ? "dot-connected" : "dot-disconnected"}`}
          />
          <span>{connected ? "Gateway Live" : "Development"}</span>
        </div>

        <button
          type="button"
          className="help-button"
          title="Urumi Help & Information"
          onClick={
            onHelpClick ||
            (() =>
              window.alert(
                "Urumi MCP Gateway Workspace\n\nMonitor servers, tools, API keys, and interact with the AI Assistant using MCP tools.",
              ))
          }
        >
          ?
        </button>

        <div className="avatar top-avatar" title="Workspace Administrator">
          A
        </div>
      </div>
    </header>
  );
}

export default Topbar;
