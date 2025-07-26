#!/bin/bash

# POP Mail MCP Server Systemd Service Setup Script
# Created: 2025-07-26 19:51:00
# Purpose: Configure systemd service for automatic startup of POP Mail MCP Server

set -e  # Exit on any error

echo "=== POP Mail MCP Systemd Service Setup ==="
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

# Step 1: Create systemd service file
echo "Step 1: Creating systemd service file..."
cat > /etc/systemd/system/popmailmcp.service << 'EOF'
[Unit]
Description=POP Mail MCP Server - FastMCP Server for Email Management
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=root
Group=root
WorkingDirectory=/opt/popmailmcp
Environment=PATH=/opt/popmailmcp/venv/bin
ExecStart=/opt/popmailmcp/venv/bin/python /opt/popmailmcp/mail_mcp.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=popmailmcp

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/opt/popmailmcp

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service file created at /etc/systemd/system/popmailmcp.service"

# Step 2: Create environment file for service
echo ""
echo "Step 2: Creating environment configuration..."
cat > /opt/popmailmcp/.env.service << 'EOF'
# POP Mail MCP Server Environment Configuration
# Created: 2025-07-26 19:51:00
# Add your environment variables here

# Example configurations (uncomment and modify as needed):
# EMAIL_SERVER=your.email.server.com
# EMAIL_PORT=995
# EMAIL_USERNAME=your-username
# EMAIL_PASSWORD=your-password
# LOG_LEVEL=INFO
# MCP_PORT=8080

# Note: Copy your actual .env file contents here if you have one
EOF

echo "✓ Environment template created at /opt/popmailmcp/.env.service"
echo "  Please edit this file with your actual configuration"

# Step 3: Set proper permissions
echo ""
echo "Step 3: Setting permissions..."
chmod 644 /etc/systemd/system/popmailmcp.service
chmod 600 /opt/popmailmcp/.env.service
chown root:root /etc/systemd/system/popmailmcp.service
chown root:root /opt/popmailmcp/.env.service

# Step 4: Reload systemd and enable service
echo ""
echo "Step 4: Configuring systemd..."
systemctl daemon-reload
systemctl enable popmailmcp.service

echo "✓ Service enabled for automatic startup"

# Step 5: Service status check
echo ""
echo "Step 5: Service configuration summary..."
echo "Service Name: popmailmcp"
echo "Service File: /etc/systemd/system/popmailmcp.service"
echo "Working Directory: /opt/popmailmcp"
echo "Python Executable: /opt/popmailmcp/venv/bin/python"
echo "Main Script: /opt/popmailmcp/mail_mcp.py"
echo "Environment File: /opt/popmailmcp/.env.service"
echo ""

echo "=== Systemd Service Setup Complete ==="
echo ""
echo "NEXT STEPS:"
echo "1. Edit /opt/popmailmcp/.env.service with your email configuration"
echo "2. Test the service: systemctl start popmailmcp"
echo "3. Check status: systemctl status popmailmcp"
echo "4. View logs: journalctl -u popmailmcp -f"
echo ""
echo "The service is now enabled and will start automatically on boot."
echo ""
