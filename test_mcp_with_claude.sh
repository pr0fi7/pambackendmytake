#!/bin/bash
# Complete MCP Integration Test with Claude Code CLI
# This script tests the full flow including Claude Code CLI usage

echo "========================================"
echo "MCP Integration Test with Claude Code"
echo "========================================"
echo ""

# Step 1: Login
echo "Step 1: Login to get access token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8001/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@harmix.ai","password":"testpassword123"}')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Login failed!"
  exit 1
fi

echo "✅ Login successful!"
echo ""

# Step 2: Get and save MCP config
echo "Step 2: Save MCP configuration..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8001/v1/mcp > ~/.mcp.json
echo "✅ MCP config saved to ~/.mcp.json"
echo ""
echo "Config preview:"
cat ~/.mcp.json | python -m json.tool | head -20
echo ""

# Step 3: Verify MCP router
echo "Step 3: Verify MCP router..."
TOOLS_RESPONSE=$(curl -s -X POST http://localhost:8001/v1/mcp/router \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}')

TOOLS_COUNT=$(echo "$TOOLS_RESPONSE" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('result', {}).get('tools', [])))" 2>/dev/null)

if [ "$TOOLS_COUNT" -gt 0 ]; then
  echo "✅ MCP router working! Found $TOOLS_COUNT tools"
else
  echo "❌ MCP router failed!"
  exit 1
fi

echo ""
echo "========================================"
echo "✅ Backend tests passed!"
echo "========================================"
echo ""

# Step 4: Test with Claude Code CLI (if available)
echo "Step 4: Testing with Claude Code CLI..."
echo ""

# Check if claude-code is available (either in PATH or via npx)
if command -v claude-code &> /dev/null; then
    CLAUDE_CMD="claude-code"
    echo "✅ Claude Code CLI found in PATH!"
elif npx --yes @anthropic-ai/claude-code --version &> /dev/null; then
    CLAUDE_CMD="npx @anthropic-ai/claude-code"
    echo "✅ Claude Code CLI found via npx!"
else
    echo "⚠️  Claude Code CLI not found. Skipping CLI test."
    echo ""
    echo "To install Claude Code CLI:"
    echo "  npm install -g @anthropic-ai/claude-code"
    echo ""
    echo "After installation, run this script again to test the full flow."
    CLAUDE_CMD=""
fi

if [ -n "$CLAUDE_CMD" ]; then
    echo "   Command: $CLAUDE_CMD"
    echo ""
    echo "Creating test prompt for Claude..."

    # Create a test file with the prompt
    cat > /tmp/claude_test_prompt.txt <<'EOF'
What tools do you have access to? Please list them.

Then, can you search for tools that can help me list my Gmail emails?
EOF

    echo ""
    echo "Test prompt saved to: /tmp/claude_test_prompt.txt"
    echo ""
    echo "Running Claude Code CLI test..."
    echo "This will start an interactive Claude session."
    echo "Claude should have access to Composio tools through MCP."
    echo ""
    echo "----------------------------------------"

    # Use expect to automate the Claude Code CLI interaction
    # Or just provide instructions for manual testing
    echo ""
    echo "📋 Manual Test Instructions:"
    echo ""
    echo "1. Open a new terminal and run:"
    echo "   $CLAUDE_CMD"
    echo ""
    echo "2. Verify Claude has access to tools:"
    echo "   > What tools do you have access to?"
    echo ""
    echo "   Expected: Claude should list COMPOSIO_SEARCH_TOOLS, COMPOSIO_MULTI_EXECUTE_TOOL, etc."
    echo ""
    echo "3. Test Gmail integration:"
    echo "   > Search for Gmail tools"
    echo ""
    echo "   Expected: Claude uses COMPOSIO_SEARCH_TOOLS to find Gmail-related tools"
    echo ""
    echo "4. List recent emails:"
    echo "   > List my 5 most recent Gmail emails"
    echo ""
    echo "   Expected: Claude uses COMPOSIO_MULTI_EXECUTE_TOOL with GMAIL_FETCH_EMAILS"
    echo ""
    echo "5. Other use cases to test:"
    echo "   - 'Send an email to test@example.com saying Hello'"
    echo "   - 'Search my emails for messages from yesterday'"
    echo "   - 'What Slack channels do I have access to?'"
    echo "   - 'Create a Google Calendar event for tomorrow at 2pm'"
    echo ""
fi

echo "========================================"
echo "📝 Quick Reference"
echo "========================================"
echo ""
echo "MCP Config Location: ~/.mcp.json"
echo "Backend Server: http://localhost:8001"
echo ""
echo "Test Commands:"
echo ""
echo "1. Verify server is running:"
echo "   curl http://localhost:8001/health"
echo ""
echo "2. Get MCP config:"
echo "   curl -H \"Authorization: Bearer \$ACCESS_TOKEN\" http://localhost:8001/v1/mcp"
echo ""
echo "3. Test tools/list:"
echo "   curl -X POST http://localhost:8001/v1/mcp/router \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -H \"Accept: application/json, text/event-stream\" \\"
echo "     -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "     -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'"
echo ""
echo "4. Start Claude Code:"
echo "   npx @anthropic-ai/claude-code"
echo "   (or 'claude-code' if in PATH)"
echo ""
echo "========================================"
echo "Example Use Cases with Claude Code"
echo "========================================"
echo ""
echo "📧 Gmail:"
echo "  - 'List my 10 most recent emails'"
echo "  - 'Search emails from john@example.com'"
echo "  - 'Send an email to alice@example.com'"
echo ""
echo "💬 Slack:"
echo "  - 'What Slack channels am I in?'"
echo "  - 'Send a message to #general channel'"
echo "  - 'Search Slack for messages about the project'"
echo ""
echo "📅 Google Calendar:"
echo "  - 'What meetings do I have today?'"
echo "  - 'Create a meeting for tomorrow at 3pm'"
echo "  - 'List my calendar events for this week'"
echo ""
echo "📊 Google Sheets:"
echo "  - 'Read data from my spreadsheet'"
echo "  - 'Add a row to my sheet'"
echo "  - 'Create a new spreadsheet'"
echo ""
echo "💾 Google Drive:"
echo "  - 'List my recent files'"
echo "  - 'Search Drive for documents'"
echo "  - 'Share a file with someone'"
echo ""
echo "🔧 GitHub:"
echo "  - 'List my repositories'"
echo "  - 'Create an issue in my repo'"
echo "  - 'Search for pull requests'"
echo ""
echo "🌐 Web Search:"
echo "  - 'Search the web for latest AI news'"
echo "  - 'Find information about...'"
echo ""
