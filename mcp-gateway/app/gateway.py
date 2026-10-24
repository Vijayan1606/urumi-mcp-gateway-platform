import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin, get_db
from app.db import Base, engine
from app.models import APIKey, AuditLog, UpstreamServer, User
from app.mcp_client import MCPUpstreamClient
from app.upstream_service import get_upstream, get_upstreams
from app.mcp_gateway import (
    _current_user_id,
    gateway_status,
    mcp_server,
    refresh_tool_registry,
)
from app.ai_chat import ask_gemini

# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

Base.metadata.create_all(bind=engine)
from app.bootstrap_k8s_admin import bootstrap_admin
bootstrap_admin()
# --------------------------------------------------
# UPSTREAM MCP SERVER CONFIGURATION
# --------------------------------------------------

REQUEST_TIMEOUT = 20


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------
async def periodic_registry_refresh():
    """Periodically refresh upstream MCP tools."""
    while True:
        await asyncio.sleep(30)

        try:
            await refresh_tool_registry()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(
                f"Periodic registry refresh failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Urumi MCP Gateway starting...", flush=True)

    async with mcp_server.session_manager.run():
        await refresh_tool_registry()

        refresh_task = asyncio.create_task(
            periodic_registry_refresh()
        )

        try:
            yield
        finally:
            refresh_task.cancel()

            try:
                await refresh_task
            except asyncio.CancelledError:
                pass

    print("Urumi MCP Gateway shutting down...", flush=True)

app = FastAPI(
    title="Urumi MCP Gateway",
    description="A gateway for multiple MCP servers",
    version="1.1.0",
    lifespan=lifespan,
)

# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://urumi-dashboard.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)

# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class ToolCallRequest(BaseModel):
    server: str = "woocommerce"
    tool: str
    arguments: dict = Field(default_factory=dict)

class UpstreamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    url: HttpUrl
    enabled: bool = True
    headers: dict[str, str] = Field(default_factory=dict)


class UpstreamUpdateRequest(BaseModel):
    url: HttpUrl | None = None
    enabled: bool | None = None
    headers: dict[str, str] | None = None


class UpstreamEnabledRequest(BaseModel):
    enabled: bool

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

async def run_upstream_operation(operation):
    return await asyncio.wait_for(
        operation(),
        timeout=REQUEST_TIMEOUT,
    )


def write_audit_log(
    db: Session,
    user_id: int,
    server: str,
    tool: str,
    start_time: float,
    outcome: str,
    error_message: str | None = None,
):
    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )

    try:
        log = AuditLog(
            user_id=user_id,
            server=server,
            tool=tool,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            outcome=outcome,
            error_message=error_message[:2000] if error_message else None,
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
        print("Failed to write audit log.", flush=True)


# --------------------------------------------------
# BASIC ENDPOINTS
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "Urumi MCP Gateway",
        "status": "running",
    }


@app.get("/health")
async def health():
    # Public endpoint for Kubernetes health probes.
    return {
        "status": "healthy",
        "service": "urumi-mcp-gateway",
    }

@app.get("/servers")
async def list_servers(
    user: User = Depends(get_current_user),
):
    return [
        {
            "name": name,
            "enabled": bool(config.get("enabled", False)),
            "url": config["url"],
        }
        for name, config in get_upstreams().items()
    ]

@app.get("/admin/upstream-health")
async def upstream_health(
    user: User = Depends(get_current_user),
):
    """Return live upstream health for the authenticated dashboard user."""
    from app.mcp_gateway import _current_user_id

    token = _current_user_id.set(user.id)

    try:
        return await gateway_status()
    finally:
        _current_user_id.reset(token)

# --------------------------------------------------
# MCP TOOL DISCOVERY
# --------------------------------------------------

async def discover_tools(name: str, config: dict):
    if not config["enabled"]:
        return []

    async def operation():
        client = MCPUpstreamClient(config["url"])

        try:
            await client.connect()
            tools = await client.list_tools()

            return [
                {
                    **tool,
                    "server": name,
                }
                for tool in tools
            ]
        finally:
            await client.close()

    return await run_upstream_operation(operation)


@app.get("/tools")
async def list_tools(
    user: User = Depends(get_current_user),
):
    aggregated_tools = []
    upstream_errors = []

    configured_upstreams = get_upstreams()
    enabled_servers = [
        name
        for name, config in configured_upstreams.items()
        if config.get("enabled", False)
    ]


    for name in enabled_servers:
        config = configured_upstreams[name]

        try:
            tools = await discover_tools(name, config)
            aggregated_tools.extend(tools)

        except asyncio.TimeoutError:
            message = f"Timed out connecting to upstream '{name}'."
            print(message, flush=True)
            upstream_errors.append({
                "server": name,
                "error": message,
            })

        except Exception as error:
            message = (
                f"{type(error).__name__}: "
                f"{str(error) or 'No details available'}"
            )
            print(
                f"Tool discovery failed for '{name}': {message}",
                flush=True,
            )
            upstream_errors.append({
                "server": name,
                "error": message,
            })

    if enabled_servers and not aggregated_tools and upstream_errors:
        raise HTTPException(
            status_code=502,
            detail={
                "message": (
                    "Unable to discover tools from enabled upstream servers."
                ),
                "upstream_errors": upstream_errors,
            },
        )

    return {
        "tools": aggregated_tools,
        "count": len(aggregated_tools),
        "upstream_errors": upstream_errors,
    }


# --------------------------------------------------
# MCP TOOL EXECUTION + AUDIT LOGGING
# --------------------------------------------------

@app.post("/tools/call")
async def call_tool(
    request: ToolCallRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.perf_counter()

    config = get_upstream(request.server)

    if not config or not config["enabled"]:
        write_audit_log(
            db=db,
            user_id=user.id,
            server=request.server,
            tool=request.tool,
            start_time=start_time,
            outcome="rejected",
            error_message="Upstream server not found or disabled.",
        )
        raise HTTPException(
            status_code=404,
            detail="Upstream server not found or disabled.",
        )

    async def operation():
        client = MCPUpstreamClient(config["url"])

        try:
            await client.connect()

            result = await client.call_tool(
                request.tool,
                request.arguments,
            )

            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            return {
                "server": request.server,
                "tool": request.tool,
                "duration_ms": duration_ms,
                "isError": result.isError,
                "content": [
                    {
                        "type": item.type,
                        "text": getattr(item, "text", None),
                    }
                    for item in result.content
                ],
            }
        finally:
            await client.close()

    try:
        response = await run_upstream_operation(operation)

        write_audit_log(
            db=db,
            user_id=user.id,
            server=request.server,
            tool=request.tool,
            start_time=start_time,
            outcome="error" if response["isError"] else "success",
            error_message=(
                "Upstream reported a tool error."
                if response["isError"]
                else None
            ),
        )

        return response

    except asyncio.TimeoutError:
        write_audit_log(
            db=db,
            user_id=user.id,
            server=request.server,
            tool=request.tool,
            start_time=start_time,
            outcome="timeout",
            error_message="The upstream MCP request timed out.",
        )
        raise HTTPException(
            status_code=504,
            detail="The upstream MCP request timed out.",
        )

    except HTTPException:
        raise

    except Exception as error:
        write_audit_log(
            db=db,
            user_id=user.id,
            server=request.server,
            tool=request.tool,
            start_time=start_time,
            outcome="error",
            error_message=f"{type(error).__name__}: {error}",
        )

        print(
            f"Tool call failed: {type(error).__name__}: {error}",
            flush=True,
        )

        raise HTTPException(
            status_code=502,
            detail={
                "message": "Upstream MCP tool call failed.",
                "error_type": type(error).__name__,
            },
        )
# --------------------------------------------------
# GEMINI AI CHAT
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@app.post("/chat")
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    started = time.perf_counter()

    try:
        result = await asyncio.wait_for(
            ask_gemini(payload.message.strip(), user.id),
            timeout=90,
        )

        return result

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="The AI request timed out. Please try again.",
        )

    except Exception as exc:
        print(
            f"AI chat failed: {type(exc).__name__}: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=502,
            detail="The AI assistant could not complete the request.",
        )
# --------------------------------------------------
# ADMIN: UPSTREAM SERVER MANAGEMENT
# --------------------------------------------------

import json
from urllib.parse import urlsplit


def serialize_upstream(server: UpstreamServer) -> dict:
    """Return upstream configuration without exposing credentials."""
    return {
        "id": server.id,
        "name": server.name,
        "url": server.url,
        "enabled": server.enabled,
        "has_headers": bool(server.headers_json),
        "created_at": server.created_at.isoformat(),
        "updated_at": server.updated_at.isoformat(),
    }


def validate_upstream_url(url: str) -> None:
    """Reject URLs that could expose local files or cloud metadata."""
    parsed = urlsplit(url)

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(
            status_code=400,
            detail="A valid HTTP or HTTPS upstream URL is required.",
        )

    if parsed.username or parsed.password:
        raise HTTPException(
            status_code=400,
            detail="Credentials must not be embedded in the URL.",
        )

    blocked_hosts = {
        "localhost",
        "127.0.0.1",
        "::1",
        "169.254.169.254",
        "metadata.google.internal",
    }

    hostname = parsed.hostname.lower()

    if hostname in blocked_hosts:
        raise HTTPException(
            status_code=400,
            detail="This upstream hostname is not allowed.",
        )


@app.get("/admin/upstreams")
async def admin_list_upstreams(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    servers = (
        db.query(UpstreamServer)
        .order_by(UpstreamServer.name)
        .all()
    )

    return [serialize_upstream(server) for server in servers]


@app.post("/admin/upstreams", status_code=201)
async def admin_create_upstream(
    payload: UpstreamCreateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    name = payload.name.strip()
    url = str(payload.url)

    validate_upstream_url(url)

    existing = (
        db.query(UpstreamServer)
        .filter(UpstreamServer.name == name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An upstream with this name already exists.",
        )

    # Reject common secret-bearing headers unless HTTPS is used.
    if payload.headers and not url.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail="Upstream credentials require an HTTPS URL.",
        )

    for header_name, header_value in payload.headers.items():
        if not header_name or "\r" in header_name or "\n" in header_name:
            raise HTTPException(
                status_code=400,
                detail="Invalid header name.",
            )

        if "\r" in header_value or "\n" in header_value:
            raise HTTPException(
                status_code=400,
                detail="Invalid header value.",
            )

    server = UpstreamServer(
        name=name,
        url=url,
        enabled=payload.enabled,
        headers_json=json.dumps(payload.headers) if payload.headers else None,
    )

    db.add(server)

    try:
        db.add(server)
        db.commit()
        db.refresh(server)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save the upstream configuration.",
        )

    try:
        await refresh_tool_registry()
    except Exception as exc:
        print(
            f"Warning: upstream registry refresh failed: {exc}",
            flush=True,
        )

    return serialize_upstream(server)


@app.put("/admin/upstreams/{name}")
async def admin_update_upstream(
    name: str,
    payload: UpstreamUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    server = (
        db.query(UpstreamServer)
        .filter(UpstreamServer.name == name)
        .first()
    )

    if server is None:
        raise HTTPException(status_code=404, detail="Upstream server not found.")

    if payload.url is not None:
        url = str(payload.url)
        validate_upstream_url(url)

        if payload.headers and not url.startswith("https://"):
            raise HTTPException(
                status_code=400,
                detail="Upstream credentials require an HTTPS URL.",
            )

        server.url = url

    if payload.enabled is not None:
        server.enabled = payload.enabled

    if payload.headers is not None:
        if payload.headers and not server.url.startswith("https://"):
            raise HTTPException(
                status_code=400,
                detail="Upstream credentials require an HTTPS URL.",
            )

        for header_name, header_value in payload.headers.items():
            if (
                not header_name
                or "\r" in header_name
                or "\n" in header_name
                or "\r" in header_value
                or "\n" in header_value
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid header name or value.",
                )

        server.headers_json = (
            json.dumps(payload.headers) if payload.headers else None
        )

    try:
        db.commit()
        db.refresh(server)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update the upstream configuration.",
        )

    try:
        await refresh_tool_registry()
    except Exception as exc:
        print(
            f"Warning: upstream registry refresh failed: {exc}",
            flush=True,
        )

    return serialize_upstream(server)


@app.patch("/admin/upstreams/{name}/enabled")
async def admin_set_upstream_enabled(
    name: str,
    payload: UpstreamEnabledRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    server = (
        db.query(UpstreamServer)
        .filter(UpstreamServer.name == name)
        .first()
    )

    if server is None:
        raise HTTPException(status_code=404, detail="Upstream server not found.")

    server.enabled = payload.enabled

    try:
        db.commit()
        db.refresh(server)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not change the upstream enabled state.",
        )

    try:
        await refresh_tool_registry()
    except Exception as exc:
        print(
            f"Warning: upstream registry refresh failed: {exc}",
            flush=True,
        )

    return serialize_upstream(server)


@app.delete("/admin/upstreams/{name}")
async def admin_delete_upstream(
    name: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    server = (
        db.query(UpstreamServer)
        .filter(UpstreamServer.name == name)
        .first()
    )

    if server is None:
        raise HTTPException(status_code=404, detail="Upstream server not found.")

    db.delete(server)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete the upstream configuration.",
        )

    try:
        await refresh_tool_registry()
    except Exception as exc:
        print(
            f"Warning: upstream registry refresh failed: {exc}",
            flush=True,
        )

    return {"message": "Upstream server deleted.", "name": name}


# --------------------------------------------------
# ADMIN: CREATE TEAM MEMBERS
# --------------------------------------------------

@app.get("/admin/users")
async def list_team_members(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.asc()).all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in users
    ]

@app.post("/admin/users", status_code=201)
async def create_member(
    payload: dict,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from app.auth_service import create_user

    email = str(payload.get("email", "")).strip().lower()

    try:
        member = create_user(
            db=db,
            email=email,
            role="member",
        )
        return {
            "id": member.id,
            "email": member.email,
            "role": member.role,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# --------------------------------------------------
# API KEY MANAGEMENT
# --------------------------------------------------

@app.get("/keys")
async def list_api_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(APIKey)

    if user.role != "admin":
        query = query.filter(APIKey.user_id == user.id)

    keys = query.order_by(APIKey.id.desc()).all()

    return [
        {
            "id": key.id,
            "name": key.name,
            "user_id": key.user_id,
            "key_prefix": key.key_prefix,
            "is_active": key.is_active,
            "created_at": key.created_at.isoformat() if key.created_at else None,
            "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
        }
        for key in keys
    ]

@app.post("/keys", status_code=201)
async def create_api_key(
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.auth_service import issue_api_key

    name = str(payload.get("name", "")).strip()
    requested_user_id = payload.get("user_id")

    # Only administrators may create keys for other users.
    if user.role == "admin":
        if requested_user_id is not None:
            try:
                target_user_id = int(requested_user_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail="user_id must be an integer.",
                )
        else:
            target_user_id = user.id
    else:
        # Members can create keys only for themselves.
        if requested_user_id is not None:
            try:
                requested_user_id = int(requested_user_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail="user_id must be an integer.",
                )

            if requested_user_id != user.id:
                raise HTTPException(
                    status_code=403,
                    detail="Members can only create API keys for themselves.",
                )

        target_user_id = user.id

    try:
        record, raw_key = issue_api_key(
            db=db,
            user_id=target_user_id,
            name=name,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "id": record.id,
        "name": record.name,
        "user_id": record.user_id,
        "key": raw_key,
        "message": "Store this key securely; it will not be shown again.",
    }

@app.post("/keys/{key_id}/revoke")
async def revoke_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.auth_service import revoke_api_key

    try:
        revoked = revoke_api_key(
            db=db,
            key_id=key_id,
            requesting_user=user,
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=403,
            detail=str(error),
        )

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail="Active API key not found.",
        )

    return {
        "message": "API key revoked successfully.",
        "key_id": key_id,
    }


# --------------------------------------------------
# ADMIN: VIEW AUDIT LOGS
# --------------------------------------------------

@app.get("/admin/audit-logs")
async def list_audit_logs(
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 500))

    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "server": log.server,
            "tool": log.tool,
            "timestamp": log.timestamp.isoformat(),
            "duration_ms": log.duration_ms,
            "outcome": log.outcome,
            "error_message": log.error_message,
        }
        for log in logs
    ]


# --------------------------------------------------
# EXTERNAL MCP ENDPOINT
# --------------------------------------------------
# External MCP clients must use the gateway URL and a user API key.
# The upstream WooCommerce MCP URL and credentials remain server-side.
from app.mcp_gateway import mcp_asgi_app  # noqa: E402

app.mount("/mcp", mcp_asgi_app)
