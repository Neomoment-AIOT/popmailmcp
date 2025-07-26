#!/bin/bash

# POP Mail MCP Server Deployment Script
# Created: 2025-07-26 19:51:00
# Purpose: Deploy POP Mail MCP Server to /opt/popmailmcp with Python 3.13 virtual environment

set -e  # Exit on any error

echo "=== POP Mail MCP Server Deployment Started ==="
echo "Date: $(date)"
echo "Target Directory: /opt/popmailmcp"
echo "Python Version: 3.13"
echo "Repository: https://github.com/Neomoment-AIOT/popmailmcp.git"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python 3.13 if not available
install_python313() {
    echo "Installing Python 3.13..."
    
    # Update package list
    apt update
    
    # Install dependencies
    apt install -y software-properties-common
    
    # Add deadsnakes PPA for Python 3.13
    add-apt-repository -y ppa:deadsnakes/ppa
    apt update
    
    # Install Python 3.13 and venv
    apt install -y python3.13 python3.13-venv python3.13-dev
    
    echo "Python 3.13 installed successfully"
}

# Step 1: Check if Python 3.13 is available
echo "Step 1: Checking Python 3.13 availability..."
if ! command_exists python3.13; then
    echo "Python 3.13 not found. Installing..."
    install_python313
else
    echo "Python 3.13 found: $(python3.13 --version)"
fi

# Step 2: Install Git if not available
echo ""
echo "Step 2: Checking Git availability..."
if ! command_exists git; then
    echo "Installing Git..."
    apt update
    apt install -y git
else
    echo "Git found: $(git --version)"
fi

# Step 3: Create deployment directory
echo ""
echo "Step 3: Creating deployment directory..."
if [ -d "/opt/popmailmcp" ]; then
    echo "Directory /opt/popmailmcp already exists. Backing up..."
    mv /opt/popmailmcp /opt/popmailmcp.backup.$(date +%Y%m%d_%H%M%S)
fi

mkdir -p /opt/popmailmcp
cd /opt/popmailmcp

# Step 4: Clone repository
echo ""
echo "Step 4: Cloning repository..."
git clone https://github.com/Neomoment-AIOT/popmailmcp.git .

# Check if clone was successful
if [ ! -f "mail_mcp.py" ]; then
    echo "ERROR: mail_mcp.py not found after cloning. Please check repository URL."
    exit 1
fi

echo "Repository cloned successfully"

# Step 5: Create virtual environment
echo ""
echo "Step 5: Creating Python 3.13 virtual environment..."
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

echo "Virtual environment created and activated"

# Step 6: Install dependencies
echo ""
echo "Step 6: Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "Dependencies installed from requirements.txt"
else
    echo "WARNING: requirements.txt not found. Installing common dependencies..."
    # Install common MCP server dependencies
    pip install fastmcp asyncio aiofiles
fi

# Step 7: Set proper permissions
echo ""
echo "Step 7: Setting permissions..."
chown -R root:root /opt/popmailmcp
chmod +x /opt/popmailmcp/mail_mcp.py
chmod 755 /opt/popmailmcp

# Step 8: Test the installation
echo ""
echo "Step 8: Testing installation..."
python3.13 -c "import sys; print(f'Python version: {sys.version}')"
echo "Testing mail_mcp.py import..."
python3.13 -c "
import sys
sys.path.insert(0, '/opt/popmailmcp')
try:
    import mail_mcp
    print('✓ mail_mcp.py imports successfully')
except Exception as e:
    print(f'✗ Error importing mail_mcp.py: {e}')
"

echo ""
echo "=== Deployment Basic Setup Complete ==="
echo "Next: Run systemd_setup.sh to configure system service"
echo "Location: /opt/popmailmcp"
echo "Virtual Environment: /opt/popmailmcp/venv"
echo "Main Server File: /opt/popmailmcp/mail_mcp.py"
echo ""
