import os
import ssl
import poplib
import smtplib
from email import message_from_bytes
from email.header import decode_header, make_header
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time
import secrets
import json
from datetime import datetime, timedelta

load_dotenv()

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_POP_PORT = int(os.getenv("MAIL_POP_PORT", "110"))
MAIL_SMTP_PORT = int(os.getenv("MAIL_SMTP_PORT", "587"))
MAIL_SSL = os.getenv("MAIL_SSL", "0")
MAIL_ALLOW_SELF_SIGNED = os.getenv("MAIL_ALLOW_SELF_SIGNED", "0")

OAUTH_CLIENT_ID = "popmail-mcp"
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", secrets.token_urlsafe(32))
OAUTH_ACCESS_TOKEN_EXPIRE_SECONDS = 3600  # 1 hour
OAUTH_REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days

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

# Debug: Print registered routes
print("\n=== Registered MCP Methods ===")
mcp_methods = []
for method_name in dir(mcp):
    if not method_name.startswith('_'):
        try:
            method = getattr(mcp, method_name)
            if hasattr(method, '_is_mcp_method'):
                mcp_methods.append(method_name)
        except Exception as e:
            print(f"Warning: Could not inspect method {method_name}: {e}")
print("\n".join(mcp_methods) or "No MCP methods found")

print("\n=== Registered Routes ===")
for route in app.routes:
    try:
        if hasattr(route, 'methods'):
            print(f"{' '.join(route.methods)} {route.path}")
        elif hasattr(route, 'path'):
            print(f"UNKNOWN_METHODS {route.path}")
        else:
            print(f"Route: {route}")
    except Exception as e:
        print(f"Error inspecting route {route}: {e}")
print("\n")

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
            "url": "http://173.212.228.93:8089/openapi.json"
        },
        "logo_url": "http://173.212.228.93:8089/logo.png",
        "contact_email": "suhail.c@neomoment.org",
        "legal_info_url": "http://173.212.228.93:8089/legal"
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
            {"url": "http://173.212.228.93:8089"}
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
    from fastapi import FastAPI, Response, Request, Depends, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
    from fastapi.security import OAuth2AuthorizationCodeBearer
    from pydantic import BaseModel

    # OAuth token storage (in-memory for now, use a database in production)
    oauth_tokens = {}
    oauth_codes = {}

    def generate_token(user_id: str, scopes: list = None) -> dict:
        """Generate OAuth access and refresh tokens."""
        if scopes is None:
            scopes = ["email:read", "email:write"]
            
        access_token = f"access_{secrets.token_urlsafe(32)}"
        refresh_token = f"refresh_{secrets.token_urlsafe(32)}"
        expires_at = int(time.time()) + OAUTH_ACCESS_TOKEN_EXPIRE_SECONDS
        
        token_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": OAUTH_ACCESS_TOKEN_EXPIRE_SECONDS,
            "refresh_token": refresh_token,
            "scope": " ".join(scopes),
            "user_id": user_id,
            "expires_at": expires_at
        }
        
        # Store the refresh token
        oauth_tokens[refresh_token] = {
            "access_token": access_token,
            "user_id": user_id,
            "scopes": scopes,
            "expires_at": int(time.time()) + (OAUTH_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
        }
        
        return token_data

    # Create FastAPI app for the plugin endpoints
    plugin_app = FastAPI()

    # Add CORS middleware to the plugin app with explicit OPTIONS handling
    # Allow ngrok domain and local development
    allowed_origins = [
        "https://witty-enormous-hippo.ngrok-free.app",
        "http://localhost:8089",
        "http://127.0.0.1:8089",
        "http://173.212.228.93:8089"
    ]
    
    plugin_app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Explicitly handle OPTIONS for all routes
    @plugin_app.middleware("http")
    async def add_cors_headers(request: Request, call_next):
        response = await call_next(request)
        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    @plugin_app.post("/")
    async def handle_post_request(request: Request):
        # Log the incoming request for debugging
        print(f"Received POST request with headers: {request.headers}")
        try:
            body = await request.json()
            print(f"Request body: {body}")
        except Exception as e:
            print(f"Error reading request body: {e}")
        
        # Handle POST requests to the root endpoint
        return {
            "status": "success",
            "message": "Request received",
            "endpoints": {
                "mcp": "/mcp",
                "openapi": "/openapi.json",
                "manifest": "/.well-known/ai-plugin.json"
            }
        }

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
                "url": "http://173.212.228.93:8089/openapi.json"
            },
            "logo_url": "http://173.212.228.93:8089/logo.png",
            "contact_email": "suhail.c@neomoment.org",
            "legal_info_url": "http://173.212.228.93:8089/legal"
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
            "servers": [{"url": "http://173.212.228.93:8089"}],
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
    @plugin_app.get("/favicon.ico")
    @plugin_app.get("/favicon.png")
    @plugin_app.get("/favicon.svg")
    async def favicon():
        # Serve the logo file for all favicon requests
        from fastapi.responses import FileResponse
        return FileResponse("LogoFile.png", media_type="image/png")

    # OAuth configuration endpoint required by ChatGPT
    @plugin_app.get("/.well-known/oauth-configuration")
    async def oauth_config():
        """Return OAuth configuration for ChatGPT connector."""
        base_url = "https://witty-enormous-hippo.ngrok-free.app"
        return {
            "client_id": OAUTH_CLIENT_ID,
            "redirect_uris": [f"{base_url}/oauth/callback"],
            "auth_uri": f"{base_url}/oauth/authorize",
            "token_uri": f"{base_url}/oauth/token",
            "scopes": ["email:read", "email:write"],
            "response_types": ["code"],
            "grant_types": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_method": "none"
        }

    # OAuth authorization endpoint
    @plugin_app.get("/oauth/authorize")
    async def oauth_authorize(
        response_type: str,
        client_id: str,
        redirect_uri: str,
        scope: str = None,
        state: str = None
    ):
        """OAuth 2.0 authorization endpoint."""
        if client_id != OAUTH_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid client_id")
            
        # In a real app, you'd show a login/consent page here
        # For simplicity, we'll auto-approve all requests
        
        # Generate an authorization code
        code = f"auth_{secrets.token_urlsafe(16)}"
        oauth_codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "expires_at": int(time.time()) + 600,  # 10 minutes
            "user_id": "chatgpt-user"  # In a real app, this would be the logged-in user
        }
        
        # Redirect back with the code
        from fastapi.responses import RedirectResponse
        redirect_url = f"{redirect_uri}?code={code}"
        if state:
            redirect_url += f"&state={state}"
        return RedirectResponse(url=redirect_url)

    # OAuth token endpoint
    @plugin_app.post("/oauth/token")
    async def oauth_token(
        grant_type: str,
        code: str = None,
        refresh_token: str = None,
        redirect_uri: str = None,
        client_id: str = None
    ):
        """OAuth 2.0 token endpoint."""
        try:
            if grant_type == "authorization_code":
                if not code or not redirect_uri or not client_id:
                    raise HTTPException(status_code=400, detail="Missing required parameters")
                
                # Verify the authorization code
                code_data = oauth_codes.pop(code, None)
                if not code_data or code_data["expires_at"] < time.time():
                    raise HTTPException(status_code=400, detail="Invalid or expired authorization code")
                
                # Generate tokens
                user_id = code_data["user_id"]
                scopes = code_data["scope"].split() if code_data["scope"] else ["email:read", "email:write"]
                
                return generate_token(user_id, scopes)
                
            elif grant_type == "refresh_token":
                if not refresh_token:
                    raise HTTPException(status_code=400, detail="Missing refresh_token")
                
                # Verify the refresh token
                token_data = oauth_tokens.get(refresh_token)
                if not token_data or token_data["expires_at"] < time.time():
                    raise HTTPException(status_code=400, detail="Invalid or expired refresh token")
                
                # Generate new tokens
                user_id = token_data["user_id"]
                scopes = token_data["scopes"]
                
                # Remove the old refresh token
                oauth_tokens.pop(refresh_token, None)
                
                return generate_token(user_id, scopes)
                
            else:
                raise HTTPException(status_code=400, detail="Unsupported grant_type")
                
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in oauth_token: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @plugin_app.get("/legal")
    async def legal():
        return {"message": """Of course. Integrating a ChatGPT or other Large Language Model (LLM) into a server, especially a public one like a Minecraft server (often associated with "MCP"), introduces unique challenges. It's crucial to have clear disclaimers to manage user expectations, limit your liability, and maintain a healthy community.

Here are essential points and disclaimers to consider, categorized for clarity.

---

### **Category 1: Nature of the AI & Accuracy of Information**

These disclaimers manage expectations about what the AI is and what it can do.

* **AI, Not Human:** "The chat assistant you are interacting with is an AI language model (powered by OpenAI's GPT technology). It is not a human, a server administrator, or a moderator. Its responses are generated algorithmically."
* **Potential for Inaccuracy:** "The AI's responses may be inaccurate, incomplete, or nonsensical. It can 'hallucinate' facts or make up information. Do not rely on it for critical in-game information (e.g., rare item locations, complex crafting recipes) or any real-world advice."
* **Knowledge Cutoff:** "The AI's knowledge is based on data up to a certain point in the past and it does not have real-time information. It will not be aware of recent server events, updates, player-built structures, or rule changes unless specifically programmed to be."
* **No Consciousness or Feelings:** "The AI does not have beliefs, opinions, or feelings. Its responses are a reflection of the patterns in the data it was trained on, not a personal viewpoint."
* **Potential for Bias:** "The AI may generate content that reflects biases present in its training data. We do not endorse any biased, offensive, or inappropriate statements made by the AI. Please report any such instances to the server staff."

---

### **Category 2: User Responsibility & Conduct**

These points outline how users are expected to behave when interacting with the AI.

* **User is Responsible:** "You are responsible for your interactions with the AI. Attempting to 'jailbreak,' manipulate, or trick the AI into violating server rules is a violation of server rules itself."
* **Do Not Share Personal Information:** "**NEVER** share personal information with the AI, including your real name, age, location, passwords, email address, or any other identifying details. While we strive for privacy, these conversations may be logged or processed by third parties."
* **AI is Not a Support Ticket:** "The AI is for general queries and entertainment. It cannot resolve player disputes, investigate griefing, issue refunds, or handle technical support requests. For these issues, please contact a human staff member through the proper channels (e.g., Discord ticket, /helpop command)."
* **Report Misconduct:** "If the AI generates content that is harmful, offensive, or breaks server rules, please take a screenshot and report it to the server staff immediately. This helps us improve the system."

---

### **Category 3: Privacy & Data Handling**

This is crucial for transparency and legal protection.

* **Interaction Logging:** "Please be aware that your conversations with the AI may be logged and reviewed by server administrators for the purposes of moderation, quality control, and system improvement."
* **Third-Party Data Processing:** "To function, this feature sends your prompts (the questions you ask) to OpenAI (or another third-party AI provider) for processing. By using this feature, you acknowledge and agree that your data will be handled according to their respective privacy policies and terms of service."
* **No Expectation of Privacy:** "Do not consider your conversations with the AI to be private. They are subject to review by staff and processing by third-party services."

---

### **Category 4: Liability & Service Availability**

These are the core legal-style disclaimers to limit your liability.

* **Use At Your Own Risk:** "This AI feature is provided on an 'as-is' and 'as-available' basis. You use it at your own risk. The server owners and staff are not liable for any damages, loss of items, misinformation, or negative experiences resulting from your use of the AI."
* **No Guarantee of Service:** "We reserve the right to modify, restrict, or disable the AI feature at any time, for any reason, without notice. Access to the feature is not a guaranteed part of the server experience."
* **Not Affiliated with OpenAI:** "This server is not an official partner of, nor is it endorsed by, OpenAI or any other AI provider. We are simply using their technology via their public API."

---

### **How to Present These Disclaimers**

You shouldn't just hide these in a long document. Make them accessible.

1.  **Initial Pop-up/Message:** The very first time a player uses the AI command, show them a condensed version of the key warnings (e.g., "This is an AI, not a human. It can be wrong. Do not share personal info. Full rules in /ai_rules.") and require them to agree.
2.  **A Dedicated Command:** Create a command like `/ai_rules`, `/ai_disclaimer`, or `/chatgpt_info` that prints the full list of points in the game chat.
3.  **Discord Channel:** Have a dedicated channel in your server's Discord (e.g., `#ai-info-and-rules`) with the complete disclaimers.
4.  **MOTD (Message of the Day):** Periodically include a short reminder in the server's MOTD, like "Remember to use our AI helper responsibly! /ai_rules for info."""}

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