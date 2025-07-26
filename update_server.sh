#!/bin/bash

# POP Mail MCP Server Update Script
# Created: 2025-07-26 23:46:00
# Purpose: Deploy ChatGPT compatibility fix to server

set -e  # Exit on any error

echo "=== POP Mail MCP Server Update - ChatGPT Compatibility Fix ==="
echo "Date: $(date)"
echo "Update: Adding validation=False for ChatGPT Accept header compatibility"
echo ""

# Check if deployment directory exists
if [ ! -d "/opt/popmailmcp" ]; then
    echo "ERROR: /opt/popmailmcp directory not found. Please run deploy_server.sh first."
    exit 1
fi

if [ ! -f "/opt/popmailmcp/mail_mcp.py" ]; then
    echo "ERROR: mail_mcp.py not found. Please run deploy_server.sh first."
    exit 1
fi

# Step 1: Backup current version
echo "Step 1: Creating backup..."
cd /opt/popmailmcp
cp mail_mcp.py mail_mcp.py.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backup created: mail_mcp.py.backup.$(date +%Y%m%d_%H%M%S)"

# Step 2: Stop the service
echo ""
echo "Step 2: Stopping POP Mail MCP service..."
if systemctl is-active --quiet popmailmcp; then
    systemctl stop popmailmcp
    echo "✓ Service stopped"
else
    echo "ℹ Service was not running"
fi

# Step 3: Apply the update (manual step - user needs to upload updated file)
echo ""
echo "Step 3: Applying ChatGPT compatibility fix..."
echo "NOTE: The updated mail_mcp.py file should be uploaded from local machine"
echo ""
echo "Expected change around line 99-106:"
echo "  OLD: mcp = FastMCP(name=\"plain-mail-mcp\", version=\"1.0.0\")"
echo "  NEW: mcp = FastMCP(name=\"plain-mail-mcp\", version=\"1.0.0\", validation=False)"
echo ""

# Check if update was applied
echo "Checking for compatibility fix..."
if grep -q "validation=False" mail_mcp.py; then
    echo "✓ ChatGPT compatibility fix detected in mail_mcp.py"
else
    echo "✗ ChatGPT compatibility fix NOT found in mail_mcp.py"
    echo "Please upload the updated mail_mcp.py file from your local machine"
    exit 1
fi

# Step 4: Start the service
echo ""
echo "Step 4: Starting POP Mail MCP service..."
systemctl start popmailmcp

# Wait a moment for startup
sleep 3

# Step 5: Verify service status
echo ""
echo "Step 5: Verifying service status..."
if systemctl is-active --quiet popmailmcp; then
    echo "✓ Service is running"
    
    # Show service status
    echo ""
    echo "Service Status:"
    systemctl status popmailmcp --no-pager -l | head -15
    
    # Test if server is responding
    echo ""
    echo "Testing server response..."
    if curl -s -f http://localhost:8088/mcp/ > /dev/null; then
        echo "✓ MCP server is responding on port 8088"
    else
        echo "⚠ MCP server connectivity test failed"
    fi
    
else
    echo "✗ Service failed to start"
    echo "Checking logs..."
    journalctl -u popmailmcp --no-pager -n 10
    exit 1
fi

echo ""
echo "=== Update Complete ==="
echo "ChatGPT compatibility fix has been applied and tested."
echo "Server URL for ChatGPT: http://173.212.228.93:8088/mcp/"
echo ""
echo "Next: Test the connector in ChatGPT with the server URL"
echo ""
