#!/usr/bin/env python3
"""
Generate Long-Lived Facebook Access Token
------------------------------------------
This script helps you exchange a short-lived token for a long-lived token.

Usage:
  python generate_facebook_token.py
"""

import requests
import json

# Your app credentials
APP_ID = "1473105401145810"
APP_SECRET = "8e5e356462cec22f0fa5fcb37c807cbd"
SHORT_LIVED_TOKEN = "EAALbZB9C9WHwBRFGZAMsCShZByHACizvqyQVOy9BzD540iV5ZC0xnFlrwF4wP5VbRINW6AZAGXjTenGFFy8SxSmnefj7ZC014xmEvO3tHLVbIdZBMJkAw6uGnBZCYdkyyX5pl1mIvoSMkQP8UB8ZAcjcgeHvqmuVe7aGwqqf9gjS51tkZBLVW6lr9RgZAN7lHZCTIzvynUQ4MMwxCgpgtaaGAgEXYDrlciNzuX0MFnWt4IZAhksSQZC3KWVMZBNO40EhMVFE2DG7oxupwmytSiNmHyL1WU4h8S6"

def exchange_for_long_lived_token(short_token, app_id, app_secret):
    """Exchange short-lived token for long-lived token (60 days)."""
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "access_token" in data:
            return {
                "success": True,
                "access_token": data["access_token"],
                "token_type": data.get("token_type", "bearer"),
                "expires_in": data.get("expires_in", "N/A")
            }
        else:
            return {
                "success": False,
                "error": data.get("error", {}).get("message", "Unknown error")
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_page_access_token(page_id, user_token):
    """Get Page Access Token from User Token."""
    url = f"https://graph.facebook.com/v19.0/{page_id}"
    params = {
        "fields": "access_token,name",
        "access_token": user_token
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "access_token" in data:
            return {
                "success": True,
                "page_access_token": data["access_token"],
                "page_name": data.get("name", "Unknown"),
                "page_id": page_id
            }
        else:
            return {
                "success": False,
                "error": "No access_token in response"
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_instagram_user_id(page_id, user_token):
    """Get Instagram Business Account ID."""
    url = f"https://graph.facebook.com/v19.0/{page_id}"
    params = {
        "fields": "instagram_business_account{id,username}",
        "access_token": user_token
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "instagram_business_account" in data:
            ig_account = data["instagram_business_account"]
            return {
                "success": True,
                "instagram_user_id": ig_account.get("id"),
                "instagram_username": ig_account.get("username")
            }
        else:
            return {
                "success": False,
                "error": "No Instagram Business Account linked"
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 60)
    print("  Facebook Long-Lived Token Generator")
    print("=" * 60)
    print()
    
    # Step 1: Exchange for long-lived user token
    print("Step 1: Exchanging for long-lived user token...")
    result = exchange_for_long_lived_token(SHORT_LIVED_TOKEN, APP_ID, APP_SECRET)
    
    if result["success"]:
        print(f"✅ Success!")
        print(f"   Long-lived token: {result['access_token'][:50]}...")
        print(f"   Expires in: {result.get('expires_in', 'N/A')} seconds")
        print()
        
        long_lived_token = result["access_token"]
        
        # Step 2: Get Page Access Token
        print("Step 2: Getting Page Access Token...")
        page_id = "804824538765436"
        page_result = get_page_access_token(page_id, long_lived_token)
        
        if page_result["success"]:
            print(f"✅ Page Access Token obtained!")
            print(f"   Page Name: {page_result['page_name']}")
            print(f"   Page ID: {page_result['page_id']}")
            print(f"   Page Token: {page_result['page_access_token'][:50]}...")
            print()
            
            # Step 3: Get Instagram User ID
            print("Step 3: Getting Instagram Business Account...")
            ig_result = get_instagram_user_id(page_id, long_lived_token)
            
            if ig_result["success"]:
                print(f"✅ Instagram Business Account found!")
                print(f"   Username: @{ig_result['instagram_username']}")
                print(f"   User ID: {ig_result['instagram_user_id']}")
                print()
                
                # Display final configuration
                print("=" * 60)
                print("  .env Configuration")
                print("=" * 60)
                print(f"""
FACEBOOK_APP_ID={APP_ID}
FACEBOOK_APP_SECRET={APP_SECRET}
FACEBOOK_ACCESS_TOKEN={page_result['page_access_token']}
FACEBOOK_PAGE_ID={page_result['page_id']}
INSTAGRAM_ACCESS_TOKEN={page_result['page_access_token']}
INSTAGRAM_USER_ID={ig_result['instagram_user_id']}
""")
                print("=" * 60)
                print("Copy these values to your .env file!")
                print("=" * 60)
            else:
                print(f"⚠️  Instagram not linked: {ig_result['error']}")
                print()
                print("Make sure your Instagram Business account is linked to this Facebook Page.")
                
                # Show config without Instagram
                print("=" * 60)
                print("  .env Configuration (Facebook only)")
                print("=" * 60)
                print(f"""
FACEBOOK_APP_ID={APP_ID}
FACEBOOK_APP_SECRET={APP_SECRET}
FACEBOOK_ACCESS_TOKEN={page_result['page_access_token']}
FACEBOOK_PAGE_ID={page_result['page_id']}
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_USER_ID=
""")
        else:
            print(f"❌ Failed to get Page Access Token: {page_result['error']}")
    else:
        print(f"❌ Failed: {result['error']}")
        print()
        print("Your short-lived token may have expired.")
        print("Please get a new token from: https://developers.facebook.com/tools/explorer/")

if __name__ == "__main__":
    main()
