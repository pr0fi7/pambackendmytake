#!/bin/bash
# Update MCP configuration with fresh token

echo "Logging in to get fresh access token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@harmix.ai","password":"testpassword123"}')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token"
  exit 1
fi

echo "Access token obtained: ${ACCESS_TOKEN:0:50}..."

# Update .mcp.json
cat > .mcp.json <<EOF
{
  "mcpServers": {
    "composio_router": {
      "url": "http://127.0.0.1:8000/v1/mcp/router",
      "headers": {
        "Authorization": "Bearer $ACCESS_TOKEN",
        "api-key": "3fgNeQWgkEUdKMnrVw69BQfNkJRpYA"
      }
    }
  }
}
EOF

echo "✅ .mcp.json updated with fresh token"
echo ""
echo "Now restart Claude Code or run the /mcp command to connect"
