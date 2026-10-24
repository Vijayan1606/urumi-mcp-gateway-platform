\# System Design and Tradeoffs



\## 1. Overview



Urumi MCP Gateway Platform provides a single authenticated MCP endpoint for accessing multiple upstream MCP servers. It combines a WooCommerce store, a custom WooCommerce MCP server, inventory and customer-support MCP servers, a gateway backend, a React dashboard, and an AI chat interface.



The platform is deployed on Kubernetes, with Helm charts supporting environment-specific configuration.



\## 2. Architecture



\### Components



\* \*\*WordPress and WooCommerce:\*\* Provide the storefront, product catalog, checkout, and order management.

\* \*\*MySQL:\*\* Stores WordPress and WooCommerce data.

\* \*\*WooCommerce MCP server:\*\* Exposes product and order operations through MCP tools.

\* \*\*Inventory MCP server:\*\* Provides inventory-related tools.

\* \*\*Customer Support MCP server:\*\* Provides customer-support tools.

\* \*\*MCP Gateway:\*\* Authenticates clients, discovers upstream tools, routes tool calls, and records audit events.

\* \*\*React dashboard:\*\* Provides the interface for server management, API-key management, audit logs, and chat.

\* \*\*AI chat agent:\*\* Uses the gateway's tools to answer user requests.

\* \*\*External MCP client:\*\* Demonstrates access through the gateway using a user-specific API key.



\## 3. Request Flow



1\. A user or external MCP client sends a request to the gateway.

2\. The gateway validates the user's API key.

3\. The gateway discovers tools exposed by enabled upstream servers.

4\. The gateway routes a tool call to the appropriate upstream MCP server.

5\. The upstream server executes the requested operation.

6\. The result is returned through the gateway to the client.

7\. The gateway records relevant audit information, including the user, server, tool, timestamp, duration, and outcome.



The chat agent uses the gateway rather than bypassing it to call upstream servers directly.



\## 4. Tool Aggregation and Routing



The gateway aggregates tools from the registered MCP servers into a unified interface. Tool names use server-specific prefixes to distinguish tools from different upstream servers.



For example:



\* `woocommerce\_\_list\_products`

\* `inventory\_\_check\_stock`

\* `customer\_support\_\_search\_faq`



The gateway uses the tool name and its server registry to determine the appropriate upstream destination.



\## 5. Authentication and Credentials



Clients authenticate with gateway API keys. Each key is associated with a user and can be revoked.



Upstream credentials are managed on the server side. They must not be returned to the dashboard or external MCP clients. Application credentials should be supplied through Kubernetes Secrets or an equivalent secret-management mechanism rather than committed as plaintext configuration.



\## 6. Failure Handling



The gateway should isolate failures between upstream servers. A timeout or unreachable server should produce a clear error without unnecessarily blocking requests to healthy servers.



Operational verification should include:



\* Testing gateway tool discovery.

\* Calling tools from each upstream server.

\* Disabling an upstream and checking tool visibility.

\* Simulating an upstream failure in a controlled test.

\* Confirming that healthy upstream servers remain usable.

\* Inspecting audit records for failed calls.



\## 7. Kubernetes and Helm



The application uses Kubernetes workloads and Services. Helm charts are maintained for the gateway and the three MCP servers.



The repository includes local and production values files. Environment-specific configuration can cover image references, service settings, resource allocation, storage, and ingress configuration.



WordPress content and MySQL data require persistent storage. Public access should be limited to intended storefront, dashboard, and gateway entry points. Internal MCP servers should remain inaccessible from outside the cluster.



Before a new deployment, validate the charts, configure the required Secrets, verify persistent storage and Ingress resources, and check readiness and liveness probes.



\## 8. Local-to-Production Tradeoffs



The same application charts can be configured for local Kubernetes and a production-like K3s environment.



Production configuration must account for:



\* Stable DNS names and ingress routing.

\* TLS where appropriate.

\* The available storage class and persistent volumes.

\* Secure management and rotation of credentials.

\* Container image availability and pull policies.

\* Resource requests and limits.

\* Backup and recovery of persistent data.

\* Helm upgrade and rollback procedures.



Environment values should contain configuration rather than real credentials.



\## 9. Design Tradeoffs



\* \*\*Single gateway endpoint:\*\* Simplifies client configuration but makes gateway availability and authentication important.

\* \*\*Independent MCP servers:\*\* Isolates business functions and makes individual services easier to troubleshoot, but introduces network and protocol failure modes.

\* \*\*Server-side credentials:\*\* Prevents clients from needing upstream credentials, but requires careful access control and secret management.

\* \*\*Kubernetes and Helm:\*\* Support repeatable deployment, but require correct configuration of storage, networking, probes, and resource limits.

\* \*\*Centralized audit logging:\*\* Helps with traceability, but logs must avoid storing API keys, passwords, or other sensitive values.



\## 10. Verification Status



This document describes the intended architecture and verification approach. Claims about specific security controls, failure isolation, and production readiness should be supported by source-code inspection and test results before being presented as verified.



