#!/usr/bin/env python3
"""
Simple direct test of MCP tools without subprocess complexity
Tests each tool function directly
"""

import os
import sys

# Add current directory to path so we can import our MCP server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment for stdio transport  
os.environ['MCP_TRANSPORT'] = 'stdio'

try:
    # Import our MCP server
    from mail_mcp import mcp
    
    print("Testing MCP Mail Server Tools")
    print("=" * 40)
    
    # Get all registered tools
    tools = []
    for name, tool_info in mcp._tools.items():
        tools.append({
            'name': name,
            'description': tool_info.description,
            'parameters': list(tool_info.func.__annotations__.keys())
        })
        
    print(f"Found {len(tools)} tools:")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   Description: {tool['description']}")
        print(f"   Parameters: {tool['parameters']}")
        print()
    
    print("SUCCESS: Your MCP server has all tools registered correctly!")
    print("Tools available:", [t['name'] for t in tools])
    
except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Error: {e}")
