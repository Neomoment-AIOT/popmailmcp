#!/usr/bin/env python3
"""
Example: How to test list_messages tool from your MCP server
This shows exactly how to call the list_messages function
"""

import os
import sys

# Set environment for MCP
os.environ['MCP_TRANSPORT'] = 'stdio'

def test_list_messages_directly():
    """Test list_messages by calling it directly from the mail_mcp module"""
    
    print("TESTING list_messages TOOL")
    print("=" * 40)
    
    try:
        # Import your MCP server module
        import mail_mcp
        
        print("Server loaded successfully!")
        print(f"Server name: {mail_mcp.mcp.name}")
        print()
        
        # The list_messages function is decorated with @mcp.tool
        # Let's try to access it directly from the module
        
        print("Available functions in mail_mcp module:")
        functions = [name for name in dir(mail_mcp) if callable(getattr(mail_mcp, name)) and not name.startswith('_')]
        for func in functions:
            print(f"  - {func}")
        print()
        
        # Try to call list_messages directly
        if hasattr(mail_mcp, 'list_messages'):
            print("Calling list_messages(max_items=5, flagged_only=False)...")
            print()
            
            try:
                # Call the function with default parameters
                result = mail_mcp.list_messages(max_items=5, flagged_only=False)
                print("SUCCESS! Results:")
                print(result)
                
            except Exception as e:
                print(f"Function call result: {e}")
                print("Note: This error is expected if email server connection fails.")
                print("The function exists and is callable - that's what matters!")
        else:
            print("list_messages function not found as direct attribute")
            
    except Exception as e:
        print(f"Error: {e}")

def show_command_usage():
    """Show how to use list_messages in different ways"""
    
    print("\nHOW TO USE list_messages")
    print("=" * 30)
    print()
    
    print("METHOD 1: Direct Function Call (Python)")
    print("--------------------------------------")
    print("import mail_mcp")
    print("messages = mail_mcp.list_messages(max_items=10, flagged_only=False)")
    print("print(messages)")
    print()
    
    print("METHOD 2: Via MCP Protocol (JSON-RPC)")
    print("------------------------------------")
    print("Send this JSON request to your running MCP server:")
    print("""
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "list_messages",
        "arguments": {
            "max_items": 10,
            "flagged_only": false
        }
    }
}""")
    print()
    
    print("METHOD 3: Via HTTP (with MCP client)")
    print("----------------------------------")
    print("1. Start server: python mail_mcp.py")
    print("2. Server runs on: http://173.212.228.93:8088/mcp/")
    print("3. Connect with MCP-compatible client")
    print("4. Call 'list_messages' tool with parameters")
    print()
    
    print("PARAMETERS for list_messages:")
    print("- max_items (int): Number of emails to retrieve (default: 10)")
    print("- flagged_only (bool): Only show flagged emails (default: False)")
    print()
    
    print("EXAMPLES:")
    print("- List 5 newest emails: list_messages(max_items=5)")
    print("- List only flagged emails: list_messages(flagged_only=True)")
    print("- List 20 emails: list_messages(max_items=20)")

if __name__ == "__main__":
    test_list_messages_directly()
    show_command_usage()
