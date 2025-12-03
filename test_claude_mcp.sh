#!/bin/bash
# Test Claude Code CLI with MCP connection

echo "Testing Claude Code CLI MCP connection..."
echo ""
echo "This will start Claude Code CLI and test the Composio tools."
echo ""

# Create a test prompt
TEST_PROMPT="Please tell me: What MCP servers do you have access to? List the server names only."

echo "Sending test prompt to Claude Code CLI..."
echo ""

# Run Claude Code CLI with the test prompt
# Using --continue mode and one-shot prompt
npx @anthropic-ai/claude-code --continue "$TEST_PROMPT"

echo ""
echo "If you see 'composio_router_2' in the output above, the MCP connection is working!"
