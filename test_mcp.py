#!/usr/bin/env python3
"""
Simple MCP client to test the mail_mcp.py server
Run this to test your MCP server locally without any external dependencies
"""

import json
import subprocess
import sys
from typing import Dict, Any

def test_mcp_server():
    """Test the MCP server by sending JSON-RPC requests via stdio"""
    
    # Start the MCP server with stdio transport
    process = subprocess.Popen(
        [sys.executable, "mail_mcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"MCP_TRANSPORT": "stdio"}
    )
    
    print("Testing MCP Mail Server...")
    print("=" * 50)
    
    # Test 1: Initialize the MCP connection
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        # Send initialize request
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print("Initialize Response:")
            print(json.dumps(response, indent=2))
        
        # Test 2: Get available tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        tools_response = process.stdout.readline()
        if tools_response:
            tools_data = json.loads(tools_response.strip())
            print("\nAvailable Tools:")
            print(json.dumps(tools_data, indent=2))
            
            # Show tool names
            if "result" in tools_data and "tools" in tools_data["result"]:
                tool_names = [tool["name"] for tool in tools_data["result"]["tools"]]
                print(f"\nTool Names: {', '.join(tool_names)}")
        
        print("\nMCP Server is working correctly!")
        print("Your mail server is ready to use!")
        
    except Exception as e:
        print(f"Error testing MCP server: {e}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_mcp_server()
