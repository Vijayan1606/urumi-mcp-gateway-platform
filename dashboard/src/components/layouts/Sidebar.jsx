import { Icon } from "../common/Icon";

const NAVIGATION = [
  {
    section: "WORKSPACE",
    items: [
      { label: "Overview", icon: "grid" },
      { label: "MCP Servers", icon: "server" },
      { label: "Tools", icon: "tools" },
    ],
  },
  {
    section: "MANAGEMENT",
    items: [
      { label: "Team Members", icon: "team" },
      { label: "API Keys", icon: "key" },
      { label: "Audit Logs", icon: "activity" },
    ],
  },
  {
    section: "PLAYGROUND",
    items: [{ label: "AI Assistant", icon: "sparkles" }],
  },
];

export default function Sidebar({
  activePage,
  setActivePage,
  servers = [],
  connected = false,
  mobileOpen = false,
  onClose,
}) {
  return (
    <>
      {mobileOpen && (
        <button
          className="sidebar-overlay"
          aria-label="Close navigation"
          onClick={onClose}
        />
      )}

      <aside
        className={`sidebar ${mobileOpen ? "sidebar-mobile-open" : ""}`}
        aria-label="Main navigation"
      >
        <div className="brand">
          <div className="brand-mark">U</div>

          <div>
            <strong>urumi</strong>
            <span>MCP GATEWAY</span>
          </div>

          <button
            type="button"
            className="sidebar-close"
            aria-label="Close navigation"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="workspace-switcher">
          <div className="workspace-icon">U</div>

          <div>
            <strong>Urumi Workspace</strong>
            <span>Local environment</span>
          </div>

          <span className="workspace-arrow">⌄</span>
        </div>

        <nav className="sidebar-navigation">
          {NAVIGATION.map((group) => (
            <div className="nav-group" key={group.section}>
              <p className="nav-label">{group.section}</p>

              {group.items.map((item) => (
                <button
                  type="button"
                  key={item.label}
                  className={`nav-item ${
                    activePage === item.label ? "active" : ""
                  }`}
                  aria-current={
                    activePage === item.label ? "page" : undefined
                  }
                  onClick={() => {
                    setActivePage(item.label);
                    onClose?.();
                  }}
                >
                  <span className="nav-icon">
                    <Icon name={item.icon} size={18} />
                  </span>

                  <span className="nav-item-label">{item.label}</span>

                  {item.label === "MCP Servers" && (
                    <span className="nav-count">{servers.length}</span>
                  )}

                  {activePage === item.label && (
                    <span className="nav-active-indicator" />
                  )}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <span
              className={`status-dot ${
                connected ? "dot-connected" : "dot-disconnected"
              }`}
            />

            <div>
              <strong>
                {connected ? "Gateway connected" : "Gateway disconnected"}
              </strong>

              <span>
                {connected ? "Live gateway data" : "Connect to load live data"}
              </span>
            </div>
          </div>

          <div className="profile">
            <div className="avatar">A</div>

            <div className="profile-info">
              <strong>Workspace Admin</strong>
              <span>Administrator</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
