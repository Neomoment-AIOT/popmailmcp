#!/usr/bin/env python3
"""
Complete testing commands for MCP Mail Server
Shows how to test each tool with actual examples
"""

import json
import requests
import subprocess
import time
import os

def test_http_server():
    """Test MCP server via HTTP (server must be running on port 8088)"""
    
    print("=== HTTP SERVER TESTING ===")
    print("First, start your server with: python mail_mcp.py")
    print("Server should be running on: http://localhost:8088/mcp/")
    print()
    
    # Basic server check
    print("1. TEST: Check if server is responding")
    print("Command: curl -H \"Accept: text/event-stream\" http://localhost:8088/mcp/")
    print("Expected: {'jsonrpc': '2.0', 'id': 'server-error', 'error': {'code': -32600, 'message': 'Bad Request: Missing session ID'}}")
    print("(This error means server is working - it needs proper MCP session)")
    print()

def test_stdio_server():
    """Test MCP server via stdio (direct communication)"""
    
    print("=== STDIO SERVER TESTING ===")
    print("Test server directly using stdio transport")
    print()
    
    # Test each tool individually
    tools_tests = [
        {
            "name": "list_messages",
            "description": "List newest messages",
            "example_request": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "list_messages",
                    "arguments": {
                        "max_items": 5,
                        "flagged_only": False
                    }
                }
            }
        },
        {
            "name": "get_message",
            "description": "Get specific message content",
            "example_request": {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_message",
                    "arguments": {
                        "uid": "12345"
                    }
                }
            }
        },
        {
            "name": "delete_message",
            "description": "Delete a message",
            "example_request": {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "delete_message",
                    "arguments": {
                        "uid": "12345"
                    }
                }
            }
        },
        {
            "name": "flag_message",
            "description": "Flag a message (IMAP only)",
            "example_request": {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "flag_message",
                    "arguments": {
                        "uid": "12345"
                    }
                }
            }
        },
        {
            "name": "unflag_message",
            "description": "Unflag a message (IMAP only)",
            "example_request": {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "unflag_message",
                    "arguments": {
                        "uid": "12345"
                    }
                }
            }
        },
        {
            "name": "send_email",
            "description": "Send an email",
            "example_request": {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "send_email",
                    "arguments": {
                        "to": "recipient@example.com",
                        "subject": "Test Email",
                        "body": "This is a test email from MCP server",
                        "cc": "",
                        "bcc": ""
                    }
                }
            }
        }
    ]
    
    for i, tool in enumerate(tools_tests, 1):
        print(f"{i}. TEST: {tool['name']}")
        print(f"   Description: {tool['description']}")
        print(f"   JSON Request:")
        print(f"   {json.dumps(tool['example_request'], indent=4)}")
        print()

def show_manual_testing_steps():
    """Show step-by-step manual testing"""
    
    print("=== MANUAL TESTING STEPS ===")
    print()
    
    steps = [
        "1. Start your MCP server:",
        "   Command: python mail_mcp.py",
        "   You should see: Server running on http://0.0.0.0:8088/mcp/",
        "",
        "2. Test server is responding:",
        "   Command: curl -H \"Accept: text/event-stream\" http://localhost:8088/mcp/",
        "   Expected: Error about missing session ID (this is good!)",
        "",
        "3. To test tools, you need email credentials in .env file:",
        "   Create/edit .env with your email settings:",
        "   MAIL_HOST=your.email.server.com",
        "   MAIL_USER=your.email@example.com", 
        "   MAIL_PASS=your_password",
        "   MAIL_SSL=1",
        "",
        "4. Test with stdio transport:",
        "   Command: $env:MCP_TRANSPORT=\"stdio\"; python mail_mcp.py",
        "   (This starts server in direct mode for testing)",
        "",
        "5. Each tool requires proper email configuration to work.",
        "   Without real email credentials, tools will show connection errors.",
        "   This is expected behavior."
    ]
    
    for step in steps:
        print(step)
    print()

def show_environment_setup():
    """Show how to set up email environment"""
    
    print("=== EMAIL ENVIRONMENT SETUP ===")
    print()
    print("Your MCP server needs email credentials to work.")
    print("Create a .env file with these settings:")
    print()
    
    env_example = """# Email Server Settings
MAIL_HOST=imap.gmail.com         # Your email server
MAIL_USER=your.email@gmail.com   # Your email address  
MAIL_PASS=your_app_password      # Your email password/app password
MAIL_SSL=1                       # Use SSL (1=yes, 0=no)

# Optional: Different settings for POP/SMTP
# MAIL_POP_HOST=pop.gmail.com
# MAIL_SMTP_HOST=smtp.gmail.com
"""
    
    print(env_example)
    print("Common email servers:")
    print("- Gmail: imap.gmail.com, smtp.gmail.com")  
    print("- Outlook: outlook.office365.com")
    print("- Yahoo: imap.mail.yahoo.com, smtp.mail.yahoo.com")
    print()

if __name__ == "__main__":
    print("MCP MAIL SERVER TESTING GUIDE")
    print("=" * 50)
    print()
    
    show_environment_setup()
    show_manual_testing_steps()
    test_http_server()
    test_stdio_server()
    
    print("=== SUMMARY ===")
    print("Your MCP server has 6 tools:")
    print("1. list_messages - List emails")
    print("2. get_message - Get email content") 
    print("3. delete_message - Delete emails")
    print("4. flag_message - Flag emails (IMAP)")
    print("5. unflag_message - Unflag emails (IMAP)")
    print("6. send_email - Send new emails")
    print()
    print("To test properly, you need:")
    print("- Real email credentials in .env file")
    print("- Server running (python mail_mcp.py)")
    print("- MCP-compatible client or custom testing script")
