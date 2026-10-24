import { PageHeading } from "../components/common/PageHeading";
import { Button } from "../components/common/Button";
import { Icon } from "../components/common/Icon";

export function TeamMembersPage({
  teamMembers = [],
  teamEmail,
  setTeamEmail,
  onCreateMember,
  onRefreshMembers,
  managementLoading = false,
  managementError = "",
  managementMessage = "",
  apiKey = "",
}) {
  return (
    <div className="page-view animate-fade-in">
      <PageHeading
        eyebrow="ACCESS MANAGEMENT"
        title="Team Members"
        subtitle="Manage collaborators who have access to this MCP workspace."
      />

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Workspace Members</h3>
            <p className="muted">Authorized team accounts and role permissions</p>
          </div>
          <div className="panel-heading-actions">
            <span className="count-badge">{teamMembers.length} accounts</span>
            <Button
              variant="secondary"
              size="sm"
              disabled={!apiKey || managementLoading}
              onClick={onRefreshMembers}
              icon={<Icon name="team" size={14} />}
            >
              Refresh
            </Button>
          </div>
        </div>

        {managementError && (
          <div className="alert-banner alert-danger" role="alert">
            <span className="alert-icon">⚠</span>
            <span>{managementError}</span>
          </div>
        )}

        {managementMessage && (
          <div className="alert-banner alert-success" role="status">
            <span className="alert-icon">✓</span>
            <span>{managementMessage}</span>
          </div>
        )}

        {teamMembers.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Icon name="team" size={24} />
            </div>
            <h3>No team members loaded</h3>
            <p>
              {apiKey
                ? "Click 'Refresh' above to load workspace members."
                : "Connect your gateway API key to view and manage team members."}
            </p>
          </div>
        ) : (
          <div className="member-list">
            {teamMembers.map((member) => (
              <div className="member-row" key={member.id}>
                <div className="avatar member-avatar">
                  {(member.email || "?").charAt(0).toUpperCase()}
                </div>
                <div className="member-info">
                  <strong>{member.email}</strong>
                  <span>
                    User ID #{member.id}
                    {member.is_active === false ? " · Inactive" : " · Active"}
                  </span>
                </div>
                <span
                  className={`role-badge ${
                    member.role === "admin" ? "admin-role" : ""
                  }`}
                >
                  {member.role || "member"}
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="form-card-divider" />

        <div className="create-section">
          <h3>Add new team member</h3>
          <p className="muted" style={{ marginBottom: 14 }}>
            Invite a collaborator to access the gateway APIs.
          </p>

          <form onSubmit={onCreateMember} className="inline-add-form">
            <input
              type="email"
              className="search-input"
              placeholder="member@company.com"
              value={teamEmail}
              onChange={(e) => setTeamEmail(e.target.value)}
              required
              disabled={!apiKey || managementLoading}
            />
            <Button
              type="submit"
              variant="primary"
              loading={managementLoading}
              disabled={!apiKey || managementLoading || !teamEmail.trim()}
            >
              Add Member
            </Button>
          </form>
        </div>

        <div className="demo-notice" style={{ marginTop: 22 }}>
          <span className="notice-icon">🔒</span>
          <span>
            Workspace role assignments and authentication are verified cryptographically by the gateway.
          </span>
        </div>
      </section>
    </div>
  );
}

export default TeamMembersPage;
