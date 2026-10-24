import os
from typing import Any

import httpx
from oauthlib.oauth1 import Client as OAuth1Client
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1

from mcp.server.mcpserver import MCPServer


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Internal Kubernetes URL used to reach WordPress.
# For local development, this defaults to localhost:8080.
WOOCOMMERCE_INTERNAL_URL = os.getenv(
    "WOOCOMMERCE_INTERNAL_URL",
    os.getenv(
        "WOOCOMMERCE_URL",
        "http://localhost:8080",
    ),
).rstrip("/")

# Canonical URL configured in WordPress.
# OAuth signatures must use this canonical hostname.
WOOCOMMERCE_CANONICAL_URL = os.getenv(
    "WOOCOMMERCE_CANONICAL_URL",
    "http://localhost:8080",
).rstrip("/")

WC_CONSUMER_KEY = os.getenv("WC_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.getenv("WC_CONSUMER_SECRET")


if not WC_CONSUMER_KEY or not WC_CONSUMER_SECRET:
    raise RuntimeError(
        "WC_CONSUMER_KEY and WC_CONSUMER_SECRET "
        "environment variables are required."
    )


# ---------------------------------------------------------
# WOOCOMMERCE REST API REQUEST HELPER
# ---------------------------------------------------------

async def woo_request(
    method: str,
    endpoint: str,
    **kwargs: Any,
) -> Any:
    """
    Send authenticated requests to the WooCommerce REST API.

    Connect through the internal Kubernetes service while
    signing requests using the canonical WordPress URL.
    """

    # Copy parameters to avoid modifying the caller's dictionary.
    params = dict(kwargs.pop("params", {}) or {})

    # Use WordPress's index.php REST API fallback route.
    params["rest_route"] = (
        f"/wc/v3/{endpoint.lstrip('/')}"
    )

    # Internal address used for the actual network connection.
    internal_base_url = (
        f"{WOOCOMMERCE_INTERNAL_URL}/index.php"
    )

    # Canonical address used to generate the OAuth signature.
    canonical_base_url = (
        f"{WOOCOMMERCE_CANONICAL_URL}/index.php"
    )

    internal_url = str(
        httpx.URL(
            internal_base_url,
            params=params,
        )
    )

    canonical_url = str(
        httpx.URL(
            canonical_base_url,
            params=params,
        )
    )

    # Generate the OAuth 1.0a authorization header.
    oauth_client = OAuth1Client(
        WC_CONSUMER_KEY,
        client_secret=WC_CONSUMER_SECRET,
        signature_method=SIGNATURE_HMAC_SHA1,
    )

    _, auth_headers, _ = oauth_client.sign(
        canonical_url,
        http_method=method.upper(),
    )

    # WordPress expects the canonical hostname.
    auth_headers["Host"] = (
        httpx.URL(WOOCOMMERCE_CANONICAL_URL).netloc
    )

    timeout = httpx.Timeout(15.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
    ) as client:

        response = await client.request(
            method.upper(),
            internal_url,
            headers=auth_headers,
            **kwargs,
        )

        response.raise_for_status()

        return response.json()


# ---------------------------------------------------------
# MCP SERVER
# ---------------------------------------------------------

server = MCPServer(
    name="Urumi WooCommerce MCP Server",
    title="Urumi WooCommerce MCP Server",
    description=(
        "MCP server exposing WooCommerce product and "
        "order management tools."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# TOOL 1: LIST PRODUCTS
# ---------------------------------------------------------

@server.tool(
    name="list_products",
    title="List WooCommerce Products",
    description="List products from the WooCommerce store.",
)
async def list_products(
    page: int = 1,
    per_page: int = 20,
) -> list:
    """List products from WooCommerce."""

    if page < 1:
        raise ValueError(
            "page must be greater than or equal to 1."
        )

    if not 1 <= per_page <= 100:
        raise ValueError(
            "per_page must be between 1 and 100."
        )

    return await woo_request(
        "GET",
        "products",
        params={
            "page": page,
            "per_page": per_page,
        },
    )


# ---------------------------------------------------------
# TOOL 2: CREATE PRODUCT
# ---------------------------------------------------------

@server.tool(
    name="create_product",
    title="Create WooCommerce Product",
    description="Create a simple product in WooCommerce.",
)
async def create_product(
    name: str,
    regular_price: str = "0",
    description: str = "",
    short_description: str = "",
    stock_quantity: int | None = None,
) -> dict:
    """Create a simple product in WooCommerce."""

    if not name.strip():
        raise ValueError(
            "Product name cannot be empty."
        )

    try:
        price = float(regular_price)
    except (TypeError, ValueError):
        raise ValueError(
            "regular_price must be a valid number."
        )

    if price < 0:
        raise ValueError(
            "regular_price cannot be negative."
        )

    if stock_quantity is not None and stock_quantity < 0:
        raise ValueError(
            "stock_quantity cannot be negative."
        )

    product = {
        "name": name.strip(),
        "type": "simple",
        "regular_price": str(regular_price),
        "description": description,
        "short_description": short_description,
    }

    if stock_quantity is not None:
        product["manage_stock"] = True
        product["stock_quantity"] = stock_quantity

    return await woo_request(
        "POST",
        "products",
        json=product,
    )


# ---------------------------------------------------------
# TOOL 3: LIST ORDERS
# ---------------------------------------------------------

@server.tool(
    name="list_orders",
    title="List WooCommerce Orders",
    description="List orders from the WooCommerce store.",
)
async def list_orders(
    page: int = 1,
    per_page: int = 20,
    after: str | None = None,
    before: str | None = None,
) -> list:
    """List WooCommerce orders, optionally filtered by date."""

    if page < 1:
        raise ValueError(
            "page must be greater than or equal to 1."
        )

    if not 1 <= per_page <= 100:
        raise ValueError(
            "per_page must be between 1 and 100."
        )

    params: dict[str, Any] = {
        "page": page,
        "per_page": per_page,
    }

    if after:
        params["after"] = after

    if before:
        params["before"] = before

    return await woo_request(
        "GET",
        "orders",
        params=params,
    )


# ---------------------------------------------------------
# TOOL 4: GET ORDER
# ---------------------------------------------------------

@server.tool(
    name="get_order",
    title="Get WooCommerce Order",
    description="Get a WooCommerce order by its ID.",
)
async def get_order(
    order_id: int,
) -> dict:
    """Get a WooCommerce order by ID."""

    if order_id < 1:
        raise ValueError(
            "order_id must be a positive integer."
        )

    return await woo_request(
        "GET",
        f"orders/{order_id}",
    )


# ---------------------------------------------------------
# TOOL 5: UPDATE ORDER STATUS
# ---------------------------------------------------------

@server.tool(
    name="update_order_status",
    title="Update WooCommerce Order Status",
    description="Update the status of a WooCommerce order.",
)
async def update_order_status(
    order_id: int,
    status: str,
) -> dict:
    """Update the status of a WooCommerce order."""

    if order_id < 1:
        raise ValueError(
            "order_id must be a positive integer."
        )

    allowed_statuses = {
        "pending",
        "processing",
        "on-hold",
        "completed",
        "cancelled",
        "refunded",
        "failed",
    }

    if status not in allowed_statuses:
        raise ValueError(
            f"Invalid order status: {status}. "
            f"Allowed values: {sorted(allowed_statuses)}"
        )

    return await woo_request(
        "PUT",
        f"orders/{order_id}",
        json={
            "status": status,
        },
    )

# ---------------------------------------------------------
# TOOL 6: CREATE ORDER
# ---------------------------------------------------------
@server.tool(
    name="create_order",
    title="Create WooCommerce Order",
    description=(
        "Create a WooCommerce order with product line items "
        "and customer billing details. Supports Cash on Delivery."
    ),
)
async def create_order(
    product_id: int,
    quantity: int = 1,
    first_name: str = "Test",
    last_name: str = "Customer",
    address_1: str = "123 Demo Street",
    city: str = "Bangalore",
    state: str = "KA",
    postcode: str = "560001",
    country: str = "IN",
    email: str = "test@example.com",
    phone: str = "9000000000",
    payment_method: str = "cod",
) -> dict:
    """Create a WooCommerce order for an existing product."""

    if product_id < 1:
        raise ValueError("product_id must be a positive integer.")

    if quantity < 1:
        raise ValueError("quantity must be at least 1.")

    if not first_name.strip() or not last_name.strip():
        raise ValueError("Customer first and last names are required.")

    if not address_1.strip() or not city.strip():
        raise ValueError("Billing address and city are required.")

    if payment_method not in {"cod"}:
        raise ValueError(
            "Only Cash on Delivery (cod) is supported by this tool."
        )

    # Confirm that the product exists before creating the order.
    product = await woo_request(
        "GET",
        f"products/{product_id}",
    )

    if product.get("status") != "publish":
        raise ValueError("The product must be published before ordering.")

    if product.get("stock_status") != "instock":
        raise ValueError("The product is not currently in stock.")

    stock_quantity = product.get("stock_quantity")

    if (
        product.get("manage_stock")
        and stock_quantity is not None
        and stock_quantity < quantity
    ):
        raise ValueError(
            f"Insufficient stock. Available quantity: {stock_quantity}."
        )

    order_payload = {
        "payment_method": "cod",
        "payment_method_title": "Cash on Delivery",
        "set_paid": False,
        "status": "pending",
        "billing": {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "address_1": address_1.strip(),
            "city": city.strip(),
            "state": state.strip(),
            "postcode": postcode.strip(),
            "country": country.strip().upper(),
            "email": email.strip(),
            "phone": phone.strip(),
        },
        "line_items": [
            {
                "product_id": product_id,
                "quantity": quantity,
            }
        ],
    }

    return await woo_request(
        "POST",
        "orders",
        json=order_payload,
    )
# ---------------------------------------------------------
# START MCP SERVER
# ---------------------------------------------------------

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
    )
