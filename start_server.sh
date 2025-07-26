#!/bin/bash

# POP Mail MCP Server Manual Start Script
# Created: 2025-07-26 19:51:00
# Purpose: Manually start the POP Mail MCP Server (alternative to systemd)

set -e  # Exit on any error

echo "=== Starting POP Mail MCP Server ==="
echo "Date: $(date)"
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

# Change to deployment directory
cd /opt/popmailmcp

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Please run deploy_server.sh first."
    exit 1
fi

# Check if already running via systemd
if systemctl is-active --quiet popmailmcp 2>/dev/null; then
    echo "WARNING: POP Mail MCP Server is already running as a systemd service."
    echo "To use manual control, first stop the systemd service:"
    echo "  systemctl stop popmailmcp"
    echo "  systemctl disable popmailmcp"
    echo ""
    read -p "Do you want to stop the systemd service and continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl stop popmailmcp
        echo "✓ Systemd service stopped"
    else
        echo "Aborted."
        exit 1
    fi
fi

# Check if process is already running manually
if pgrep -f "mail_mcp.py" > /dev/null; then
    echo "WARNING: POP Mail MCP Server appears to be already running."
    echo "Process IDs: $(pgrep -f 'mail_mcp.py')"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    set -a
    source .env
    set +a
elif [ -f ".env.service" ]; then
    echo "Loading environment variables from .env.service..."
    set -a
    source .env.service
    set +a
else
    echo "No environment file found (.env or .env.service)"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo ""
echo "Starting POP Mail MCP Server..."
echo "Working Directory: $(pwd)"
echo "Python Version: $(python --version)"
echo "Log file: logs/popmailmcp.log"
echo ""
echo "Starting server... (Press Ctrl+C to stop)"
echo "=========================="

# Start the server with logging
python mail_mcp.py 2>&1 | tee logs/popmailmcp.log

echo ""
echo "=== POP Mail MCP Server Stopped ==="
