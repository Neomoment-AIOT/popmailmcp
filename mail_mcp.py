"""
mail_mcp.py – Minimal MCP server for POP/IMAP/SMTP mailboxes.
Run with:  python mail_mcp.py            # HTTP on :8088 (default)
           MCP_TRANSPORT=stdio python mail_mcp.py   # for local CLI tests
"""
import os, ssl, base64, email.header, email.message, logging
from typing import List, Dict
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import poplib, imaplib, smtplib

load_dotenv()                           # pick up .env
LOG = logging.getLogger("mail_mcp")
logging.basicConfig(level=logging.INFO)

# ──────────────────────────  helpers  ────────────────────────── #

def _ssl_ctx() -> ssl.SSLContext | None:
    """Create a permissive SSL context if MAIL_SSL==1."""
    if os.getenv("MAIL_SSL", "1") == "1":
        ctx = ssl.create_default_context()
        if os.getenv("MAIL_ALLOW_SELF_SIGNED") == "1":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None

def _connect_pop() -> poplib.POP3 | poplib.POP3_SSL:
    host = os.environ["MAIL_HOST"]
    port = int(os.getenv("MAIL_POP_PORT", "110"))
    if _ssl_ctx():
        pop = poplib.POP3_SSL(host, port, context=_ssl_ctx())
    else:
        pop = poplib.POP3(host, port)
    pop.user(os.environ["MAIL_USER"])
    pop.pass_(os.environ["MAIL_PASS"])
    return pop

def _connect_imap() -> imaplib.IMAP4 | imaplib.IMAP4_SSL:
    host = os.environ["MAIL_HOST"]
    port = int(os.getenv("MAIL_IMAP_PORT", "993"))
    if _ssl_ctx():
        imap = imaplib.IMAP4_SSL(host, port, ssl_context=_ssl_ctx())
    else:
        imap = imaplib.IMAP4(host, port)
        imap.starttls(_ssl_ctx())
    imap.login(os.environ["MAIL_USER"], os.environ["MAIL_PASS"])
    imap.select("INBOX")            # default mailbox
    return imap

def _connect_smtp() -> smtplib.SMTP:
    host = os.environ["MAIL_HOST"]
    port = int(os.getenv("MAIL_SMTP_PORT", "587"))
    if _ssl_ctx() and port in (465, 587):      # implicit TLS (465) or upgrade (587)
        if port == 465:
            smtp = smtplib.SMTP_SSL(host, port, context=_ssl_ctx())
        else:
            smtp = smtplib.SMTP(host, port)
            smtp.starttls(context=_ssl_ctx())
    else:
        smtp = smtplib.SMTP(host, port)
    smtp.login(os.environ["MAIL_USER"], os.environ["MAIL_PASS"])
    return smtp

def _decode_header(raw: str) -> str:
    """Turn '=?UTF‑8?Q?=E2=9C=94?=' into readable text."""
    parts = email.header.decode_header(raw)
    return "".join(
        (b.decode(enc or "utf-8", "replace") if isinstance(b, bytes) else b)
        for b, enc in parts
    )

# ────────────────────────── CORS Configuration ──────────────────────────── #

# Fixed: 2025-07-26T22:59:00+05:00 - Updated to use Starlette CORSMiddleware per FastMCP documentation
# This replaces the custom middleware approach which couldn't inject HTTP headers properly
cors_middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins including ChatGPT web interface
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
        allow_credentials=False  # Disable credentials for security
    )
]

# ──────────────────────────  MCP  ────────────────────────────── #

# Fixed: 2025-07-26T14:07:03+05:00 - Removed description parameter as FastMCP doesn't support it
# Original code (commented out):
# mcp = FastMCP(
#     name="plain-mail-mcp",
#     version="1.0.0",
#     description="Connector that exposes POP/IMAP/SMTP tools."
# )

mcp = FastMCP(
    name="plain-mail-mcp",
    version="1.0.0"
)

# Fixed: 2025-07-26T23:03:00+05:00 - Add CORS middleware using properly formatted Middleware object
# This enables ChatGPT web interface connectivity by adding proper CORS headers
mcp.add_middleware(cors_middleware[0])  # Use the Middleware object from cors_middleware list

# ---------------- reading / listing ---------------- #

@mcp.tool(description="List newest messages (optionally only flagged).")
def list_messages(max_items: int = 10, flagged_only: bool = False) -> List[Dict]:
    """
    Returns a summary list.  Uses IMAP if available (better), otherwise POP.
    Each item = {uid, from, subject, date, is_flagged}
    """
    if os.getenv("MAIL_IMAP_PORT"):
        imap = _connect_imap()
        search_crit = '(FLAGGED)' if flagged_only else 'ALL'
        ok, data = imap.uid("SEARCH", None, search_crit)
        if ok != "OK":
            raise RuntimeError("IMAP SEARCH failed")
        uids = data[0].split()[-max_items:]     # newest last; slice
        results = []
        for uid in reversed(uids):
            ok, msgdata = imap.uid("FETCH", uid, "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            hdr_bytes = msgdata[0][1]
            msg = email.message_from_bytes(hdr_bytes)
            results.append({
                "uid": uid.decode(),
                "from": _decode_header(msg.get("From", "")),
                "subject": _decode_header(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "is_flagged": b"\\Flagged" in msgdata[0][0]
            })
        imap.logout()
        return results
    # ---------- POP fallback (no flags) ----------
    pop = _connect_pop()
    total, _ = pop.stat()
    msgs = []
    for i in range(max(1, total - max_items + 1), total + 1):
        hdr = pop.top(i, 0)[1]
        msg = email.message_from_bytes(b"\n".join(hdr))
        msgs.append({
            "uid": str(i),
            "from": _decode_header(msg.get("From", "")),
            "subject": _decode_header(msg.get("Subject", "")),
            "date": msg.get("Date", ""),
            "is_flagged": False
        })
    pop.quit()
    return list(reversed(msgs))

@mcp.tool(description="Download full RFC‑822 message by UID / POP ordinal.")
def get_message(uid: str) -> str:
    """
    Returns the raw message text.  Use IMAP UID or POP ordinal.
    """
    if os.getenv("MAIL_IMAP_PORT"):
        imap = _connect_imap()
        ok, data = imap.uid("FETCH", uid.encode(), "(RFC822)")
        imap.logout()
        if ok != "OK":
            raise RuntimeError("IMAP FETCH failed")
        return data[0][1].decode(errors="replace")
    pop = _connect_pop()
    msg_lines = pop.retr(int(uid))[1]
    pop.quit()
    return b"\n".join(msg_lines).decode(errors="replace")

@mcp.tool(description="Delete message by UID / POP ordinal.")
def delete_message(uid: str) -> str:
    if os.getenv("MAIL_IMAP_PORT"):
        imap = _connect_imap()
        imap.uid("STORE", uid, "+FLAGS.SILENT", "(\\Deleted)")
        imap.expunge()
        imap.logout()
    else:
        pop = _connect_pop()
        pop.dele(int(uid))
        pop.quit()
    return f"Message {uid} deleted."

# ---------------- flag / pin (IMAP only) ---------------- #

@mcp.tool(description="Flag (pin) a message (IMAP only).")
def flag_message(uid: str) -> str:
    if not os.getenv("MAIL_IMAP_PORT"):
        return "Flagging not supported on POP‑only mailboxes."
    imap = _connect_imap()
    imap.uid("STORE", uid, "+FLAGS.SILENT", "(\\Flagged)")
    imap.logout()
    return f"Message {uid} flagged."

@mcp.tool(description="Remove flag from a message (IMAP only).")
def unflag_message(uid: str) -> str:
    if not os.getenv("MAIL_IMAP_PORT"):
        return "Unflagging not supported on POP‑only mailboxes."
    imap = _connect_imap()
    imap.uid("STORE", uid, "-FLAGS.SILENT", "(\\Flagged)")
    imap.logout()
    return f"Message {uid} unflagged."

# ---------------- sending ---------------- #

@mcp.tool(description="Send an email.")
def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> str:
    """
    Simple text email.  Supports CC/BCC (comma‑separated).
    """
    msg = email.message.EmailMessage()
    msg["From"] = os.environ["MAIL_USER"]
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg.set_content(body)
    smtp = _connect_smtp()
    all_rcpts = [to] + [e.strip() for e in cc.split(",") if e] + [e.strip() for e in bcc.split(",") if e]
    smtp.send_message(msg, from_addr=os.environ["MAIL_USER"], to_addrs=all_rcpts)
    smtp.quit()
    return "Email sent."

# ---------------- main entry ---------------- #

if __name__ == "__main__":
    mode = os.getenv("MCP_TRANSPORT", "http")
    if mode == "stdio":
        mcp.run(transport="stdio")
    else:
        port = int(os.getenv("PORT", "8088"))
        # Fixed: 2025-07-26T23:01:00+05:00 - Reverting to basic approach since custom_middleware not supported
        # Will need to implement CORS through alternative method
        mcp.run(transport="http", host="0.0.0.0", port=port)
