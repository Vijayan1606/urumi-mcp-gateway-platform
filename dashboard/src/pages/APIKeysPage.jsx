import { useState } from "react";
import { PageHeading } from "../components/common/PageHeading";
import { Button } from "../components/common/Button";
import { StatusBadge } from "../components/common/StatusBadge";
import { Icon } from "../components/common/Icon";

export function APIKeysPage({
  managedKeys = [],
  teamMembers = [],
  newKeyName,
  setNewKeyName,
  newKeyUserId,
  setNewKeyUserId,
  newlyCreatedKey,
  onCreateApiKey,
  onRevokeApiKey,
  onRefreshKeys,
  managementLoading = false,
  managementError = "",
  managementMessage = "",
  apiKey = "",
}) {
  const [copiedKey, setCopiedKey] = useState(false);

  const handleCopyNewKey = async () => {
    try {
      await navigator.clipboard.writeText(newlyCreatedKey);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2500);
    } catch {
      // fallback
    }
  };

  return (
    <div className="page-view animate-fade-in">
      <PageHeading
        eyebrow="SECURITY"
        title="API Keys"
        subtitle="Manage credentials used to authenticate with your gateway instance."
      />

      <section className="panel">
        <div className="security-callout">
          <span className="callout-icon">🛡</span>
          <div>
            <strong>Keep your API keys confidential</strong>
            <p>
              Newly generated keys are displayed only once. Anyone with this key can execute tools
              configured on your MCP upstreams.
            </p>
          </div>
        </div>

        {managementError && (
          <div className="alert-banner alert-danger" role="alert" style={{ marginTop: 16 }}>
            <span className="alert-icon">⚠</span>
            <span>{managementError}</span>
          </div>
        )}

        {managementMessage && (
          <div className="alert-banner alert-success" role="status" style={{ marginTop: 16 }}>
            <span className="alert-icon">✓</span>
            <span>{managementMessage}</span>
          </div>
        )}

        {/* Secret Key Reveal Alert */}
        {newlyCreatedKey && (
          <div className="panel newly-created-key-box animate-slide-down" style={{ marginTop: 20 }}>
            <div className="key-reveal-header">
              <span className="key-badge">NEW SECRET GENERATED</span>
              <span className="key-warning">Save this secret key now. It will not be shown again.</span>
            </div>
            <div className="key-input-copy-group">
              <input
                className="search-input key-display-input"
                type="text"
                readOnly
                value={newlyCreatedKey}
                onFocus={(e) => e.target.select()}
                aria-label="Newly created API key"
              />
              <Button
                variant="primary"
                onClick={handleCopyNewKey}
                icon={<Icon name="key" size={14} />}
              >
                {copiedKey ? "✓ Copied!" : "Copy Key"}
              </Button>
            </div>
          </div>
        )}

        {/* Create Key Form */}
        <div className="create-section" style={{ marginTop: 24 }}>
          <h3>Generate new API key</h3>
          <p className="muted" style={{ marginBottom: 14 }}>
            Create an access credential for an external client or agent.
          </p>

          <form onSubmit={onCreateApiKey} className="inline-add-form">
            <input
              className="search-input"
              type="text"
              placeholder="e.g. Cursor IDE, Claude Desktop, Production Gateway"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              required
              disabled={!apiKey || managementLoading}
            />

            {teamMembers.length > 0 && (
              <select
                className="search-input"
                value={newKeyUserId}
                onChange={(e) => setNewKeyUserId(e.target.value)}
                aria-label="API key owner"
                disabled={!apiKey || managementLoading}
              >
                <option value="">My Account (Self)</option>
                {teamMembers.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.email} (ID #{member.id})
                  </option>
                ))}
              </select>
            )}

            <Button
              type="submit"
              variant="primary"
              loading={managementLoading}
              disabled={!apiKey || managementLoading || !newKeyName.trim()}
            >
              Generate Key
            </Button>
          </form>
        </div>

        <div className="form-card-divider" />

        {/* Existing Keys Table */}
        <div className="panel-heading" style={{ marginTop: 24 }}>
          <div>
            <h3>Active Credentials</h3>
            <p className="muted">All issued tokens with access privileges</p>
          </div>
          <div className="panel-heading-actions">
            <span className="count-badge">{managedKeys.length} keys</span>
            <Button
              variant="secondary"
              size="sm"
              disabled={!apiKey || managementLoading}
              onClick={onRefreshKeys}
              icon={<Icon name="key" size={14} />}
            >
              Refresh
            </Button>
          </div>
        </div>

        {!apiKey ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Icon name="key" size={24} />
            </div>
            <h3>Gateway disconnected</h3>
            <p>Connect your gateway API key above to inspect and manage credentials.</p>
          </div>
        ) : managedKeys.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Icon name="key" size={24} />
            </div>
            <h3>No API keys found</h3>
            <p>Generate your first API key using the form above.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>NAME</th>
                  <th>PREFIX</th>
                  <th>OWNER ID</th>
                  <th>STATUS</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {managedKeys.map((key) => (
                  <tr key={key.id} className="table-row-interactive">
                    <td>
                      <div className="table-key-name">
                        <Icon name="key" size={15} />
                        <strong>{key.name || "Unnamed Key"}</strong>
                      </div>
                    </td>
                    <td>
                      <code className="key-prefix-code">
                        {key.key_prefix || "••••"}••••
                      </code>
                    </td>
                    <td>
                      <span className="user-id-pill">
                        User #{key.user_id || "Self"}
                      </span>
                    </td>
                    <td>
                      <StatusBadge
                        status={key.is_active ? "Active" : "Revoked"}
                      />
                    </td>
                    <td>
                      {key.is_active ? (
                        <button
                          type="button"
                          className="danger-button btn-sm"
                          disabled={managementLoading}
                          onClick={() => onRevokeApiKey(key.id)}
                        >
                          Revoke
                        </button>
                      ) : (
                        <span className="muted-text">Revoked</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default APIKeysPage;
