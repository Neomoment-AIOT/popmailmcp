import os
import ssl
import poplib
import smtplib
from email import message_from_bytes
from email.header import decode_header, make_header
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_POP_PORT = int(os.getenv("MAIL_POP_PORT", "110"))
MAIL_SMTP_PORT = int(os.getenv("MAIL_SMTP_PORT", "587"))
MAIL_SSL = os.getenv("MAIL_SSL", "0")
MAIL_ALLOW_SELF_SIGNED = os.getenv("MAIL_ALLOW_SELF_SIGNED", "0")

USE_SSL = MAIL_SSL not in ["0", "false", "False", None]
ALLOW_SELF_SIGNED = MAIL_ALLOW_SELF_SIGNED in ["1", "true", "True"]

ssl_context = None
if ALLOW_SELF_SIGNED:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

from fastmcp import FastMCP

# Create FastMCP instance
mcp = FastMCP("plain-mail-mcp")

# Create the FastAPI app with MCP protocol at /mcp
app = mcp.http_app(path="/mcp")

# Fixed: 2025-07-27T01:30:00+05:00 - Add AI Plugin Manifest for ChatGPT Connector Registration
# ChatGPT requires an ai-plugin.json manifest to register MCP connectors
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# AI Plugin Manifest for ChatGPT
def ai_plugin_manifest():
    return {
        "schema_version": "v1",
        "name_for_model": "plain_mail_mcp",
        "name_for_human": "Email Management",
        "description_for_model": "A comprehensive email management tool that provides POP3/SMTP capabilities for reading, sending, and managing emails. Supports listing messages, retrieving email content, deleting emails, and sending new messages with CC/BCC support.",
        "description_for_human": "Manage your emails through POP3/SMTP protocols. Read, send, organize, and delete emails.",
        "auth": {
            "type": "none"
        },
        "api": {
            "type": "openapi",
            "url": "http://173.212.228.93:8088/openapi.json"
        },
        "logo_url": "http://173.212.228.93:8088/logo.png",
        "contact_email": "suhail.c@neomoment.org",
        "legal_info_url": "http://173.212.228.93:8088/legal"
    }

# OpenAPI Schema for the MCP tools
def openapi_schema():
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "POP Mail MCP Server",
            "description": "Email management via POP3/SMTP protocols",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "http://173.212.228.93:8088"}
        ],
        "paths": {
            "/mcp": {
                "post": {
                    "summary": "MCP Protocol Endpoint",
                    "description": "Main MCP protocol endpoint for email management tools",
                    "responses": {
                        "200": {
                            "description": "MCP protocol response",
                            "content": {
                                "text/event-stream": {
                                    "schema": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }

@mcp.tool
def list_messages(max_items: int = 10, flagged_only: bool = False) -> List[Dict]:
    """Return up to *max_items* newest messages (POP3)."""
    messages: List[Dict] = []
    conn = poplib.POP3_SSL(MAIL_HOST, MAIL_POP_PORT, context=ssl_context) if USE_SSL \
        else poplib.POP3(MAIL_HOST, MAIL_POP_PORT)
    conn.user(MAIL_USER)
    conn.pass_(MAIL_PASS)
    total = len(conn.list()[1])
    count = min(total, max_items if max_items else total)
    for i in range(total, total - count, -1):
        resp, hdr_lines, _ = conn.top(i, 0)
        msg = message_from_bytes(b"\r\n".join(hdr_lines))
        messages.append({
            "uid": i,
            "from": str(make_header(decode_header(msg.get("From", "")))),
            "subject": str(make_header(decode_header(msg.get("Subject", "")))),
            "date": msg.get("Date", "")
        })
    conn.quit()
    return list(reversed(messages))

@mcp.tool
def get_message(uid: int) -> str:
    """Return full raw RFC‑822 message identified by POP3 ordinal *uid*."""
    conn = poplib.POP3_SSL(MAIL_HOST, MAIL_POP_PORT, context=ssl_context) if USE_SSL \
        else poplib.POP3(MAIL_HOST, MAIL_POP_PORT)
    conn.user(MAIL_USER)
    conn.pass_(MAIL_PASS)
    resp, lines, _ = conn.retr(uid)
    conn.quit()
    return "\n".join(l.decode(errors="replace") for l in lines)

@mcp.tool
def delete_message(uid: int) -> str:
    conn = poplib.POP3_SSL(MAIL_HOST, MAIL_POP_PORT, context=ssl_context) if USE_SSL \
        else poplib.POP3(MAIL_HOST, MAIL_POP_PORT)
    conn.user(MAIL_USER)
    conn.pass_(MAIL_PASS)
    conn.dele(uid)
    conn.quit()
    return f"Message {uid} deleted."

@mcp.tool
def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> str:
    """Send a plain‑text e‑mail."""
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = MAIL_USER
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg.set_content(body)
    rcpts = [e.strip() for e in (to + "," + cc + "," + bcc).split(',') if e.strip()]
    if MAIL_SMTP_PORT == 465 or USE_SSL:
        smtp = smtplib.SMTP_SSL(MAIL_HOST, MAIL_SMTP_PORT, context=ssl_context)
    else:
        smtp = smtplib.SMTP(MAIL_HOST, MAIL_SMTP_PORT)
        try:
            smtp.starttls(context=ssl_context)
        except Exception:
            pass
    smtp.login(MAIL_USER, MAIL_PASS)
    smtp.send_message(msg, from_addr=MAIL_USER, to_addrs=rcpts)
    smtp.quit()
    return "Email sent."

if __name__ == "__main__":
    import uvicorn
    import threading

    # Create a separate FastAPI app for the plugin manifest
    from fastapi import FastAPI, Response
    from fastapi.middleware.cors import CORSMiddleware

    # Create FastAPI app for the plugin endpoints
    plugin_app = FastAPI()

    # Add CORS middleware to the plugin app
    plugin_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @plugin_app.get("/")
    @plugin_app.get("/.well-known/ai-plugin.json")
    async def plugin_manifest():
        return {
            "schema_version": "v1",
            "name_for_human": "Email Manager",
            "name_for_model": "email_manager",
            "description_for_human": "Manage your email - send, receive, and organize messages with ease.",
            "description_for_model": "A tool for managing email. It can send emails, check incoming messages, and manage email folders.",
            "auth": {"type": "none"},
            "api": {
                "type": "openapi",
                "url": "http://173.212.228.93:8088/openapi.json"
            },
            "logo_url": "http://173.212.228.93:8088/logo.png",
            "contact_email": "suhail.c@neomoment.org",
            "legal_info_url": "http://173.212.228.93:8088/legal"
        }

    @plugin_app.get("/openapi.json")
    async def openapi_schema():
        return {
            "openapi": "3.0.1",
            "info": {
                "title": "Email Manager API",
                "version": "1.0.0",
                "description": "API for managing emails through MCP protocol"
            },
            "servers": [{"url": "http://173.212.228.93:8088"}],
            "paths": {
                "/mcp": {
                    "post": {
                        "description": "MCP protocol endpoint for email operations",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "MCP response",
                                "content": {
                                    "application/json": {"schema": {"type": "object"}}
                                }
                            }
                        }
                    }
                }
            }
        }

    @plugin_app.get("/logo.png")
    async def logo():
        # Return a placeholder logo
        from fastapi.responses import FileResponse
        return FileResponse("logo.png", media_type="image/png")

    @plugin_app.get("/legal")
    async def legal():
        return {"message": "Legal information for Email Manager"}

    # Start the MCP server in a separate thread
    def run_mcp_server():
        mcp.run(transport="http", host="0.0.0.0", port=8088, path="/mcp")

    # Start the plugin API server in the main thread
    def run_plugin_server():
        import uvicorn
        uvicorn.run(plugin_app, host="0.0.0.0", port=8089)

    # Start MCP server in a separate thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    # Start plugin server in the main thread
    run_plugin_server()