"""
Advanced mail server authentication test - Date: 2025-07-26 17:53
Test different authentication methods and get detailed error information
"""
import poplib
import imaplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pop3_variations():
    """Test different POP3 authentication variations"""
    host = os.environ["MAIL_HOST"]
    port = int(os.getenv("MAIL_POP_PORT", "110"))
    user = os.environ["MAIL_USER"]
    password = os.environ["MAIL_PASS"]
    
    print("=== Testing POP3 Authentication Variations ===")
    
    # Test 1: Plain POP3
    try:
        print(f"1. Testing plain POP3 connection to {host}:{port}")
        pop = poplib.POP3(host, port, timeout=10)
        print(f"   Server welcome: {pop.getwelcome()}")
        
        # Try authentication
        try:
            pop.user(user)
            response = pop.pass_(password)
            print(f"   Authentication SUCCESS: {response}")
            msg_count, mailbox_size = pop.stat()
            print(f"   Found {msg_count} messages, {mailbox_size} bytes")
            pop.quit()
            return True
        except Exception as auth_error:
            print(f"   Authentication FAILED: {auth_error}")
            try:
                pop.quit()
            except:
                pass
    except Exception as e:
        print(f"   Connection FAILED: {e}")
    
    # Test 2: Try username without domain
    try:
        print(f"2. Testing with username without domain")
        username_only = user.split('@')[0]  # Extract 'suhail.c' from 'suhail.c@neomoment.org'
        pop = poplib.POP3(host, port, timeout=10)
        pop.user(username_only)
        response = pop.pass_(password)
        print(f"   Authentication SUCCESS with {username_only}: {response}")
        msg_count, mailbox_size = pop.stat()
        print(f"   Found {msg_count} messages, {mailbox_size} bytes")
        pop.quit()
        return True
    except Exception as e:
        print(f"   Authentication FAILED with username only: {e}")
        try:
            pop.quit()
        except:
            pass
    
    # Test 3: Try different password variations
    print(f"3. Current credentials being tested:")
    print(f"   Username: {user}")
    print(f"   Password: {password}")
    
    return False

def test_imap_variations():
    """Test different IMAP authentication variations"""
    host = os.environ["MAIL_HOST"]
    port = int(os.getenv("MAIL_IMAP_PORT", "143"))
    user = os.environ["MAIL_USER"]
    password = os.environ["MAIL_PASS"]
    
    print("\\n=== Testing IMAP Authentication Variations ===")
    
    # Test 1: Plain IMAP
    try:
        print(f"1. Testing plain IMAP connection to {host}:{port}")
        imap = imaplib.IMAP4(host, port)
        print(f"   Server capabilities: {imap.capabilities}")
        
        # Try authentication
        try:
            result = imap.login(user, password)
            print(f"   Authentication SUCCESS: {result}")
            imap.select("INBOX")
            status, messages = imap.search(None, 'ALL')
            msg_count = len(messages[0].split()) if messages[0] else 0
            print(f"   Found {msg_count} messages")
            imap.logout()
            return True
        except Exception as auth_error:
            print(f"   Authentication FAILED: {auth_error}")
            try:
                imap.logout()
            except:
                pass
    except Exception as e:
        print(f"   Connection FAILED: {e}")
    
    # Test 2: Try username without domain
    try:
        print(f"2. Testing with username without domain")
        username_only = user.split('@')[0]
        imap = imaplib.IMAP4(host, port)
        result = imap.login(username_only, password)
        print(f"   Authentication SUCCESS with {username_only}: {result}")
        imap.select("INBOX")
        status, messages = imap.search(None, 'ALL')
        msg_count = len(messages[0].split()) if messages[0] else 0
        print(f"   Found {msg_count} messages")
        imap.logout()
        return True
    except Exception as e:
        print(f"   Authentication FAILED with username only: {e}")
        try:
            imap.logout()
        except:
            pass
    
    return False

def main():
    print("=== Advanced Mail Authentication Test ===")
    print(f"Host: {os.getenv('MAIL_HOST')}")
    print(f"User: {os.getenv('MAIL_USER')}")
    print(f"Password: {os.getenv('MAIL_PASS')}")
    print()
    
    pop3_success = test_pop3_variations()
    imap_success = test_imap_variations()
    
    print("\\n=== Summary ===")
    if pop3_success:
        print("SUCCESS: POP3 authentication working")
    else:
        print("FAILED: POP3 authentication failed")
        
    if imap_success:
        print("SUCCESS: IMAP authentication working")
    else:
        print("FAILED: IMAP authentication failed")
        
    if not pop3_success and not imap_success:
        print("\\n=== Possible Solutions ===")
        print("1. Check if the email account exists and is active")
        print("2. Verify the password is correct")
        print("3. Check if the mail server requires app-specific passwords")
        print("4. Contact the hosting provider (webhostbox.net) for mail server settings")
        print("5. Check if mail services are enabled for this domain")

if __name__ == "__main__":
    main()
