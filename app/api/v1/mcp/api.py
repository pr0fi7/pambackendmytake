"""
MCP (Model Context Protocol) Endpoint
Provides tools from connected integrations to Claude CLI sessions
"""

import json
import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.auth import AuthDependencies
from app.container import ApplicationContainer
from app.services.auth.auth_service import AuthService
from app.services.mcp.mcp_service import MCPService

router = APIRouter(prefix="/mcp")
logger = logging.getLogger(__name__)


@router.get("")
@inject
async def get_mcp_config(
    token: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    deps: AuthDependencies = Depends(Provide[ApplicationContainer.auth_deps]),
    mcp_service: MCPService = Depends(Provide[ApplicationContainer.mcp_service]),
):
    """
    Get MCP configuration for Claude Code sessions.

    Returns the MCP server configuration that can be used with Claude Code CLI
    to enable tool access from connected integrations.

    The configuration uses the tool router endpoint by default for better output formatting.
    """
    # Get user from token
    user_id = deps.require_access_token_user_id(token)

    # Get the access token from the credentials
    access_token = token.credentials if token else None

    if not access_token:
        return Response(
            json.dumps({
                "error": "Access token is required"
            }),
            media_type="application/json",
            status_code=401
        )

    # Get MCP config from service
    mcp_config = mcp_service.get_mcp_config(access_token=access_token, user_id=user_id)

    return Response(
        json.dumps(mcp_config, indent=2),
        media_type="application/json"
    )


@router.post("/router")
@inject
async def mcp_tool_router(
    request: Request,
    token: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    deps: AuthDependencies = Depends(Provide[ApplicationContainer.auth_deps]),
    auth_service: AuthService = Depends(Provide[ApplicationContainer.auth_service]),
    mcp_service: MCPService = Depends(Provide[ApplicationContainer.mcp_service]),
):
    """
    MCP Tool Router endpoint - Uses Composio's experimental tool router for better formatting.

    This endpoint creates a tool router session and proxies all MCP requests to it.
    The tool router provides improved output formatting and handling compared to direct tool execution.

    Architecture B from server_db.py - Tool Router approach.
    """
    # Get user from token
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)

    if not user:
        return Response(
            json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "Unknown user"},
            }),
            media_type="application/json",
        )

    # Get Composio entity ID
    composio_entity_id = user.composio_entity_id
    if not composio_entity_id:
        return Response(
            json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "User not configured for Composio"},
            }),
            media_type="application/json",
        )

    # Parse request body
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Parse error in tool router: {e}")
        return Response(
            json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
            }),
            media_type="application/json",
        )

    # Handle request via service
    response_data, status_code = await mcp_service.handle_tool_router_request(
        user_id=user_id,
        composio_entity_id=composio_entity_id,
        request_body=body,
        accept_header=request.headers.get("accept", "application/json")
    )

    return Response(
        json.dumps(response_data),
        media_type="application/json",
        status_code=status_code
    )


@router.delete("/session")
@inject
async def clear_mcp_session(
    token: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    deps: AuthDependencies = Depends(Provide[ApplicationContainer.auth_deps]),
    mcp_service: MCPService = Depends(Provide[ApplicationContainer.mcp_service]),
):
    """
    Clear the cached MCP tool router session for the current user.

    This endpoint can be used to force recreation of the tool router session,
    which is useful if the session becomes stale or expired.
    """
    # Get user from token
    user_id = deps.require_access_token_user_id(token)

    # Clear the session
    cleared = await mcp_service.clear_session(user_id)

    return Response(
        json.dumps({
            "success": cleared,
            "message": "Session cleared" if cleared else "No session found"
        }),
        media_type="application/json",
        status_code=200
    )
