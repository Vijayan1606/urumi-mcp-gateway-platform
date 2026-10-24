from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

mcp = FastMCP(
    "Urumi Inventory MCP",
    host="0.0.0.0",
    port=8000,
    streamable_http_path="/",
    stateless_http=True,
    json_response=True,
)
inventory = {
    "MOUSE-001": {
        "name": "Wireless Mouse",
        "quantity": 25,
        "warehouse": "Bangalore",
    },
    "KEYBOARD-001": {
        "name": "Mechanical Keyboard",
        "quantity": 12,
        "warehouse": "Bangalore",
    },
    "HEADSET-001": {
        "name": "USB Headset",
        "quantity": 8,
        "warehouse": "Chennai",
    },
}


@mcp.tool()
def list_inventory() -> list[dict]:
    """List all inventory items and their stock quantities."""
    return [
        {"sku": sku, **item}
        for sku, item in inventory.items()
    ]


@mcp.tool()
def check_stock(sku: str) -> dict:
    """Check the available stock for a specific SKU."""
    item = inventory.get(sku.upper())

    if item is None:
        return {
            "found": False,
            "sku": sku,
            "message": "SKU not found",
        }

    return {
        "found": True,
        "sku": sku.upper(),
        **item,
    }


@mcp.tool()
def update_stock(sku: str, quantity: int) -> dict:
    """Set the available stock quantity for an existing SKU."""
    if quantity < 0:
        return {
            "success": False,
            "message": "Quantity cannot be negative",
        }

    item = inventory.get(sku.upper())

    if item is None:
        return {
            "success": False,
            "message": "SKU not found",
        }

    item["quantity"] = quantity

    return {
        "success": True,
        "sku": sku.upper(),
        "quantity": quantity,
    }


if __name__ == "__main__":
    import uvicorn
    from contextlib import asynccontextmanager
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    @asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    async def health(request):
        return JSONResponse({"status": "healthy"})

    mcp_app = mcp.streamable_http_app()

    app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Mount("/", app=mcp_app),
        ],
        lifespan=lifespan,
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)
