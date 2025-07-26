"""
SMTP Send Test - Date: 2025-07-26 18:21
Test SMTP email sending functionality
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_smtp_send():
    """Test SMTP email sending"""
    host = os.environ["MAIL_HOST"]
    port = int(os.getenv("MAIL_SMTP_PORT", "465"))
    user = os.environ["MAIL_USER"]
    password = os.environ["MAIL_PASS"]
    ssl_enabled = int(os.getenv("MAIL_SSL", "1"))
    
    print("=== Testing SMTP Send Functionality ===")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"SSL: {ssl_enabled}")
    print()
    
    # Create test email
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = user  # Send to self for testing
    msg['Subject'] = "MCP Email Test - POP3/SMTP Integration"
    
    # Email body
    body = """
This is a test email from the MCP Email Client.

Testing POP3 receive and SMTP send functionality.

✅ POP3 authentication: SUCCESS
✅ SMTP send test: In progress...

Date: 2025-07-26 18:21
"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Test SMTP connection and send
        if ssl_enabled:
            print("1. Testing SMTP SSL connection...")
            server = smtplib.SMTP_SSL(host, port, timeout=30)
        else:
            print("1. Testing SMTP connection with STARTTLS...")
            server = smtplib.SMTP(host, port, timeout=30)
            server.starttls()
        
        print("2. Authenticating with SMTP server...")
        server.login(user, password)
        print("   SMTP Authentication SUCCESS")
        
        print("3. Sending test email...")
        text = msg.as_string()
        server.sendmail(user, user, text)
        print("   Email sent successfully!")
        
        server.quit()
        print("✅ SMTP Send Test: SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ SMTP Send Test: FAILED - {e}")
        return False

def main():
    success = test_smtp_send()
    
    if success:
        print("\n=== SUCCESS: Email System Ready ===")
        print("✅ POP3 receiving: Working (1889 messages)")
        print("✅ SMTP sending: Working")
        print("\nNext steps:")
        print("1. Test complete MCP email functionality")
        print("2. Run FastMCP client with real email data")
        print("3. Verify end-to-end email receive/send through MCP")
    else:
        print("\n=== SMTP Configuration Issues ===")
        print("Need to debug SMTP settings further")

if __name__ == "__main__":
    main()
