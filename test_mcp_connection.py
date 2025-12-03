#!/usr/bin/env python3
"""Test MCP connection like Claude Code CLI would"""
import json
import httpx
import asyncio

async def test_mcp_connection():
    def find_config_path() -> str:
        """Find .mcp.json across WSL/Windows locations."""
        candidates = [
            os.environ.get("MCP_CONFIG_PATH"),
            "/mnt/c/Users/memor/.mcp.json",  # WSL path to Windows home
            "/c/Users/memor/.mcp.json",      # Git Bash style path
            os.path.expanduser("~/.mcp.json"),
            r"C:\Users\memor\.mcp.json",
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return path
        raise FileNotFoundError("Could not find .mcp.json; set MCP_CONFIG_PATH to override")

    # Read config
    config_path = find_config_path()
    with open(config_path, "r") as f:
        config = json.load(f)

    server_config = config['mcpServers']['composio_router_2']
    # Claude Code CLI expects flat format (not nested in transport)
    url = server_config['url']
    headers = server_config['headers']

    print(f"Testing connection to: {url}")
    print(f"Headers: {json.dumps({k: v[:20]+'...' if len(v) > 20 else v for k, v in headers.items()}, indent=2)}")
    print()

    # Test tools/list request (what Claude Code CLI does on connect)
    request_body = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Sending tools/list request...")
            response = await client.post(
                url,
                json=request_body,
                headers=headers
            )

            print(f"Status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print()

            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'tools' in data['result']:
                    tools = data['result']['tools']
                    print(f"SUCCESS! Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"  - {tool['name']}")
                else:
                    print(f"ERROR: Unexpected response format: {json.dumps(data, indent=2)[:500]}")
            else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"ERROR: Connection error using config at {config_path}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
