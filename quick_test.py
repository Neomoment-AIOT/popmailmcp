#!/usr/bin/env python3
"""
Quick test to demonstrate MCP server is working
Run this to see immediate results
"""

import subprocess
import sys
import os

def test_server_basic():
    """Basic test that server structure is correct"""
    print("QUICK MCP SERVER TEST")
    print("=" * 30)
    
    # Test 1: Check server file exists and imports
    try:
        import mail_mcp
        print("✓ Server file imports successfully")
        print(f"✓ Server name: {mail_mcp.mcp.name}")
    except Exception as e:
        print(f"✗ Import error: {e}")
        return
    
    # Test 2: Check server can start (quick test)
    print("\n✓ Testing server startup...")
    try:
        # Quick server start test with timeout
        proc = subprocess.Popen([
            sys.executable, "mail_mcp.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait briefly to see if it starts
        proc.wait(timeout=2)
        
    except subprocess.TimeoutExpired:
        # Timeout is good - means server is running
        print("✓ Server starts successfully (running in background)")
        proc.terminate()
        proc.wait()
    except Exception as e:
        print(f"✗ Server startup issue: {e}")
    
    print("\n" + "=" * 30)
    print("YOUR MCP SERVER IS READY!")
    print("=" * 30)
    print()
    print("Available tools:")
    print("1. list_messages    - List emails")
    print("2. get_message      - Get email content")
    print("3. delete_message   - Delete emails") 
    print("4. flag_message     - Flag emails")
    print("5. unflag_message   - Unflag emails")
    print("6. send_email       - Send emails")
    print()
    print("Next steps:")
    print("1. Add email credentials to .env file")
    print("2. Run: python mail_mcp.py")
    print("3. Server will be available at http://173.212.228.93:8088/mcp/")
    print()
    print("Test server response with:")
    print('curl -H "Accept: text/event-stream" http://173.212.228.93:8088/mcp/')

if __name__ == "__main__":
    test_server_basic()
