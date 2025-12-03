"""
MCP (Model Context Protocol) Service
Handles MCP configuration generation and tool router session management
"""

import asyncio
import logging
from typing import Any, Dict

from composio import Composio

from app.config import settings
from app.services.messages.claude_cli import AsyncClaudeCLI

logger = logging.getLogger(__name__)

# Cache for tool router sessions (user_id -> session) with thread safety
_tool_router_sessions: Dict[int, Any] = {}
_sessions_lock = asyncio.Lock()


class MCPService:
    """Service for managing MCP configurations and tool router sessions."""

    def __init__(self):
        self._composio_client: Composio | None = None

    @property
    def composio(self) -> Composio:
        """Lazy-load Composio client."""
        if self._composio_client is None:
            self._composio_client = Composio(api_key=settings.COMPOSIO_API_KEY)
        return self._composio_client

    def get_mcp_config(self, access_token: str, user_id: int) -> dict:
        """
        Get MCP configuration for Claude Code sessions.

        Returns the MCP server configuration that can be used with Claude Code CLI
        to enable tool access from connected integrations.

        The configuration uses the tool router endpoint by default for better output formatting.

        Args:
            access_token: User's JWT access token
            user_id: User ID

        Returns:
            MCP configuration dict
        """
        mcp_config = AsyncClaudeCLI.create_mcp_config_with_tool_router(
            api_url=settings.API_URL,
            access_token=access_token,
            api_key=settings.HARMIX_API_KEY,
            user_id=user_id
        )

        logger.info(f"Generated MCP config for user {user_id}")
        return mcp_config

    async def handle_tool_router_request(
        self,
        user_id: int,
        composio_entity_id: str,
        request_body: dict,
        accept_header: str = "application/json"
    ) -> tuple[dict, int]:
        """
        Handle MCP tool router request.

        Uses Composio's experimental tool router for better formatting.
        Creates or reuses a tool router session and proxies the MCP request to it.

        Args:
            user_id: User ID
            composio_entity_id: User's Composio entity ID
            request_body: MCP request body (JSON-RPC format)
            accept_header: Accept header from the original request

        Returns:
            Tuple of (response_dict, status_code)
        """
        method = request_body.get("method")
        req_id = request_body.get("id")
        logger.info(f"Tool Router MCP request from user {user_id}: method={method}, id={req_id}")

        # Create or get existing tool router session with thread safety
        session = None
        try:
            async with _sessions_lock:
                if user_id not in _tool_router_sessions:
                    # Get connected toolkits for user
                    accounts = self.composio.connected_accounts.list(user_ids=[composio_entity_id])
                    connected_toolkits = []
                    for acc in accounts.items:
                        if hasattr(acc, "toolkit") and hasattr(acc.toolkit, "slug"):
                            toolkit_slug = acc.toolkit.slug.lower()
                            if toolkit_slug not in connected_toolkits:
                                connected_toolkits.append(toolkit_slug)

                    if not connected_toolkits:
                        return {
                            "jsonrpc": "2.0",
                            "error": {"code": -32602, "message": "No connected integrations found"},
                        }, 200

                    logger.info(f"Creating tool router session for user {user_id} with toolkits: {connected_toolkits}")

                    # Create tool router session
                    session = self.composio.experimental.tool_router.create_session(
                        user_id=composio_entity_id,
                        toolkits=connected_toolkits,
                        manually_manage_connections=True
                    )

                    _tool_router_sessions[user_id] = session
                    logger.info(f"Tool router session created: {session.session_id}")
                else:
                    session = _tool_router_sessions[user_id]

        except Exception as e:
            logger.error(f"Failed to create/get tool router session: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            }, 500

        # Forward the request to the tool router session with retry logic
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                import httpx
    
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        session.url,
                        json=request_body,
                        headers={"Accept": accept_header},
                        timeout=60.0
                    )
    
                    # Parse response - handle both JSON and SSE formats
                    try:
                        # Check if response is SSE format (starts with "event:" or "data:")
                        response_text = response.text
                        if response_text.startswith(("event:", "data:")):
                            # Parse SSE format - extract JSON from data: lines
                            import json as json_lib
                            for line in response_text.split('\n'):
                                if line.startswith('data: '):
                                    json_str = line[6:]  # Remove 'data: ' prefix
                                    response_data = json_lib.loads(json_str)
                                    break
                            else:
                                response_data = {"error": "No valid data found in SSE response"}
                        else:
                            # Regular JSON response
                            response_data = response.json()
                    except Exception as e:
                        logger.error(f"Failed to parse response: {e}")
                        logger.error(f"Response status: {response.status_code}")
                        logger.error(f"Response content: {response.text[:500]}")
                        response_data = {"error": "Failed to parse response", "details": str(e)}
    
                    return response_data, response.status_code
    
            except Exception as e:
            logger.error(f"Error forwarding to tool router: {e}")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": f"Tool router error: {str(e)}"},
            }, 500
