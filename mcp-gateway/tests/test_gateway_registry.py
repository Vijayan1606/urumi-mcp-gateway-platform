import asyncio

from app.mcp_gateway import (
    mcp_server,
    refresh_tool_registry,
    resolve_tool_name,
)


def test_resolve_tool_name():
    assert resolve_tool_name(
        "woocommerce",
        "list_products",
    ) == "woocommerce__list_products"


def test_resolve_tool_name_keeps_server_namespace():
    woo_tool = resolve_tool_name("woocommerce", "list_products")
    inventory_tool = resolve_tool_name("inventory", "list_products")

    assert woo_tool != inventory_tool


def test_gateway_status_tool_is_registered():
    assert "gateway_status" in mcp_server._tool_manager._tools


def test_refresh_registry_handles_unreachable_upstream(monkeypatch):
    import app.mcp_gateway as gateway

    async def fake_discover(server_name, config):
        if server_name == "unreachable":
            raise ConnectionError("Test server unavailable")

        return [
            {
                "name": "list_items",
                "description": "List test items",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            }
        ]

    monkeypatch.setattr(
        gateway,
        "get_upstreams",
        lambda: {
            "unreachable": {
                "url": "http://unreachable.invalid/mcp",
                "enabled": True,
            },
            "test_inventory": {
                "url": "http://inventory.invalid/mcp",
                "enabled": True,
            },
        },
    )

    monkeypatch.setattr(
        gateway,
        "discover_upstream_tools",
        fake_discover,
    )

    asyncio.run(refresh_tool_registry())

    registered_tools = mcp_server._tool_manager._tools

    assert "gateway_status" in registered_tools
    assert "test_inventory__list_items" in registered_tools
    assert "unreachable__list_items" not in registered_tools

    # Remove the test tool so it cannot affect subsequent tests.
    mcp_server._tool_manager.remove_tool("test_inventory__list_items")
def test_disabled_upstream_tools_are_removed(monkeypatch):
    import app.mcp_gateway as gateway

    async def fake_discover(server_name, config):
        return [
            {
                "name": "list_items",
                "description": "List test items",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            }
        ]

    # First refresh: the upstream is enabled.
    monkeypatch.setattr(
        gateway,
        "get_upstreams",
        lambda: {
            "test_inventory": {
                "url": "http://inventory.invalid/mcp",
                "enabled": True,
            }
        },
    )
    monkeypatch.setattr(
        gateway,
        "discover_upstream_tools",
        fake_discover,
    )

    asyncio.run(refresh_tool_registry())

    assert "test_inventory__list_items" in (
        mcp_server._tool_manager._tools
    )

    # Second refresh: the upstream is disabled.
    monkeypatch.setattr(
        gateway,
        "get_upstreams",
        lambda: {
            "test_inventory": {
                "url": "http://inventory.invalid/mcp",
                "enabled": False,
            }
        },
    )

    asyncio.run(refresh_tool_registry())

    assert "test_inventory__list_items" not in (
        mcp_server._tool_manager._tools
    )
    assert "gateway_status" in mcp_server._tool_manager._tools

def test_deleted_upstream_tools_are_removed(monkeypatch):
    import app.mcp_gateway as gateway

    async def fake_discover(server_name, config):
        return [
            {
                "name": "list_items",
                "description": "List test items",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            }
        ]

    # First refresh: the upstream exists.
    monkeypatch.setattr(
        gateway,
        "get_upstreams",
        lambda: {
            "temporary_inventory": {
                "url": "http://inventory.invalid/mcp",
                "enabled": True,
            }
        },
    )
    monkeypatch.setattr(
        gateway,
        "discover_upstream_tools",
        fake_discover,
    )

    asyncio.run(refresh_tool_registry())

    assert "temporary_inventory__list_items" in (
        mcp_server._tool_manager._tools
    )

    # Second refresh: the upstream has been deleted.
    monkeypatch.setattr(
        gateway,
        "get_upstreams",
        lambda: {},
    )

    asyncio.run(refresh_tool_registry())

    assert "temporary_inventory__list_items" not in (
        mcp_server._tool_manager._tools
    )
    assert "gateway_status" in mcp_server._tool_manager._tools

def test_tool_timeout_is_audited(monkeypatch):
    import app.mcp_gateway as gateway

    audit_records = []

    async def fake_call_upstream_tool(server, tool, arguments):
        raise asyncio.TimeoutError()

    def fake_write_mcp_audit(
        user_id,
        server,
        tool,
        started,
        outcome,
        error_message=None,
    ):
        audit_records.append({
            "user_id": user_id,
            "server": server,
            "tool": tool,
            "outcome": outcome,
            "error_message": error_message,
        })

    monkeypatch.setattr(
        gateway,
        "call_upstream_tool",
        fake_call_upstream_tool,
    )
    monkeypatch.setattr(
        gateway,
        "write_mcp_audit",
        fake_write_mcp_audit,
    )

    handler = gateway._build_tool_handler(
        server_name="test_inventory",
        tool_name="list_items",
        input_schema={"type": "object", "properties": {}},
    )

    gateway._current_user_id.set(123)

    try:
        try:
            asyncio.run(handler())
            assert False, "Expected a timeout RuntimeError"
        except RuntimeError as exc:
            assert "timed out" in str(exc).lower()
    finally:
        gateway._current_user_id.set(None)

    assert len(audit_records) == 1
    assert audit_records[0]["user_id"] == 123
    assert audit_records[0]["server"] == "test_inventory"
    assert audit_records[0]["tool"] == "list_items"
    assert audit_records[0]["outcome"] == "timeout"
    assert "timed out" in audit_records[0]["error_message"].lower()
