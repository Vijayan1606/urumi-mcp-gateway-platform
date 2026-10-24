"""Authenticated Streamable HTTP MCP facade for the Urumi gateway.

Upstream tools are discovered at application startup and exposed with names
like ``woocommerce__list_products``. API keys are checked on every HTTP
request. Upstream credentials remain in the gateway's server-side config.
"""

import asyncio
import inspect
import keyword
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth_service import authenticate_api_key
from app.db import SessionLocal
from app.models import AuditLog
from app.mcp_client import MCPUpstreamClient
from app.upstream_service import get_upstream, get_upstreams

REQUEST_TIMEOUT = 20
TOOL_SEPARATOR = "__"
_current_user_id: ContextVar[Optional[int]] = ContextVar(
    "mcp_current_user_id", default=None
)

mcp_server = FastMCP(
    name="Urumi MCP Gateway",
    instructions=(
        "Use approved tools exposed by the Urumi gateway. Tool names are "
        "namespaced as server__tool, for example woocommerce__list_products."
    ),
    streamable_http_path="/",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "reuters-chicken-attractive-unable.trycloudflare.com",
            "danny-evans-teens-deputy.trycloudflare.com",
        ],
    ),
)


def resolve_tool_name(server_name: str, tool_name: str) -> str:
    return f"{server_name}{TOOL_SEPARATOR}{tool_name}"


def write_mcp_audit(
    user_id: int,
    server: str,
    tool: str,
    started: float,
    outcome: str,
    error_message: Optional[str] = None,
) -> None:
    """Persist an audit record without allowing audit DB errors to crash MCP."""
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                user_id=user_id,
                server=server,
                tool=tool,
                timestamp=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                outcome=outcome,
                error_message=error_message[:2000] if error_message else None,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        print("Failed to write MCP audit log.", flush=True)
    finally:
        db.close()


async def discover_upstream_tools(server_name: str, config: dict) -> list[dict]:
    if not config.get("enabled", False):
        return []

    async def operation():
        client = MCPUpstreamClient(
            config["url"],
            headers=config.get("headers") or {},
        )
        try:
            await client.connect()
            return await client.list_tools()
        finally:
            await client.close()

    return await asyncio.wait_for(operation(), timeout=REQUEST_TIMEOUT)


async def call_upstream_tool(server_name: str, tool_name: str, arguments: dict):
    config = get_upstream(server_name)

    if not config or not config.get("enabled", False):
        raise RuntimeError(
            f"Upstream server '{server_name}' is disabled or not configured."
        )

    async def operation():
        client = MCPUpstreamClient(
            config["url"],
            headers=config.get("headers") or {},
        )
        try:
            await client.connect()
            return await client.call_tool(tool_name, arguments)
        finally:
            await client.close()

    return await asyncio.wait_for(operation(), timeout=REQUEST_TIMEOUT)


def _annotation_for_schema(property_schema: dict):
    """Translate common JSON Schema types to Python annotations for FastMCP."""
    schema_type = property_schema.get("type")
    if isinstance(schema_type, list):
        non_null = [item for item in schema_type if item != "null"]
        schema_type = non_null[0] if len(non_null) == 1 else None

    return {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }.get(schema_type, Any)


def _build_tool_handler(server_name: str, tool_name: str, input_schema: dict):
    """Create a handler with a schema-derived signature and fixed upstream IDs."""

    async def handler(**arguments) -> dict:
        user_id = _current_user_id.get()
        if user_id is None:
            raise RuntimeError("Authentication context is missing.")

        started = time.perf_counter()
        try:
            result = await call_upstream_tool(server_name, tool_name, arguments or {})
            is_error = (
                bool(result.get("isError", False))
                if isinstance(result, dict)
                else bool(getattr(result, "isError", False))
            )
            raw_content = (
                result.get("content", [])
                if isinstance(result, dict)
                else getattr(result, "content", [])
            )
            content = []
            for item in raw_content or []:
                if isinstance(item, dict):
                    content.append(
                        {
                            "type": item.get("type", "text"),
                            "text": item.get("text"),
                        }
                    )
                else:
                    content.append(
                        {
                            "type": getattr(item, "type", "text"),
                            "text": getattr(item, "text", None),
                        }
                    )

            write_mcp_audit(
                user_id,
                server_name,
                tool_name,
                started,
                "error" if is_error else "success",
                "Upstream reported a tool error." if is_error else None,
            )
            return {
                "server": server_name,
                "tool": tool_name,
                "isError": is_error,
                "content": content,
            }
        except asyncio.TimeoutError:
            write_mcp_audit(
                user_id,
                server_name,
                tool_name,
                started,
                "timeout",
                "The upstream MCP request timed out.",
            )
            raise RuntimeError("The upstream MCP request timed out.") from None
        except Exception as exc:
            write_mcp_audit(
                user_id,
                server_name,
                tool_name,
                started,
                "error",
                f"{type(exc).__name__}: {exc}",
            )
            raise

    properties = (input_schema or {}).get("properties", {})
    required = set((input_schema or {}).get("required", []))
    parameters = []

    # Required parameters must precede parameters with defaults in a Python
    # signature. JSON Schema property names that cannot be Python arguments
    # are skipped rather than creating an invalid callable signature.
    valid_properties = [
        (name, schema)
        for name, schema in properties.items()
        if name.isidentifier() and not keyword.iskeyword(name)
    ]
    valid_properties.sort(key=lambda pair: pair[0] not in required)

    for property_name, property_schema in valid_properties:
        if property_name in required:
            default = inspect.Parameter.empty
        else:
            default = property_schema.get("default")
            if default is None and property_name == "page":
                default = 1
            elif default is None and property_name == "per_page":
                default = 20
        parameters.append(
            inspect.Parameter(
                property_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=_annotation_for_schema(property_schema or {}),
            )
        )

    handler.__signature__ = inspect.Signature(parameters)
    handler.__annotations__ = {
        parameter.name: parameter.annotation for parameter in parameters
    }
    handler.__annotations__["return"] = dict
    handler.__name__ = f"forward_{server_name}_{tool_name}".replace("-", "_")
    handler.__doc__ = (input_schema or {}).get("description") or (
        f"Forward the call to the {server_name} upstream tool {tool_name}."
    )
    return handler


@mcp_server.tool()
async def gateway_status() -> dict:
    """Return configured upstream servers and their reachability."""
    user_id = _current_user_id.get()

    if user_id is None:
        raise RuntimeError("Authentication context is missing.")

    started = time.perf_counter()
    configured_upstreams = get_upstreams()
    servers = []

    for name, config in configured_upstreams.items():
        enabled = bool(config.get("enabled", False))

        server_info = {
            "name": name,
            "enabled": enabled,
            "status": "disabled" if not enabled else "unknown",
        }

        if enabled:
            try:
                await asyncio.wait_for(
                    discover_upstream_tools(name, config),
                    timeout=5.0,
                )
                server_info["status"] = "healthy"
            except asyncio.TimeoutError:
                server_info["status"] = "unreachable"
            except Exception:
                server_info["status"] = "unreachable"

        servers.append(server_info)

    write_mcp_audit(
        user_id,
        "gateway",
        "gateway_status",
        started,
        "success",
    )

    return {"servers": servers}


async def refresh_tool_registry() -> None:
    """Refresh MCP tools independently for each configured upstream."""

    configured_upstreams = get_upstreams()
    registered_tools = mcp_server._tool_manager._tools

    # Identify upstream tools currently registered in the gateway.
    # Preserve the built-in gateway_status tool.
    for registered_name in list(registered_tools.keys()):
        if registered_name == "gateway_status":
            continue

        # Names generated by resolve_tool_name use the server prefix.
        server_prefix = registered_name.split("__", 1)[0]

        # Remove tools belonging to servers that no longer exist
        # or have been disabled.
        config = configured_upstreams.get(server_prefix)

        if not config or not config.get("enabled", False):
            mcp_server._tool_manager.remove_tool(registered_name)

    # Discover and register tools for enabled upstreams.
    for server_name, config in configured_upstreams.items():
        if not config.get("enabled", False):
            continue

        try:
            upstream_tools = await discover_upstream_tools(
                server_name,
                config,
            )
        except Exception as exc:
            print(
                f"MCP discovery failed for {server_name}: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

            # Remove stale tools for this unreachable server.
            prefix = f"{server_name}__"

            for registered_name in list(mcp_server._tool_manager._tools.keys()):
                if registered_name.startswith(prefix):
                    mcp_server._tool_manager.remove_tool(registered_name)

            continue

        # Discovery succeeded. Replace this upstream's tool definitions.
        prefix = f"{server_name}__"

        for registered_name in list(mcp_server._tool_manager._tools.keys()):
            if registered_name.startswith(prefix):
                mcp_server._tool_manager.remove_tool(registered_name)

        for upstream_tool in upstream_tools:
            original_name = upstream_tool.get("name")

            if not original_name:
                continue

            exposed_name = resolve_tool_name(
                server_name,
                original_name,
            )

            if exposed_name in mcp_server._tool_manager._tools:
                print(
                    f"Skipping duplicate MCP tool: {exposed_name}",
                    flush=True,
                )
                continue

            description = upstream_tool.get("description") or (
                f"Forward to {server_name}.{original_name}"
            )

            handler = _build_tool_handler(
                server_name,
                original_name,
                upstream_tool.get("inputSchema") or {},
            )

            mcp_server.add_tool(
                handler,
                name=exposed_name,
                description=description,
            )

            print(
                f"Registered MCP tool: {exposed_name}",
                flush=True,
            )


class GatewayMCPAuthMiddleware:
    """Pure ASGI middleware authenticating each MCP HTTP request."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        authorization = headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            await self._unauthorized(send, "A bearer API key is required.")
            return

        db = SessionLocal()
        try:
            user = authenticate_api_key(db, token.strip())
            if user is None or not user.is_active:
                await self._unauthorized(send, "Invalid or revoked API key.")
                return
            user_id = user.id
        finally:
            db.close()

        context_token = _current_user_id.set(user_id)
        try:
            await self.app(scope, receive, send)
        finally:
            _current_user_id.reset(context_token)

    @staticmethod
    async def _unauthorized(send: Send, message: str) -> None:
        import json

        body = json.dumps({"detail": message}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


mcp_asgi_app = mcp_server.streamable_http_app()
mcp_asgi_app.add_middleware(GatewayMCPAuthMiddleware)
