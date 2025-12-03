#!/bin/bash
# Start Claude Code CLI with strict MCP config
# This ensures only the composio_router_2 MCP server is loaded

echo "Starting Claude Code CLI with Composio MCP server..."
echo ""
echo "MCP Server: composio_router_2"
echo "URL: http://localhost:8001/v1/mcp/router"
echo ""

# Resolve MCP config path (handles WSL, Git Bash, Windows paths)
resolve_config_path() {
    local path="$1"

    # If path exists as-is, use it
    if [ -n "$path" ] && [ -f "$path" ]; then
        echo "$path"
        return
    fi

    # If path is WSL-style /mnt/c/... but missing, try /c/...
    if [[ "$path" == /mnt/c/* ]]; then
        local alt="/c${path#/mnt/c}"
        [ -f "$alt" ] && echo "$alt" && return
    fi

    # If path is Git Bash style /c/... but missing, try /mnt/c/...
    if [[ "$path" == /c/* ]]; then
        local alt="/mnt${path}"
        [ -f "$alt" ] && echo "$alt" && return
    fi

    # If Windows-style C:\... convert to /mnt/c/...
    if [[ "$path" =~ ^[A-Za-z]:\\\\ ]]; then
        local drive_lower
        drive_lower=$(echo "${path:0:1}" | tr 'A-Z' 'a-z')
        local converted="/mnt/${drive_lower}${path:2}"
        converted=${converted//\\\\//}
        [ -f "$converted" ] && echo "$converted" && return
    fi

    # No match
    echo ""
}

resolved=""

# Prefer user-specified path if provided
if [ -n "$MCP_CONFIG_PATH" ]; then
    resolved=$(resolve_config_path "$MCP_CONFIG_PATH")
fi

# Otherwise try common locations
if [ -z "$resolved" ]; then
    for candidate in "/mnt/c/Users/memor/.mcp.json" "/c/Users/memor/.mcp.json" "$HOME/.mcp.json"; do
        resolved=$(resolve_config_path "$candidate")
        [ -n "$resolved" ] && break
    done
fi

if [ -z "$resolved" ]; then
    echo "❌ Could not find MCP config file."
    echo "   Looked in /mnt/c/Users/memor/.mcp.json, /c/Users/memor/.mcp.json, and $HOME/.mcp.json"
    echo "   Set MCP_CONFIG_PATH to the correct location and retry."
    exit 1
fi

MCP_CONFIG_PATH="$resolved"

echo "Using MCP config: $MCP_CONFIG_PATH"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Backend server doesn't appear to be running on port 8001"
    echo "   Make sure your backend is started before using MCP tools"
    echo ""
fi

# Start Claude Code with strict MCP config
npx @anthropic-ai/claude-code --strict-mcp-config --mcp-config "$MCP_CONFIG_PATH"
