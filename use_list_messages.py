#!/usr/bin/env python3
"""
Practical example: How to actually use list_messages tool
This creates a simple client to test your MCP server
"""

import requests
import json
import time
import subprocess
import sys

def test_list_messages_http():
    """Test list_messages via HTTP request to running server"""
    
    print("TESTING list_messages via HTTP")
    print("=" * 35)
    
    # MCP server URL
    server_url = "http://173.212.228.93:8088/mcp/"
    
    # Request to list messages
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "list_messages",
            "arguments": {
                "max_items": 10,        # Get 10 newest emails
                "flagged_only": False   # Get all emails, not just flagged
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    try:
        print("Sending request to MCP server...")
        print(f"URL: {server_url}")
        print(f"Request: {json.dumps(request_data, indent=2)}")
        print()
        
        response = requests.post(server_url, json=request_data, headers=headers, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\nSUCCESS! Email list retrieved:")
                print(json.dumps(result, indent=2))
            except:
                print("Response received but not JSON format")
        else:
            print("Server responded with error - check if server is running")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP server!")
        print("Make sure server is running with: python mail_mcp.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def start_server_and_test():
    """Start server in background and test"""
    
    print("COMPLETE list_messages TEST")
    print("=" * 30)
    
    # Start server in background
    print("1. Starting MCP server...")
    try:
        server_process = subprocess.Popen([
            sys.executable, "mail_mcp.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give server time to start
        time.sleep(3)
        
        print("2. Server started, testing list_messages...")
        
        # Test the list_messages tool
        success = test_list_messages_http()
        
        if success:
            print("\n✅ list_messages tool works correctly!")
        else:
            print("\n❌ Test failed - check email configuration in .env")
            
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        # Clean up
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
            print("\n3. Server stopped.")
        except:
            pass

def show_usage_examples():
    """Show different ways to use list_messages"""
    
    print("\nlist_messages USAGE EXAMPLES")
    print("=" * 30)
    
    examples = [
        {
            "description": "Get 5 newest emails",
            "arguments": {"max_items": 5, "flagged_only": False}
        },
        {
            "description": "Get only flagged emails", 
            "arguments": {"max_items": 10, "flagged_only": True}
        },
        {
            "description": "Get 20 newest emails",
            "arguments": {"max_items": 20, "flagged_only": False}
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}:")
        request = {
            "jsonrpc": "2.0",
            "id": i,
            "method": "tools/call",
            "params": {
                "name": "list_messages",
                "arguments": example['arguments']
            }
        }
        print(f"   Request: {json.dumps(request, indent=6)}")

if __name__ == "__main__":
    # Show usage examples first
    show_usage_examples()
    
    print("\n" + "=" * 50)
    choice = input("Do you want to test list_messages now? (y/n): ").lower()
    
    if choice == 'y':
        start_server_and_test()
    else:
        print("\nTo test manually:")
        print("1. Run: python mail_mcp.py")
        print("2. Use the HTTP requests shown above")
        print("3. Or run: python use_list_messages.py")
