"""
Test mail server connectivity - Date: 2025-07-26 17:49
Diagnose the exact mail server connection issue
"""
import socket
import ssl
import poplib
import imaplib
import smtplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_socket_connection(host, port, timeout=10):
    """Test basic socket connection to host:port"""
    try:
        print(f"Testing socket connection to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"SUCCESS: Socket connection to {host}:{port} successful")
            return True
        else:
            print(f"FAILED: Socket connection to {host}:{port} failed (error code: {result})")
            return False
    except Exception as e:
        print(f"ERROR: Socket connection error: {e}")
        return False

def test_ssl_connection(host, port):
    """Test SSL connection to host:port"""
    try:
        print(f"Testing SSL connection to {host}:{port}...")
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        ssl_sock = context.wrap_socket(sock, server_hostname=host)
        ssl_sock.connect((host, port))
        ssl_sock.close()
        print(f"SUCCESS: SSL connection to {host}:{port} successful")
        return True
    except Exception as e:
        print(f"ERROR: SSL connection error: {e}")
        return False

def test_pop_connection():
    """Test POP3 connection"""
    try:
        print("Testing POP3 connection...")
        host = os.environ["MAIL_HOST"]
        port = int(os.getenv("MAIL_POP_PORT", "110"))
        user = os.environ["MAIL_USER"]
        password = os.environ["MAIL_PASS"]
        
        if os.getenv("MAIL_SSL", "1") == "1":
            pop = poplib.POP3_SSL(host, port, timeout=10)
        else:
            pop = poplib.POP3(host, port, timeout=10)
            
        pop.user(user)
        pop.pass_(password)
        msg_count, mailbox_size = pop.stat()
        pop.quit()
        
        print(f"SUCCESS: POP3 connection successful! Found {msg_count} messages")
        return True
    except Exception as e:
        print(f"ERROR: POP3 connection error: {e}")
        return False

def test_imap_connection():
    """Test IMAP connection"""
    try:
        print("Testing IMAP connection...")
        host = os.environ["MAIL_HOST"]
        port = int(os.getenv("MAIL_IMAP_PORT", "993"))
        user = os.environ["MAIL_USER"]
        password = os.environ["MAIL_PASS"]
        
        if os.getenv("MAIL_SSL", "1") == "1":
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            imap = imaplib.IMAP4_SSL(host, port, ssl_context=context)
        else:
            imap = imaplib.IMAP4(host, port)
            
        imap.login(user, password)
        imap.select("INBOX")
        status, messages = imap.search(None, 'ALL')
        msg_count = len(messages[0].split()) if messages[0] else 0
        imap.logout()
        
        print(f"SUCCESS: IMAP connection successful! Found {msg_count} messages")
        return True
    except Exception as e:
        print(f"ERROR: IMAP connection error: {e}")
        return False

def main():
    print("=== Mail Server Connectivity Test ===")
    
    # Print configuration
    print(f"Host: {os.getenv('MAIL_HOST', 'Not set')}")
    print(f"User: {os.getenv('MAIL_USER', 'Not set')}")
    print(f"POP Port: {os.getenv('MAIL_POP_PORT', 'Not set')}")
    print(f"IMAP Port: {os.getenv('MAIL_IMAP_PORT', 'Not set')}")
    print(f"SMTP Port: {os.getenv('MAIL_SMTP_PORT', 'Not set')}")
    print(f"SSL: {os.getenv('MAIL_SSL', 'Not set')}")
    print()
    
    host = os.getenv('MAIL_HOST')
    if not host:
        print("ERROR: MAIL_HOST not configured")
        return
    
    # Test basic connectivity
    pop_port = int(os.getenv('MAIL_POP_PORT', '110'))
    imap_port = int(os.getenv('MAIL_IMAP_PORT', '993'))
    smtp_port = int(os.getenv('MAIL_SMTP_PORT', '587'))
    
    print("1. Testing basic socket connectivity...")
    test_socket_connection(host, pop_port)
    test_socket_connection(host, imap_port)
    test_socket_connection(host, smtp_port)
    print()
    
    print("2. Testing SSL connectivity...")
    test_ssl_connection(host, imap_port)
    print()
    
    print("3. Testing mail protocol connections...")
    if os.getenv('MAIL_POP_PORT'):
        test_pop_connection()
    
    if os.getenv('MAIL_IMAP_PORT'):
        test_imap_connection()

if __name__ == "__main__":
    main()
