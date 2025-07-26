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
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

mcp = FastMCP("plain-mail-mcp")

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = mcp.http_app(path="/mcp", custom_middleware=middleware)

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
def get_message(uid: int) -> str    :
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
    uvicorn.run(app, host="0.0.0.0", port=8088)
    