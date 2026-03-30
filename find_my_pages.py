#!/usr/bin/env python3
"""
Find Your Facebook Pages
-------------------------
This script lists all Facebook Pages you have access to.

Usage:
  python find_my_pages.py
"""

import requests
from dotenv import load_dotenv
import os

load_dotenv()

def find_pages():
    """List all Pages accessible to the user token."""
    # Use fresh short-lived token directly
    SHORT_LIVED_TOKEN = "EAALbZB9C9WHwBRFGZAMsCShZByHACizvqyQVOy9BzD540iV5ZC0xnFlrwF4wP5VbRINW6AZAGXjTenGFFy8SxSmnefj7ZC014xmEvO3tHLVbIdZBMJkAw6uGnBZCYdkyyX5pl1mIvoSMkQP8UB8ZAcjcgeHvqmuVe7aGwqqf9gjS51tkZBLVW6lr9RgZAN7lHZCTIzvynUQ4MMwxCgpgtaaGAgEXYDrlciNzuX0MFnWt4IZAhksSQZC3KWVMZBNO40EhMVFE2DG7oxupwmytSiNmHyL1WU4h8S6"
    app_id = "1473105401145810"
    app_secret = "8e5e356462cec22f0fa5fcb37c807cbd"
    
    print("=" * 60)
    print("  Find Your Facebook Pages")
    print("=" * 60)
    print()
    
    # First, exchange for long-lived token if needed
    token = SHORT_LIVED_TOKEN
    
    # Exchange for long-lived token
    print("Step 1: Getting long-lived user token...")
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "access_token" not in data:
        print(f"❌ Failed: {data.get('error', {}).get('message', 'Unknown error')}")
        return
    
    long_lived_token = data["access_token"]
    print(f"✅ Long-lived token obtained (expires in {data.get('expires_in', 'N/A')}s)")
    print()
    
    # Get user info
    print("Step 2: Getting user info...")
    url = "https://graph.facebook.com/v19.0/me"
    params = {"access_token": long_lived_token}
    response = requests.get(url, params=params)
    user = response.json()
    print(f"✅ User: {user.get('name', 'Unknown')} (ID: {user.get('id')})")
    print()
    
    # Get pages
    print("Step 3: Getting your Pages...")
    url = "https://graph.facebook.com/v19.0/me/accounts"
    params = {
        "access_token": long_lived_token,
        "fields": "id,name,access_token,category"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    print()
    print("=" * 60)
    print("  Your Facebook Pages")
    print("=" * 60)
    
    if "data" not in data or len(data["data"]) == 0:
        print()
        print("❌ No Pages found!")
        print()
        print("You need to CREATE a Facebook Page first:")
        print("  1. Go to: https://www.facebook.com/pages/create")
        print("  2. Create a Page for your AI Employee project")
        print("  3. Come back and run this script again")
        print()
        print("OR if you already have a Page:")
        print("  - Make sure you're an admin of the Page")
        print("  - The Page might be under a different Facebook account")
        return
    
    pages = data["data"]
    
    for i, page in enumerate(pages, 1):
        print()
        print(f"Page #{i}:")
        print(f"  Name: {page.get('name', 'Unknown')}")
        print(f"  ID: {page.get('id')}")
        print(f"  Category: {page.get('category', 'N/A')}")
        print(f"  Access Token: {page.get('access_token', '')[:50]}...")
    
    print()
    print("=" * 60)
    print("  Recommended .env Configuration")
    print("=" * 60)
    
    if len(pages) > 0:
        page = pages[0]  # Use first page
        print(f"""
# Use this Page:
FACEBOOK_ACCESS_TOKEN={page.get('access_token', '')}
FACEBOOK_PAGE_ID={page.get('id')}
INSTAGRAM_ACCESS_TOKEN={page.get('access_token', '')}
INSTAGRAM_USER_ID=(get from Graph API after linking Instagram)
""")
    
    print("=" * 60)


if __name__ == "__main__":
    find_pages()
