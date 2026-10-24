# Urumi MCP Gateway Platform

A Kubernetes-deployed Model Context Protocol (MCP) gateway that provides centralized access to multiple MCP servers, authenticated tool execution, API-key management, audit logging, and an AI chat interface.

## Architecture

The platform contains these components:

- **MCP Gateway:** Routes tool requests to configured MCP servers and provides centralized authentication and audit logging.
- **WooCommerce MCP Server:** Provides product and order operations through a custom MCP server.
- **Inventory MCP Server:** Exposes inventory-related tools.
- **Customer Support MCP Server:** Exposes customer-support tools.
- **Dashboard:** Provides the management interface for gateway configuration, API keys, server health, and audit logs.
- **External MCP Client:** Demonstrates connecting to the gateway from an independent client.
- **WordPress and WooCommerce:** Provide the e-commerce backend.
- **MySQL:** Stores WordPress data.

## Technology Stack

- Python and FastAPI
- Model Context Protocol (MCP)
- React and Vite
- Docker
- Kubernetes and Helm
- K3s
- WordPress and WooCommerce
- MySQL
- Vercel for the dashboard frontend

## Repository Structure

```text
urumi/
├── aws-deployment/
│   ├── helm/
│   └── k8s/
├── customer-support-mcp-server/
├── dashboard/
├── external-mcp-client/
├── inventory-mcp-server/
├── keys/
├── mcp-gateway/
└── woo-mcp-server/
```

## MCP Tools

### WooCommerce

- `woocommerce__list_products`
- `woocommerce__create_product`
- `woocommerce__list_orders`
- `woocommerce__get_order`
- `woocommerce__update_order_status`

### Inventory

- `inventory__list_inventory`
- `inventory__check_stock`
- `inventory__update_stock`

### Customer Support

- `customer_support__search_faq`
- `customer_support__get_shipping_policy`
- `customer_support__create_support_ticket`

The gateway also provides a gateway status tool.

## Security and Observability

The gateway is designed to provide:

- API-key authentication for MCP requests.
- User-associated API keys and revocation.
- Centralized routing to configured upstream servers.
- Audit records containing user, server, tool, timestamp, duration, and outcome.
- Kubernetes Secret references for application credentials.
- Container security contexts, resource limits, and health probes.

Verify each security control against the deployed application before representing it as production-ready.

## Prerequisites

For local deployment, install:

- Docker
- Kubernetes through a local cluster such as k3d, kind, or Minikube
- Helm
- kubectl

For VPS deployment, use a Linux host with K3s, kubectl access, Helm, and the required container images.

## Helm Chart Validation

Run these commands from the repository root in PowerShell:

```powershell
helm lint .\mcp-gateway\helm\gateway
helm lint .\woo-mcp-server\helm\woo-mcp
helm lint .\inventory-mcp-server\helm\inventory-mcp
helm lint .\customer-support-mcp-server\helm\customer-support-mcp
```

Render the production manifests without deploying:

```powershell
helm template urumi-gateway .\mcp-gateway\helm\gateway `
  -f .\mcp-gateway\helm\gateway\values-prod.yaml

helm template woo-mcp .\woo-mcp-server\helm\woo-mcp `
  -f .\woo-mcp-server\helm\woo-mcp\values-prod.yaml

helm template inventory-mcp .\inventory-mcp-server\helm\inventory-mcp `
  -f .\inventory-mcp-server\helm\inventory-mcp\values-prod.yaml

helm template customer-support-mcp .\customer-support-mcp-server\helm\customer-support-mcp `
  -f .\customer-support-mcp-server\helm\customer-support-mcp\values-prod.yaml
```

These commands validate chart rendering. They do not deploy the application.

## Kubernetes Deployment

The application has individual Helm charts for the gateway and three MCP servers. Each chart has its own `values.yaml`, `values-local.yaml`, and `values-prod.yaml`.

The shared files under `aws-deployment/helm/` describe environment-level settings. They must be mapped to the individual charts through a deployment script or equivalent orchestration; they are not automatically consumed by the independent charts.

WordPress and MySQL manifests are located under `aws-deployment/k8s/`.

Before deploying to a new cluster:

1. Create the target namespace.
2. Create Kubernetes Secrets for all required credentials.
3. Verify image availability and pull policies.
4. Apply the WordPress and MySQL resources.
5. Install the MCP charts with the appropriate environment-specific values.
6. Wait for workloads to become ready.
7. Verify health endpoints and gateway tool discovery.

Do not apply manifests containing plaintext credentials. Use externally managed or securely generated Kubernetes Secrets.

## Suggested Functional Test Plan

1. Authenticate using a valid member API key.
2. Discover tools exposed through the gateway.
3. List WooCommerce products.
4. Create a test product and verify it in WooCommerce.
5. Place a test order and retrieve its details.
6. Query inventory and customer-support tools.
7. Inspect audit records for user attribution, duration, and outcome.
8. Revoke a test API key and verify that subsequent requests are rejected.
9. Disable an upstream server and verify its tools are no longer available.
10. Stop a test upstream pod and verify failure isolation and recovery.

Use test data and non-production credentials during demonstrations.

## Deployment Environment

The project has been deployed to a K3s cluster on an AWS VPS. The WordPress NodePort endpoint used during testing is:

`http://3.26.224.164:30080/`

This endpoint depends on the server remaining available and the relevant network rules. Do not publish credentials, API keys, private customer data, or administrative URLs containing sensitive tokens.

## Known Deployment Considerations

- The gateway and MCP servers use separate Helm charts.
- The shared environment values need an explicit deployment workflow.
- The AWS Helm release metadata previously showed a failed gateway release even though the gateway workload subsequently became healthy. Check both Helm release status and Kubernetes workload health.
- The production deployment should be validated before running an upgrade.
- Database credentials must be rotated and removed from plaintext manifests before the repository is published.

