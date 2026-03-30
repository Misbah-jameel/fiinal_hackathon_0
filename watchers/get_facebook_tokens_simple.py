#!/usr/bin/env python3
"""
Facebook Token Setup - Simple Manual Guide
===========================================
This script provides direct links and instructions to get your tokens manually.

Usage:
    python watchers/get_facebook_tokens_simple.py
"""

import os
import webbrowser
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Your App Credentials
APP_ID = os.getenv("FACEBOOK_APP_ID", "1383922417086696")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "22d4377e9ea0963e8eba3123dc3f4647")

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(num, text):
    print(f"\n{'─'*70}")
    print(f"STEP {num}: {text}")
    print(f"{'─'*70}")

def main():
    print_header("Facebook Token Setup - Manual Guide")
    print(f"\nApp ID: {APP_ID}")
    print(f"App Secret: {APP_SECRET[:20]}...{APP_SECRET[-10:]}")
    
    print_step(1, "Open Graph API Explorer")
    
    url = f"https://developers.facebook.com/tools/explorer/?client_id={APP_ID}"
    print(f"\n1. Click this URL (or copy to browser):")
    print(f"   {url}")
    
    try:
        webbrowser.open(url)
        print("\n   ✅ Opened in browser!")
    except:
        pass
    
    print_step(2, "Get User Access Token")
    
    print("""
In the Graph API Explorer:

1. Click "Get Token" button (top right)
2. Select "Get User Token"
3. Check these permissions:
   ✅ pages_manage_posts
   ✅ pages_read_engagement  
   ✅ pages_read_user_content
   ✅ pages_manage_metadata
   ✅ instagram_basic
   ✅ instagram_manage_comments
   ✅ instagram_manage_insights

4. Click "Generate Access Token"
5. Log in to Facebook if prompted
6. Select your Facebook Page
7. Click "Continue" to approve
""")
    
    print_step(3, "Copy Your User Token")
    
    print("""
After approval, you'll see an access token in the box.
It looks like: EAAc1234567890abcdef...

Copy this token!
""")
    
    user_token = input("Paste your User Access Token here: ").strip()
    
    if not user_token:
        print("\n❌ No token provided. Exiting.")
        return
    
    print("\n✅ Got User Token!")
    
    print_step(4, "Get Your Page Access Token")
    
    print(f"""
Now let's get your Page token.

1. In the Graph API Explorer, make sure your token is selected
2. In the request box, type:
   
   GET /me/accounts
   
3. Click "Submit"

You'll see a response like:
{{
  "data": [
    {{
      "name": "Your Page Name",
      "id": "123456789012345",
      "access_token": "EAAc...PageTokenHere..."
    }}
  ]
}}

Copy BOTH:
- The "id" (this is your PAGE ID)
- The "access_token" (this is your PAGE TOKEN)
""")
    
    page_id = input("Paste your Page ID here: ").strip()
    page_token = input("Paste your Page Access Token here: ").strip()
    
    if not page_id or not page_token:
        print("\n❌ Missing information. Exiting.")
        return
    
    print("\n✅ Got Page ID and Token!")
    
    print_step(5, "Get Instagram User ID (Optional)")
    
    print(f"""
If you have Instagram Business connected:

1. In Graph API Explorer, type:
   
   GET /{page_id}?fields=instagram_business_account
   
2. Click "Submit"

If you see:
{{
  "instagram_business_account": {{
    "id": "17841400000000000"
  }}
}}

Then copy the Instagram ID!

If you get an error or no account, Instagram is not connected.
That's OK - you can skip this step.
""")
    
    ig_response = input("Do you see an Instagram Business Account? (y/n): ").strip().lower()
    
    ig_user_id = ""
    ig_token = ""
    
    if ig_response == 'y':
        ig_user_id = input("Paste your Instagram User ID: ").strip()
        ig_token = page_token  # Instagram uses same token
        print("\n✅ Got Instagram User ID!")
    else:
        print("\n⚠️  Skipping Instagram (you can add it later)")
        print("   To connect: Facebook Page Settings → Instagram → Connect Account")
    
    print_step(6, "Save Configuration")
    
    # Update .env file
    env_file = Path(__file__).parent.parent / ".env"
    
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        
        # Replace placeholders
        replacements = {
            "FACEBOOK_ACCESS_TOKEN=your_facebook_access_token_here": f"FACEBOOK_ACCESS_TOKEN={page_token}",
            "FACEBOOK_PAGE_ID=your_facebook_page_id_here": f"FACEBOOK_PAGE_ID={page_id}",
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if ig_user_id:
            content = content.replace(
                "INSTAGRAM_USER_ID=your_instagram_user_id_here",
                f"INSTAGRAM_USER_ID={ig_user_id}"
            )
            content = content.replace(
                "INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here",
                f"INSTAGRAM_ACCESS_TOKEN={ig_token}"
            )
        
        env_file.write_text(content, encoding="utf-8")
        print(f"\n✅ Updated .env file!")
    else:
        print(f"\n⚠️  .env file not found at {env_file}")
        print("\nAdd these manually to your .env file:")
        print(f"   FACEBOOK_ACCESS_TOKEN={page_token}")
        print(f"   FACEBOOK_PAGE_ID={page_id}")
        if ig_user_id:
            print(f"   INSTAGRAM_USER_ID={ig_user_id}")
            print(f"   INSTAGRAM_ACCESS_TOKEN={ig_token}")
    
    print_step(7, "Test Configuration")
    
    print("\n✅ Configuration Complete!")
    print("\nYour .env file now has:")
    print(f"   ✅ FACEBOOK_ACCESS_TOKEN: {page_token[:30]}...")
    print(f"   ✅ FACEBOOK_PAGE_ID: {page_id}")
    if ig_user_id:
        print(f"   ✅ INSTAGRAM_USER_ID: {ig_user_id}")
    
    print("\n" + "="*70)
    print("  Next Steps")
    print("="*70)
    print("""
1. Test your connection:
   python watchers/test_facebook.py

2. Run full integration test:
   python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault

3. Start monitoring:
   python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch

4. Post to Facebook (test):
   claude /social_post_facebook --message "Hello from AI Employee!"
""")
    
    print("\n💡 Token Expiry:")
    print("   Your Page Access Token should last ~60 days")
    print("   Run this script again to refresh tokens")
    print("\n📖 Full documentation: docs/FACEBOOK_TOKEN_SETUP.md")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
