#!/bin/bash

# POP Mail MCP Server Status Check Script
# Created: 2025-07-26 19:51:00
# Purpose: Check status and health of POP Mail MCP Server

echo "=== POP Mail MCP Server Status Check ==="
echo "Date: $(date)"
echo ""

# Function to check systemd service status
check_systemd_status() {
    echo "1. Systemd Service Status:"
    echo "-------------------------"
    
    if systemctl list-units --type=service | grep -q popmailmcp; then
        local status=$(systemctl is-active popmailmcp 2>/dev/null || echo "unknown")
        local enabled=$(systemctl is-enabled popmailmcp 2>/dev/null || echo "unknown")
        
        echo "  Service exists: Yes"
        echo "  Active status: $status"
        echo "  Enabled status: $enabled"
        
        if [ "$status" = "active" ]; then
            echo "  ✓ Service is running"
            # Get service details
            echo ""
            echo "  Service Details:"
            systemctl status popmailmcp --no-pager -l | head -10
        else
            echo "  ✗ Service is not active"
        fi
    else
        echo "  Service exists: No"
        echo "  ✗ Systemd service not found"
    fi
    echo ""
}

# Function to check manual processes
check_manual_processes() {
    echo "2. Manual Process Status:"
    echo "------------------------"
    
    local pids=$(pgrep -f "mail_mcp.py" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "  Running processes: Yes"
        echo "  Process IDs: $pids"
        echo ""
        echo "  Process Details:"
        echo "$pids" | while read pid; do
            if [ -n "$pid" ]; then
                echo "    PID $pid:"
                ps -p $pid -o pid,ppid,cmd,etime,pcpu,pmem --no-headers 2>/dev/null || echo "      Process info unavailable"
            fi
        done
        echo "  ✓ Manual processes found"
    else
        echo "  Running processes: No"
        echo "  ✗ No manual processes found"
    fi
    echo ""
}

# Function to check deployment directory
check_deployment() {
    echo "3. Deployment Status:"
    echo "--------------------"
    
    if [ -d "/opt/popmailmcp" ]; then
        echo "  Deployment directory: ✓ /opt/popmailmcp exists"
        
        if [ -f "/opt/popmailmcp/mail_mcp.py" ]; then
            echo "  Main server file: ✓ mail_mcp.py found"
        else
            echo "  Main server file: ✗ mail_mcp.py missing"
        fi
        
        if [ -d "/opt/popmailmcp/venv" ]; then
            echo "  Virtual environment: ✓ venv directory found"
            
            if [ -f "/opt/popmailmcp/venv/bin/python" ]; then
                local python_version=$(/opt/popmailmcp/venv/bin/python --version 2>/dev/null || echo "Unknown")
                echo "  Python version: $python_version"
            fi
        else
            echo "  Virtual environment: ✗ venv directory missing"
        fi
        
        if [ -f "/opt/popmailmcp/requirements.txt" ]; then
            echo "  Requirements file: ✓ requirements.txt found"
        else
            echo "  Requirements file: ✗ requirements.txt missing"
        fi
        
        if [ -f "/opt/popmailmcp/.env" ] || [ -f "/opt/popmailmcp/.env.service" ]; then
            echo "  Environment config: ✓ Found"
        else
            echo "  Environment config: ⚠ No .env or .env.service file found"
        fi
        
    else
        echo "  Deployment directory: ✗ /opt/popmailmcp missing"
        echo "  ✗ Server not deployed"
    fi
    echo ""
}

# Function to check ports and network
check_network() {
    echo "4. Network Status:"
    echo "-----------------"
    
    # Check if any Python processes are listening on common MCP ports
    local listening_ports=$(netstat -tlnp 2>/dev/null | grep python || true)
    if [ -n "$listening_ports" ]; then
        echo "  Python processes listening on ports:"
        echo "$listening_ports" | while read line; do
            echo "    $line"
        done
        echo "  ✓ Network listeners found"
    else
        echo "  Python network listeners: None found"
        echo "  ⚠ No Python processes listening on ports"
    fi
    echo ""
}

# Function to check recent logs
check_logs() {
    echo "5. Recent Logs:"
    echo "--------------"
    
    # Check systemd logs
    if systemctl list-units --type=service | grep -q popmailmcp; then
        echo "  Systemd Logs (last 5 entries):"
        journalctl -u popmailmcp --no-pager -n 5 --since "1 hour ago" 2>/dev/null || echo "    No recent systemd logs"
        echo ""
    fi
    
    # Check manual logs
    if [ -f "/opt/popmailmcp/logs/popmailmcp.log" ]; then
        echo "  Manual Logs (last 5 lines):"
        tail -5 /opt/popmailmcp/logs/popmailmcp.log 2>/dev/null || echo "    Cannot read log file"
    else
        echo "  Manual Logs: No log file found at /opt/popmailmcp/logs/popmailmcp.log"
    fi
    echo ""
}

# Function to provide overall health summary
health_summary() {
    echo "6. Overall Health Summary:"
    echo "-------------------------"
    
    local health_score=0
    local max_score=5
    
    # Check deployment
    if [ -d "/opt/popmailmcp" ] && [ -f "/opt/popmailmcp/mail_mcp.py" ]; then
        health_score=$((health_score + 1))
        echo "  ✓ Deployment: OK"
    else
        echo "  ✗ Deployment: Missing"
    fi
    
    # Check virtual environment
    if [ -d "/opt/popmailmcp/venv" ]; then
        health_score=$((health_score + 1))
        echo "  ✓ Virtual Environment: OK"
    else
        echo "  ✗ Virtual Environment: Missing"
    fi
    
    # Check if running (systemd or manual)
    if systemctl is-active --quiet popmailmcp 2>/dev/null || pgrep -f "mail_mcp.py" > /dev/null; then
        health_score=$((health_score + 1))
        echo "  ✓ Process: Running"
    else
        echo "  ✗ Process: Not Running"
    fi
    
    # Check systemd configuration
    if systemctl list-units --type=service | grep -q popmailmcp; then
        health_score=$((health_score + 1))
        echo "  ✓ Systemd Service: Configured"
    else
        echo "  ⚠ Systemd Service: Not Configured"
    fi
    
    # Check environment configuration
    if [ -f "/opt/popmailmcp/.env" ] || [ -f "/opt/popmailmcp/.env.service" ]; then
        health_score=$((health_score + 1))
        echo "  ✓ Environment Config: Present"
    else
        echo "  ⚠ Environment Config: Missing"
    fi
    
    echo ""
    echo "  Health Score: $health_score/$max_score"
    
    if [ $health_score -eq $max_score ]; then
        echo "  Status: ✓ EXCELLENT - All systems operational"
    elif [ $health_score -ge 3 ]; then
        echo "  Status: ⚠ GOOD - Minor issues detected"
    elif [ $health_score -ge 1 ]; then
        echo "  Status: ⚠ POOR - Significant issues detected"
    else
        echo "  Status: ✗ CRITICAL - System not operational"
    fi
}

# Run all checks
check_systemd_status
check_manual_processes
check_deployment
check_network
check_logs
health_summary

echo ""
echo "=== Status Check Complete ==="
echo ""
