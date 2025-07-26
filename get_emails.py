#!/usr/bin/env python3
"""
MCP Email Client - Updated to use FastMCP client approach
Date: 2025-07-26 18:34

This script connects to the FastMCP email server and provides email functionality
for ChatGPT integration through the MCP protocol.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Optional
from fastmcp.client import Client

# Set UTF-8 encoding for console output to handle Unicode
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPEmailClient:
    """MCP Email Client using FastMCP library"""
    
    def __init__(self, base_url: str = "http://localhost:8088/mcp/"):
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = Client(self.base_url)
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def list_tools(self) -> List[Dict]:
        """List available MCP tools"""
        try:
            tools = await self.client.list_tools()
            logger.info(f"Found {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def list_messages(self, max_items: int = 20, flagged_only: bool = False) -> List[Dict]:
        """List email messages"""
        try:
            result = await self.client.call_tool(
                "list_messages",
                arguments={
                    "max_items": max_items,
                    "flagged_only": flagged_only
                }
            )
            
            if result.is_error:
                logger.error(f"Error listing messages: {result.content}")
                return []
            
            # Parse the result
            if result.structured_content and 'result' in result.structured_content:
                messages = result.structured_content['result']
                logger.info(f"Retrieved {len(messages)} messages")
                return messages
            else:
                logger.warning("No structured content found in response")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list messages: {e}")
            return []
    
    async def get_message(self, uid: str) -> Optional[str]:
        """Get full message content by UID"""
        try:
            result = await self.client.call_tool(
                "get_message",
                arguments={"uid": uid}
            )
            
            if result.is_error:
                logger.error(f"Error getting message {uid}: {result.content}")
                return None
            
            if result.structured_content and 'result' in result.structured_content:
                return result.structured_content['result']
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get message {uid}: {e}")
            return None
    
    async def send_email(self, to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> bool:
        """Send an email"""
        try:
            result = await self.client.call_tool(
                "send_email",
                arguments={
                    "to": to,
                    "subject": subject,
                    "body": body,
                    "cc": cc,
                    "bcc": bcc
                }
            )
            
            if result.is_error:
                logger.error(f"Error sending email: {result.content}")
                return False
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def search_messages_by_sender(self, sender: str, max_items: int = 20) -> List[Dict]:
        """Search for messages from a specific sender"""
        try:
            # Get all messages first (more than max_items to search through)
            all_messages = await self.list_messages(max_items=100)
            
            # Filter messages by sender
            filtered_messages = []
            for msg in all_messages:
                if sender.lower() in msg.get('from', '').lower():
                    filtered_messages.append(msg)
            
            # Sort by UID (descending - newer messages first)
            filtered_messages.sort(key=lambda x: int(x.get('uid', '0')), reverse=True)
            
            # Return requested number of messages
            return filtered_messages[:max_items]
            
        except Exception as e:
            logger.error(f"Failed to search messages by sender {sender}: {e}")
            return []

    async def delete_message(self, uid: str) -> bool:
        """Delete a message by UID"""
        try:
            result = await self.client.call_tool(
                "delete_message",
                arguments={"uid": uid}
            )
            
            if result.is_error:
                logger.error(f"Error deleting message {uid}: {result.content}")
                return False
            
            logger.info(f"Message {uid} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete message {uid}: {e}")
            return False

    async def flag_message(self, uid: str) -> bool:
        """Flag (pin) a message"""
        try:
            result = await self.client.call_tool(
                "flag_message",
                arguments={"uid": uid}
            )
            
            if result.is_error:
                logger.error(f"Error flagging message {uid}: {result.content}")
                return False
            
            logger.info(f"Message {uid} flagged successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to flag message {uid}: {e}")
            return False

def print_messages(messages: List[Dict], title: str = "Messages"):
    """Helper function to print messages in a readable format"""
    if not messages:
        print(f"\n=== {title} ===")
        print("No messages found.")
        return
    
    print(f"\n=== {title} ({len(messages)} messages) ===")
    for i, msg in enumerate(messages, 1):
        print(f"{i}. UID: {msg.get('uid', 'N/A')}")
        print(f"   From: {msg.get('from', 'N/A')}")
        print(f"   Subject: {msg.get('subject', 'N/A')}")
        print(f"   Date: {msg.get('date', 'N/A')}")
        print(f"   Flagged: {msg.get('is_flagged', False)}")
        print()

async def main():
    """Main function to demonstrate MCP email functionality"""
    
    try:
        # Use async context manager for proper connection handling
        async with MCPEmailClient() as client:
            # List available tools
            print("=== Available MCP Tools ===")
            tools = await client.list_tools()
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")
            
            # List recent messages
            print("\n=== Recent Messages ===")
            recent_messages = await client.list_messages(max_items=10)
            print_messages(recent_messages, "Recent Messages")
            
            # Search for messages from Zaecy
            print("\n=== Searching for Messages from Zaecy ===")
            zaecy_messages = await client.search_messages_by_sender("Zaecy", max_items=20)
            print_messages(zaecy_messages, "Messages from Zaecy")
            
            # If we found Zaecy messages, show the latest one's content
            if zaecy_messages:
                latest_msg = zaecy_messages[0]
                print(f"\n=== Latest Message from Zaecy (UID: {latest_msg['uid']}) ===")
                message_content = await client.get_message(latest_msg['uid'])
                if message_content:
                    print(message_content)
                else:
                    print("Failed to retrieve message content")
            
            # Example: Send a test email (commented out to avoid spam)
            """
            print("\n=== Sending Test Email ===")
            success = await client.send_email(
                to="suhail.c@neomoment.org",
                subject="Test from MCP Email Client",
                body="This is a test email sent through the MCP protocol!"
            )
            print(f"Email sent: {success}")
            """
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
