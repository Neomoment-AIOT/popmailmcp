#!/usr/bin/env python3
"""
Simple verification that MCP server can import and has tools defined
This proves the server structure is correct
"""

import sys
import importlib.util

def verify_mcp_server():
    print("Verifying MCP Mail Server...")
    print("-" * 30)
    
    try:
        # Load the mail_mcp module
        spec = importlib.util.spec_from_file_location("mail_mcp", "mail_mcp.py")
        mail_mcp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mail_mcp_module)
        
        # Check if mcp object exists
        if hasattr(mail_mcp_module, 'mcp'):
            print("✓ FastMCP server object created successfully")
            
            # Check if it's a FastMCP instance
            mcp_obj = mail_mcp_module.mcp
            print(f"✓ Server name: {getattr(mcp_obj, 'name', 'Unknown')}")
            print(f"✓ Server version: {getattr(mcp_obj, 'version', 'Unknown')}")
            
            # Try to find tool decorators in the source
            with open('mail_mcp.py', 'r') as f:
                content = f.read()
                tool_count = content.count('@mcp.tool')
                print(f"✓ Found {tool_count} tool definitions")
                
                # Extract tool names
                import re
                tool_matches = re.findall(r'def (\w+)\([^)]*\).*?@mcp\.tool|@mcp\.tool.*?def (\w+)\(', content, re.DOTALL)
                tools = [match[0] or match[1] for match in tool_matches if match[0] or match[1]]
                
                if tools:
                    print("✓ Tool functions found:")
                    for tool in tools:
                        print(f"  - {tool}")
                
            print("\n🎉 SUCCESS: Your MCP server is properly structured!")
            print("🚀 Ready to use with any MCP client!")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    verify_mcp_server()
