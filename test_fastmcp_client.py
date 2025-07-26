"""
Test FastMCP client connectivity - Date: 2025-07-26 17:37
Using FastMCP's own client library to test communication with the server
"""
import asyncio
import logging
import sys
from fastmcp.client import Client

# Set UTF-8 encoding for console output
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_fastmcp_client():
    """Test using FastMCP's own client library"""
    print("=== Testing FastMCP Client Library ===")
    
    try:
        # Connect using FastMCP client
        async with Client("http://173.212.228.93:8088/mcp/") as client:
            print("SUCCESS: Connected to FastMCP server successfully!")
            
            # Test 1: List available tools
            print("\n1. Listing available tools...")
            tools = await client.list_tools()
            print(f"Found {len(tools)} tools:")
            for tool in tools:
                # Handle Unicode characters in descriptions
                description = tool.description.encode('ascii', 'replace').decode('ascii')
                print(f"  - {tool.name}: {description}")
            
            # Test 2: Call list_messages tool
            if tools:
                print("\n2. Calling list_messages tool...")
                result = await client.call_tool(
                    "list_messages",
                    {
                        "max_items": 3,
                        "flagged_only": False
                    }
                )
                print("SUCCESS: Tool call successful!")
                print("Result:", result)
                
                # Parse and display messages if successful
                if hasattr(result, 'content') and result.content:
                    print("\n=== Email Messages ===")
                    for i, content in enumerate(result.content, 1):
                        if hasattr(content, 'text'):
                            print(f"{i}. {content.text}")
                        else:
                            print(f"{i}. {content}")
            else:
                print("ERROR: No tools found - cannot test tool calling")
                
    except Exception as e:
        print(f"ERROR: FastMCP Client Error: {e}")
        logger.exception("Full error details:")

if __name__ == "__main__":
    asyncio.run(test_fastmcp_client())
