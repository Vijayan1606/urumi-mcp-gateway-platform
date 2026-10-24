# Threat Model — Urumi MCP Gateway Platform

## 1. Purpose

This document identifies security risks associated with a team MCP gateway that exposes tools from multiple upstream servers to authenticated users.

It describes the intended security boundaries, potential threats, mitigations, and tests needed to verify those mitigations.

## 2. Assets to Protect

- Team members' API keys.
- Upstream MCP server credentials.
- WooCommerce products, orders, and customer information.
- Inventory and customer-support data.
- User identities, roles, and permissions.
- Audit logs.
- Kubernetes Secrets and persistent application data.
- The integrity of tool execution and AI-generated tool requests.

## 3. Trust Boundaries

The main trust boundaries are:

1. External MCP clients and browsers communicating with the gateway.
2. Authenticated users with different roles.
3. The gateway and its upstream MCP servers.
4. MCP servers and the WordPress/WooCommerce backend.
5. Kubernetes workloads and cluster administration.
6. The AI model and tool descriptions supplied by upstream servers.

The gateway should be the controlled access point for clients. Upstream MCP servers should not be exposed publicly unless there is an explicitly justified requirement.

## 4. Shared Upstream Credentials

### Threat

An upstream server may use a shared credential that allows access to products, orders, inventory, or other data. A team member might be able to invoke tools that use that credential even though the member cannot see the credential itself.

### Mitigations

- Keep upstream credentials on the server side.
- Do not return upstream credentials in API responses or tool results.
- Limit tool access according to user role and business requirements.
- Validate tool inputs and enforce authorization before executing sensitive operations.
- Use least-privilege upstream credentials where supported.
- Store secrets in Kubernetes Secrets or an equivalent secret manager.
- Avoid recording credentials in logs.

### Verification

Inspect API responses, browser network requests, logs, and external-client results to confirm that upstream credentials are not exposed.

## 5. Client API-Key Handling

### Threat

A leaked or stolen gateway API key could allow another person to make requests as the associated user.

### Mitigations

- Associate each API key with a specific user.
- Store keys as hashes where required by the implementation.
- Support immediate revocation.
- Reject invalid, expired, or revoked keys.
- Avoid displaying stored key material after initial issuance.
- Never include keys in logs, source control, or screenshots.

### Verification

Test valid-key authentication, invalid-key rejection, and revocation. Confirm that a request using a revoked key is rejected.

## 6. Untrusted Upstream MCP Servers

### Threat

An upstream MCP server may return misleading tool descriptions or malicious content intended to manipulate the AI model. Tool output could attempt to persuade the model to disclose information or perform unintended actions.

### Mitigations

- Treat tool descriptions and tool results as untrusted input.
- Do not treat instructions returned by a tool as trusted system instructions.
- Validate tool arguments and enforce authorization independently of the model.
- Require explicit user confirmation for consequential actions when appropriate.
- Restrict the network access available to upstream servers.
- Validate and restrict upstream URLs to reduce server-side request forgery risks.
- Apply timeouts and isolate failures from unhealthy upstream servers.

### Verification

Review URL validation, authorization checks, timeout handling, and the chat agent's treatment of tool output. Do not claim protections are implemented unless the code and tests support that claim.

## 7. Risks Between Team Members

### Threats

- A member attempts to use an administrator-only function.
- A member attempts to use another person's API key.
- A user attempts to access another user's records.
- A revoked user continues attempting requests.
- A user attempts to perform a sensitive write operation through a tool.

### Mitigations

- Enforce role and ownership checks on the server.
- Verify authorization for each sensitive operation.
- Associate audit events with the authenticated user.
- Reject revoked keys.
- Avoid relying solely on frontend controls to enforce authorization.

### Verification

Test administrator and member accounts separately. Attempt unauthorized actions through direct API requests, not only through the dashboard.

## 8. Audit Logging

Audit logs should capture the user, upstream server, tool, timestamp, duration, and outcome of each tool call.

Logs should not expose API keys, passwords, upstream credentials, or unnecessary customer information.

Verify that successful and failed calls are recorded and attributed to the correct user.

## 9. Kubernetes and Deployment Security

Potential risks include accidental secret exposure, unnecessary public service exposure, excessive container privileges, and loss of persistent data.

Recommended controls include:

- Kubernetes Secrets or an appropriate external secret manager.
- Internal-only Services for upstream MCP servers.
- Ingress rules that expose only intended endpoints.
- Resource requests and limits.
- Readiness and liveness probes.
- Non-root containers and least-privilege RBAC where supported.
- NetworkPolicies where supported by the cluster networking configuration.
- Secure backup and recovery procedures for persistent data.

These controls must be verified against the actual manifests and running cluster.

## 10. Residual Risks and Limitations

A gateway API key does not by itself guarantee that every tool invocation is safe. The gateway must also enforce authorization, validate inputs, and handle untrusted tool output.

Kubernetes Secrets provide a mechanism for distributing sensitive configuration, but access to those Secrets must still be restricted.

An upstream service may return incorrect data, be compromised, or become unavailable. Timeouts and failure isolation reduce operational impact but do not eliminate all security risks.

## 11. Security Test Checklist

- [ ] Invalid API keys are rejected.
- [ ] Revoked API keys are rejected.
- [ ] Members cannot perform unauthorized administrative operations.
- [ ] Upstream credentials are not exposed to clients.
- [ ] Sensitive data is not written to logs.
- [ ] Internal MCP servers are not directly exposed publicly.
- [ ] Untrusted upstream URLs are appropriately validated.
- [ ] Slow or failed upstream calls have bounded timeouts.
- [ ] A failed upstream does not unnecessarily interrupt healthy upstreams.
- [ ] Audit records correctly identify the requesting user.
- [ ] Kubernetes permissions and Secret access are appropriately restricted.

## 12. Scope

This document is a threat-model baseline, not a certification that every listed mitigation is implemented. Mark each control as verified only after inspecting the implementation and completing the relevant test.
