#!/usr/bin/env python3
"""
Facebook Token Completer - Uses the token you provided
"""

import os
import requests
from pathlib import Path

# Your credentials
APP_ID = "1383922417086696"
APP_SECRET = "22d4377e9ea0963e8eba3123dc3f4647"
USER_TOKEN = "EAATqq4wRMOgBQZCGj4Fl6Cq5TcX3VeOd6zRCvrlG8GJsln177UCu7YPk0oigIRZBBuZC8Mn8HwBc3zUaGjdQP2Ab44NBZAgWZC56kebPYZCcoeIR1HZBvCBkYfpbhrHILfyzHoYtpeyZAZAveBL41NCcF1BwPnVeXfPwPlDiP3OnHsznWZBxxLvKeTKJvZCaTwf9iX0QGJV8qU4LQfZAOx6zzfLf7zo3DkrAwHV0Aux5zBBkp2iXLDej0ZB2Ql6ze6l9II8Qv0dU2ip30ubrNOSbn"

GRAPH_API = "https://graph.facebook.com/v19.0"

def main():
    print("="*70)
    print("  Facebook Token Setup - Auto Completer")
    print("="*70)
    
    # Step 1: Get Pages
    print("\n📄 Fetching your Facebook Pages...")
    url = f"{GRAPH_API}/me/accounts"
    params = {"access_token": USER_TOKEN}
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        if "error" in data:
            print(f"❌ Error: {data['error']['message']}")
            return
        
        pages = data.get("data", [])
        if not pages:
            print("❌ No pages found. Please create a Facebook Page first.")
            return
        
        print(f"✅ Found {len(pages)} page(s):")
        for i, page in enumerate(pages, 1):
            print(f"   {i}. {page.get('name', 'Unknown')} (ID: {page['id']})")
        
        # Select first page
        selected = pages[0]
        page_name = selected.get('name', 'Unknown')
        page_id = selected.get('id', '')
        page_token = selected.get('access_token', '')
        
        print(f"\n✅ Selected: {page_name}")
        print(f"   Page ID: {page_id}")
        
        # Step 2: Get Instagram Account
        print(f"\n📷 Checking for Instagram Business Account...")
        url = f"{GRAPH_API}/{page_id}"
        params = {
            "fields": "instagram_business_account",
            "access_token": page_token
        }
        
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        ig_user_id = ""
        ig_username = ""
        
        if "instagram_business_account" in data:
            ig_account = data["instagram_business_account"]
            if ig_account:
                ig_user_id = ig_account.get("id", "")
                
                # Get username
                url = f"{GRAPH_API}/{ig_user_id}"
                params = {"fields": "username", "access_token": page_token}
                resp = requests.get(url, params=params, timeout=15)
                ig_data = resp.json()
                ig_username = ig_data.get("username", "unknown")
                
                print(f"✅ Instagram found: @{ig_username} (ID: {ig_user_id})")
        else:
            print("⚠️  No Instagram Business Account connected")
            print("   To connect: Facebook Page → Settings → Instagram → Connect Account")
        
        # Step 3: Update .env
        print(f"\n💾 Updating .env file...")
        env_file = Path(__file__).parent.parent / ".env"
        
        if env_file.exists():
            content = env_file.read_text(encoding="utf-8")
            
            # Replace tokens
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
                    f"INSTAGRAM_ACCESS_TOKEN={page_token}"
                )
            
            env_file.write_text(content, encoding="utf-8")
            print("✅ .env file updated!")
        else:
            print(f"❌ .env file not found at {env_file}")
            return
        
        # Step 4: Summary
        print("\n" + "="*70)
        print("  ✅ Configuration Complete!")
        print("="*70)
        print(f"\n📋 Your Configuration:")
        print(f"   Facebook Page: {page_name}")
        print(f"   Page ID: {page_id}")
        print(f"   Page Token: {page_token[:40]}...")
        if ig_user_id:
            print(f"   Instagram: @{ig_username}")
            print(f"   Instagram ID: {ig_user_id}")
        
        print("\n📋 .env file updated with:")
        print(f"   ✅ FACEBOOK_ACCESS_TOKEN")
        print(f"   ✅ FACEBOOK_PAGE_ID={page_id}")
        print(f"   ✅ INSTAGRAM_ACCESS_TOKEN")
        if ig_user_id:
            print(f"   ✅ INSTAGRAM_USER_ID={ig_user_id}")
        
        print("\n" + "="*70)
        print("  Next Steps - Test Your Setup")
        print("="*70)
        print("""
1. Test connection:
   python watchers/test_facebook.py

2. Run integration test:
   python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault

3. Start monitoring:
   python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch

4. Post to Facebook (dry run):
   claude /social_post_facebook --message "Hello from AI Employee!"
""")
        
        print("\n💡 Token Info:")
        print("   Your Page Access Token doesn't expire!")
        print("   (Generated from long-lived user token)")
        print("\n📖 Documentation: docs/FACEBOOK_TOKEN_SETUP.md")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
