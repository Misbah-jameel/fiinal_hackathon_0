#!/usr/bin/env python3
"""
Facebook & Instagram Connection Test — AI Employee Gold Tier
------------------------------------------------------------
Tests your Facebook/Instagram credentials before running the watcher.

Usage:
    python watchers/test_facebook.py
    python watchers/test_facebook.py --platform facebook
    python watchers/test_facebook.py --platform instagram
"""

import os
import sys
import json
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

GRAPH_API = "https://graph.facebook.com/v19.0"


def test_facebook():
    token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")

    print("\n── Facebook ──────────────────────────────")
    if not token:
        print("❌ FACEBOOK_ACCESS_TOKEN not set in .env")
        return False
    if not page_id:
        print("❌ FACEBOOK_PAGE_ID not set in .env")
        return False

    # Test page info
    resp = requests.get(f"{GRAPH_API}/{page_id}", params={
        "fields": "name,fan_count,talking_about_count",
        "access_token": token,
    }, timeout=10)
    data = resp.json()

    if "error" in data:
        print(f"❌ Graph API error: {data['error']['message']}")
        return False

    print(f"✅ Page: {data.get('name', 'unknown')}")
    print(f"   Fans: {data.get('fan_count', 0)}")
    print(f"   Talking about: {data.get('talking_about_count', 0)}")
    return True


def test_instagram():
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    user_id = os.getenv("INSTAGRAM_USER_ID", "")

    print("\n── Instagram ─────────────────────────────")
    if not token:
        print("❌ INSTAGRAM_ACCESS_TOKEN not set in .env")
        return False
    if not user_id:
        print("❌ INSTAGRAM_USER_ID not set in .env")
        return False

    # Test IG account info
    resp = requests.get(f"{GRAPH_API}/{user_id}", params={
        "fields": "username,followers_count,media_count",
        "access_token": token,
    }, timeout=10)
    data = resp.json()

    if "error" in data:
        print(f"❌ Graph API error: {data['error']['message']}")
        return False

    print(f"✅ Instagram: @{data.get('username', 'unknown')}")
    print(f"   Followers: {data.get('followers_count', 0)}")
    print(f"   Posts: {data.get('media_count', 0)}")
    return True


def get_instagram_user_id():
    """Helper: find your Instagram User ID from the linked Facebook Page."""
    token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")

    if not token or not page_id:
        print("Set FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID first")
        return

    resp = requests.get(f"{GRAPH_API}/{page_id}", params={
        "fields": "instagram_business_account",
        "access_token": token,
    }, timeout=10)
    data = resp.json()

    ig = data.get("instagram_business_account", {})
    if ig:
        print(f"\n✅ Your INSTAGRAM_USER_ID = {ig.get('id')}")
        print("   Add this to your .env file!")
    else:
        print("\n⚠️  No Instagram Business Account linked to this Facebook Page.")
        print("   Go to: Facebook Page Settings → Instagram → Connect Account")


def main():
    parser = argparse.ArgumentParser(description="Test Facebook/Instagram credentials")
    parser.add_argument("--platform", choices=["facebook", "instagram", "both"], default="both")
    parser.add_argument("--get-ig-id", action="store_true", help="Find Instagram User ID from Page")
    args = parser.parse_args()

    print("=" * 50)
    print("  Facebook/Instagram Credential Test")
    print("=" * 50)

    if args.get_ig_id:
        get_instagram_user_id()
        return

    results = {}
    if args.platform in ("facebook", "both"):
        results["facebook"] = test_facebook()
    if args.platform in ("instagram", "both"):
        results["instagram"] = test_instagram()

    print("\n── Summary ───────────────────────────────")
    all_ok = True
    for p, ok in results.items():
        status = "✅ Ready" if ok else "❌ Needs setup"
        print(f"   {p.capitalize()}: {status}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n✅ All credentials valid! Start watcher:")
        print("   python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch")
    else:
        print("\n💡 Run for setup guide:")
        print("   python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --auth")


if __name__ == "__main__":
    main()
