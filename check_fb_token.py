#!/usr/bin/env python3
"""
Quick Facebook/Instagram Token Test
------------------------------------
Simple test to check if your credentials are working.

Usage:
  python check_fb_token.py
"""

import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

def test_facebook_token():
    """Test Facebook access token."""
    token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    
    print("=" * 60)
    print("  Facebook Token Test")
    print("=" * 60)
    print()
    
    if not token:
        print("❌ FACEBOOK_ACCESS_TOKEN not set in .env")
        return False
    
    if not page_id:
        print("❌ FACEBOOK_PAGE_ID not set in .env")
        return False
    
    # Test 1: Check token validity
    print("Test 1: Checking token validity...")
    url = "https://graph.facebook.com/v19.0/me"
    params = {
        "access_token": token,
        "fields": "id,name"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"❌ Token invalid: {data['error'].get('message', 'Unknown error')}")
            print()
            print("Solution:")
            print("  1. Go to: https://developers.facebook.com/tools/explorer/")
            print("  2. Select your app")
            print("  3. Get Token → Get User Access Token")
            print("  4. Get Long-Lived User Access Token")
            print("  5. Update .env with new token")
            return False
        else:
            print(f"✅ Token valid!")
            print(f"   User: {data.get('name', 'Unknown')} (ID: {data.get('id')})")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Test 2: Check Page access
    print("Test 2: Checking Page access...")
    url = f"https://graph.facebook.com/v19.0/{page_id}"
    params = {
        "access_token": token,
        "fields": "id,name,fan_count"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"❌ Page access failed: {data['error'].get('message', 'Unknown error')}")
            return False
        else:
            print(f"✅ Page accessible!")
            print(f"   Page: {data.get('name', 'Unknown')}")
            print(f"   Fans: {data.get('fan_count', 'N/A')}")
            print(f"   ID: {data.get('id')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Test 3: Get Page posts
    print("Test 3: Checking Page posts...")
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    params = {
        "access_token": token,
        "limit": 1
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"⚠️  Cannot access posts: {data['error'].get('message', 'Unknown error')}")
        else:
            posts_count = len(data.get("data", []))
            print(f"✅ Posts accessible! Found {posts_count} recent post(s)")
    except Exception as e:
        print(f"⚠️  Error: {e}")
    
    print()
    return True


def test_instagram_token():
    """Test Instagram access token."""
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    user_id = os.getenv("INSTAGRAM_USER_ID", "")
    
    print("=" * 60)
    print("  Instagram Token Test")
    print("=" * 60)
    print()
    
    if not token:
        print("❌ INSTAGRAM_ACCESS_TOKEN not set in .env")
        return False
    
    if not user_id:
        print("❌ INSTAGRAM_USER_ID not set in .env")
        return False
    
    # Test: Get Instagram Business account info
    print("Test: Checking Instagram Business Account...")
    url = f"https://graph.facebook.com/v19.0/{user_id}"
    params = {
        "access_token": token,
        "fields": "id,username,followers_count,media_count"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"❌ Instagram access failed: {data['error'].get('message', 'Unknown error')}")
            print()
            print("Possible solutions:")
            print("  1. Make sure Instagram is a Business Account")
            print("  2. Link Instagram to your Facebook Page")
            print("  3. Get Instagram Graph API permissions")
            print("  4. Run: GET /me?fields=instagram_business_account")
            return False
        else:
            print(f"✅ Instagram Business Account accessible!")
            print(f"   Username: @{data.get('username', 'Unknown')}")
            print(f"   Followers: {data.get('followers_count', 'N/A')}")
            print(f"   Posts: {data.get('media_count', 'N/A')}")
            print(f"   ID: {data.get('id')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Test: Get Instagram media
    print("Test: Checking Instagram media...")
    url = f"https://graph.facebook.com/v19.0/{user_id}/media"
    params = {
        "access_token": token,
        "limit": 1
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"⚠️  Cannot access media: {data['error'].get('message', 'Unknown error')}")
        else:
            media_count = len(data.get("data", []))
            print(f"✅ Media accessible! Found {media_count} recent post(s)")
    except Exception as e:
        print(f"⚠️  Error: {e}")
    
    print()
    return True


def main():
    print()
    print("🔍 Facebook & Instagram Credential Checker")
    print()
    
    fb_ok = test_facebook_token()
    print()
    ig_ok = test_instagram_token()
    
    print("=" * 60)
    print("  Final Summary")
    print("=" * 60)
    print()
    
    if fb_ok and ig_ok:
        print("✅ ALL TESTS PASSED!")
        print()
        print("Your credentials are working correctly.")
        print("You can now run:")
        print("  python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch")
    elif fb_ok:
        print("⚠️  PARTIAL SUCCESS")
        print()
        print("✅ Facebook: Working")
        print("❌ Instagram: Needs setup")
    elif ig_ok:
        print("⚠️  PARTIAL SUCCESS")
        print()
        print("❌ Facebook: Needs setup")
        print("✅ Instagram: Working")
    else:
        print("❌ ALL TESTS FAILED")
        print()
        print("Both Facebook and Instagram need setup.")
        print()
        print("Next steps:")
        print("  1. Go to: https://developers.facebook.com/tools/explorer/")
        print("  2. Select your app (1274097058270498)")
        print("  3. Get Token → Get User Access Token")
        print("  4. Select permissions:")
        print("     - pages_manage_posts")
        print("     - pages_read_engagement")
        print("     - instagram_basic")
        print("     - instagram_manage_comments")
        print("  5. Get Long-Lived User Access Token")
        print("  6. Update .env file")
    
    print()


if __name__ == "__main__":
    main()
