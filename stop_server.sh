#!/bin/bash

# POP Mail MCP Server Manual Stop Script
# Created: 2025-07-26 19:51:00
# Purpose: Manually stop the POP Mail MCP Server

set -e  # Exit on any error

echo "=== Stopping POP Mail MCP Server ==="
echo "Date: $(date)"
echo ""

# Function to stop systemd service
stop_systemd_service() {
    if systemctl is-active --quiet popmailmcp 2>/dev/null; then
        echo "Stopping systemd service..."
        systemctl stop popmailmcp
        echo "✓ Systemd service stopped"
        return 0
    else
        echo "Systemd service is not running"
        return 1
    fi
}

# Function to stop manual processes
stop_manual_processes() {
    local pids=$(pgrep -f "mail_mcp.py" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "Found running POP Mail MCP processes: $pids"
        echo "Sending SIGTERM to processes..."
        
        # Send SIGTERM first (graceful shutdown)
        echo "$pids" | xargs -r kill -TERM
        
        # Wait a few seconds for graceful shutdown
        sleep 3
        
        # Check if processes are still running
        local remaining_pids=$(pgrep -f "mail_mcp.py" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo "Some processes still running. Sending SIGKILL..."
            echo "$remaining_pids" | xargs -r kill -KILL
            sleep 1
        fi
        
        # Final check
        local final_pids=$(pgrep -f "mail_mcp.py" 2>/dev/null || true)
        if [ -z "$final_pids" ]; then
            echo "✓ All POP Mail MCP processes stopped"
            return 0
        else
            echo "✗ Some processes could not be stopped: $final_pids"
            return 1
        fi
    else
        echo "No manual POP Mail MCP processes found"
        return 1
    fi
}

# Try to stop systemd service first
systemd_stopped=false
manual_stopped=false

if stop_systemd_service; then
    systemd_stopped=true
fi

# Try to stop manual processes
if stop_manual_processes; then
    manual_stopped=true
fi

# Summary
echo ""
if [ "$systemd_stopped" = true ] || [ "$manual_stopped" = true ]; then
    echo "=== POP Mail MCP Server Stopped Successfully ==="
    
    # Show final status
    echo ""
    echo "Final Status Check:"
    if pgrep -f "mail_mcp.py" > /dev/null; then
        echo "✗ WARNING: Some processes may still be running:"
        pgrep -f "mail_mcp.py" | while read pid; do
            echo "  PID $pid: $(ps -p $pid -o cmd= 2>/dev/null || echo 'Process info unavailable')"
        done
    else
        echo "✓ No POP Mail MCP processes detected"
    fi
    
    if systemctl is-active --quiet popmailmcp 2>/dev/null; then
        echo "✗ WARNING: Systemd service still appears active"
        echo "  Status: $(systemctl is-active popmailmcp 2>/dev/null || echo 'unknown')"
    else
        echo "✓ Systemd service is inactive"
    fi
    
else
    echo "=== No POP Mail MCP Server Processes Found ==="
    echo "The server was not running (neither as systemd service nor manual process)"
fi

echo ""
