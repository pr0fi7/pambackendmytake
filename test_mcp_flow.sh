#!/bin/bash
# MCP Integration Test Script
# This script demonstrates the complete flow of MCP integration

echo "================================"
echo "MCP Integration Test Flow"
echo "================================"
echo ""

# Step 1: Login
echo "Step 1: Login to get access token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@harmix.ai","password":"testpassword123"}')

# Extract access token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Login failed!"
  exit 1
fi

echo "✅ Login successful!"
echo "   Access Token: ${ACCESS_TOKEN:0:50}..."
echo ""

# Step 2: Get MCP Configuration
echo "Step 2: Get MCP configuration..."
MCP_CONFIG=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8000/v1/mcp)

if [ -z "$MCP_CONFIG" ]; then
  echo "❌ Failed to get MCP config!"
  exit 1
fi

echo "✅ MCP configuration retrieved!"
echo ""

# Step 3: Save MCP config to file
echo "Step 3: Save MCP config to ~/.mcp.json and .claude.json..."
echo "$MCP_CONFIG" > ~/.mcp.json

# Also update .claude.json for this project
python << 'ENDPY'
import json
import os

# Read .claude.json
claude_config_path = os.path.expanduser('~/.claude.json')
mcp_config_path = os.path.expanduser('~/.mcp.json')

with open(claude_config_path, 'r') as f:
    claude_config = json.load(f)

with open(mcp_config_path, 'r') as f:
    mcp_config = json.load(f)

# Update the project's MCP server config
project_path = r"C:\Users\memor\Desktop\my_projects\harmixpam_backendapi"
if project_path in claude_config.get('projects', {}):
    claude_config['projects'][project_path]['mcpServers'] = mcp_config['mcpServers']

    with open(claude_config_path, 'w') as f:
        json.dump(claude_config, f, indent=2)

    print("   Updated .claude.json for project")
ENDPY

echo "✅ MCP config saved to .mcp.json and .claude.json"
echo ""

# Step 4: Test MCP Router
echo "Step 4: Test MCP router (tools/list)..."
TOOLS_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/mcp/router \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}')

TOOLS_COUNT=$(echo "$TOOLS_RESPONSE" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('result', {}).get('tools', [])))" 2>/dev/null)

if [ "$TOOLS_COUNT" -gt 0 ]; then
  echo "✅ MCP router working! Found $TOOLS_COUNT tools:"
  echo "$TOOLS_RESPONSE" | python -c "import sys, json; data=json.load(sys.stdin); [print(f'   - {t[\"name\"]}') for t in data.get('result', {}).get('tools', [])]" 2>/dev/null
else
  echo "❌ MCP router failed!"
  echo "Response: $TOOLS_RESPONSE"
  exit 1
fi
