#!/usr/bin/env python3
"""
Facebook Token Generator — AI Employee Gold Tier
-------------------------------------------------
Generates long-lived Facebook Page Access Token using your App ID and Secret.

Usage:
    python watchers/generate_facebook_token.py
    
This will:
1. Guide you to get a short-lived user token
2. Exchange it for a long-lived Page token
3. Help you find your Page ID and Instagram User ID
"""

import os
import sys
import webbrowser
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Installing python-dotenv...")
    os.system("pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests

# Your App Credentials
APP_ID = os.getenv("FACEBOOK_APP_ID", "1383922417086696")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "22d4377e9ea0963e8eba3123dc3f4647")

GRAPH_API = "https://graph.facebook.com/v19.0"


def print_step(num: int, text: str):
    """Print formatted step."""
    print(f"\n{'='*60}")
    print(f"Step {num}: {text}")
    print(f"{'='*60}")


def get_short_lived_token_url():
    """Generate URL to get short-lived user token."""
    redirect_uri = "https://developers.facebook.com/tools/explorer"
    scope = ",".join([
        "pages_manage_posts",
        "pages_read_engagement",
        "pages_read_user_content",
        "pages_manage_metadata",
        "instagram_basic",
        "instagram_manage_comments",
        "instagram_manage_insights"
    ])
    
    url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={APP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=token"
    )
    return url


def exchange_for_long_lived_user_token(short_lived_token: str) -> str:
    """Exchange short-lived user token for long-lived user token."""
    url = f"{GRAPH_API}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_lived_token
    }
    
    print("Exchanging for long-lived user token...")
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    
    if "access_token" in data:
        print(f"✅ Long-lived user token obtained!")
        print(f"   Token: {data['access_token'][:50]}...")
        if "expires_in" in data:
            print(f"   Expires in: {data['expires_in']} seconds")
        return data["access_token"]
    else:
        print(f"❌ Error: {data}")
        return None


def get_page_access_token(long_lived_user_token: str) -> tuple:
    """Get Page Access Token from user token."""
    url = f"{GRAPH_API}/me/accounts"
    params = {"access_token": long_lived_user_token}
    
    print("\nFetching your pages...")
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    
    if "data" not in data:
        print(f"❌ Error: {data}")
        return None, None
    
    pages = data["data"]
    if not pages:
        print("❌ No pages found. Please create a Facebook Page first.")
        return None, None
    
    print(f"\nFound {len(pages)} page(s):")
    for i, page in enumerate(pages, 1):
        print(f"  {i}. {page.get('name', 'Unknown')} (ID: {page['id']})")
    
    # Select first page or let user choose
    if len(pages) == 1:
        selected = pages[0]
    else:
        try:
            choice = input("\nSelect page number (default: 1): ").strip()
            idx = int(choice) - 1 if choice else 0
            selected = pages[idx]
        except (ValueError, IndexError):
            selected = pages[0]
    
    page_token = selected.get("access_token", "")
    page_id = selected.get("id", "")
    page_name = selected.get("name", "Unknown")
    
    print(f"\n✅ Page Access Token obtained!")
    print(f"   Page: {page_name}")
    print(f"   Page ID: {page_id}")
    print(f"   Token: {page_token[:50]}...")
    
    return page_token, page_id


def get_instagram_user_id(page_access_token: str, page_id: str) -> str:
    """Get Instagram User ID linked to the Facebook Page."""
    url = f"{GRAPH_API}/{page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": page_access_token
    }
    
    print("\nFetching Instagram Business Account...")
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    
    if "error" in data:
        print(f"❌ Error: {data['error']['message']}")
        print("   Make sure your Instagram account is connected to this Facebook Page.")
        return None
    
    ig_account = data.get("instagram_business_account")
    if not ig_account:
        print("⚠️  No Instagram Business Account linked to this Page.")
        print("   Go to: Facebook Page Settings → Instagram → Connect Account")
        return None
    
    ig_user_id = ig_account.get("id", "")
    print(f"✅ Instagram Business Account found!")
    print(f"   User ID: {ig_user_id}")
    
    return ig_user_id


def get_instagram_username(page_access_token: str, ig_user_id: str) -> str:
    """Get Instagram username from User ID."""
    url = f"{GRAPH_API}/{ig_user_id}"
    params = {
        "fields": "username",
        "access_token": page_access_token
    }
    
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    
    if "username" in data:
        return data["username"]
    return "unknown"


def update_env_file(page_token: str, page_id: str, ig_user_id: str):
    """Update .env file with tokens."""
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print(f"⚠️  .env file not found at {env_file}")
        return
    
    content = env_file.read_text(encoding="utf-8")
    
    # Update tokens
    if page_token:
        content = content.replace(
            "FACEBOOK_ACCESS_TOKEN=your_facebook_access_token_here",
            f"FACEBOOK_ACCESS_TOKEN={page_token}"
        )
    
    if page_id:
        content = content.replace(
            "FACEBOOK_PAGE_ID=your_facebook_page_id_here",
            f"FACEBOOK_PAGE_ID={page_id}"
        )
    
    if ig_user_id:
        content = content.replace(
            "INSTAGRAM_USER_ID=your_instagram_user_id_here",
            f"INSTAGRAM_USER_ID={ig_user_id}"
        )
        # Instagram uses same token as Facebook
        content = content.replace(
            "INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here",
            f"INSTAGRAM_ACCESS_TOKEN={page_token}"
        )
    
    env_file.write_text(content, encoding="utf-8")
    print(f"\n✅ Updated .env file with your tokens!")


def main():
    print("="*60)
    print("  Facebook Access Token Generator")
    print("  AI Employee Gold Tier")
    print("="*60)
    print(f"\nApp ID: {APP_ID}")
    print(f"App Secret: {APP_SECRET[:20]}...")
    
    print_step(1, "Get Short-Lived User Token")
    print("\n1. Click this URL to authorize the app:")
    url = get_short_lived_token_url()
    print(f"   {url}")
    print("\n2. Log in to Facebook and select your Page")
    print("3. Grant all permissions")
    print("4. Copy the 'Access Token' from the URL or page")
    
    # Try to open browser automatically
    try:
        webbrowser.open(url)
        print("\n✅ Opened browser for you!")
    except Exception:
        pass
    
    short_lived_token = input("\n5. Paste the short-lived access token here: ").strip()
    
    if not short_lived_token:
        print("❌ No token provided. Exiting.")
        sys.exit(1)
    
    print_step(2, "Exchange for Long-Lived User Token")
    long_lived_user_token = exchange_for_long_lived_user_token(short_lived_token)
    
    if not long_lived_user_token:
        print("❌ Failed to get long-lived token. Exiting.")
        sys.exit(1)
    
    print_step(3, "Get Page Access Token")
    page_token, page_id = get_page_access_token(long_lived_user_token)
    
    if not page_token:
        print("❌ Failed to get Page token. Exiting.")
        sys.exit(1)
    
    print_step(4, "Get Instagram User ID")
    ig_user_id = get_instagram_user_id(page_token, page_id)
    
    ig_username = ""
    if ig_user_id:
        ig_username = get_instagram_username(page_token, ig_user_id)
        print(f"   Username: @{ig_username}")
    
    print_step(5, "Save Configuration")
    update_env_file(page_token, page_id, ig_user_id)
    
    print("\n" + "="*60)
    print("  Configuration Complete!")
    print("="*60)
    print(f"\nYour .env file has been updated with:")
    print(f"  ✅ FACEBOOK_ACCESS_TOKEN")
    print(f"  ✅ FACEBOOK_PAGE_ID: {page_id}")
    print(f"  ✅ INSTAGRAM_ACCESS_TOKEN")
    print(f"  ✅ INSTAGRAM_USER_ID: {ig_user_id}")
    
    print("\nNext steps:")
    print("  1. Test connection: python watchers/test_facebook.py")
    print("  2. Run integration test: python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault")
    print("  3. Start monitoring: python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch")
    
    if not ig_user_id:
        print("\n⚠️  Instagram not connected. To connect:")
        print("   1. Go to your Facebook Page Settings")
        print("   2. Click 'Instagram'")
        print("   3. Click 'Connect Account'")
        print("   4. Log in to Instagram")
        print("   5. Run this script again")


if __name__ == "__main__":
    main()
