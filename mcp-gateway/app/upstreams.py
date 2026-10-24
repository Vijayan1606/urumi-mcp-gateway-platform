import os

UPSTREAMS = {
    "woocommerce": {
        "url": os.getenv(
            "WOOCOMMERCE_MCP_URL",
            "http://woo-mcp.urumi.svc.cluster.local:8000/mcp",
        ),
        "enabled": True,
    },
    "inventory": {
        "url": os.getenv(
            "INVENTORY_MCP_URL",
            "http://inventory-mcp.urumi.svc.cluster.local:8000/",
        ),
        "enabled": True,
    },
    "customer_support": {
        "url": os.getenv(
            "CUSTOMER_SUPPORT_MCP_URL",
            "http://customer-support-mcp.urumi.svc.cluster.local:8000/",
        ),
        "enabled": True,
    },
}
