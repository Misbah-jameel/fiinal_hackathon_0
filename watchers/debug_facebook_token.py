#!/usr/bin/env python3
"""Debug what your token has access to"""

import requests

USER_TOKEN = "EAATqq4wRMOgBQZCGj4Fl6Cq5TcX3VeOd6zRCvrlG8GJsln177UCu7YPk0oigIRZBBuZC8Mn8HwBc3zUaGjdQP2Ab44NBZAgWZC56kebPYZCcoeIR1HZBvCBkYfpbhrHILfyzHoYtpeyZAZAveBL41NCcF1BwPnVeXfPwPlDiP3OnHsznWZBxxLvKeTKJvZCaTwf9iX0QGJV8qU4LQfZAOx6zzfLf7zo3DkrAwHV0Aux5zBBkp2iXLDej0ZB2Ql6ze6l9II8Qv0dU2ip30ubrNOSbn"

GRAPH_API = "https://graph.facebook.com/v19.0"

print("="*70)
print("  Debugging Your Facebook Token")
print("="*70)

# Check token validity
print("\n1. Checking token validity...")
url = f"{GRAPH_API}/me"
params = {"access_token": USER_TOKEN}
resp = requests.get(url, params=params, timeout=15)
data = resp.json()

if "error" in data:
    print(f"   ❌ Token is invalid or expired")
    print(f"   Error: {data['error']['message']}")
else:
    print(f"   ✅ Token is valid!")
    print(f"   User ID: {data.get('id', 'unknown')}")
    print(f"   Name: {data.get('name', 'unknown')}")

# Check permissions
print("\n2. Checking permissions...")
url = f"{GRAPH_API}/me/permissions"
params = {"access_token": USER_TOKEN}
resp = requests.get(url, params=params, timeout=15)
data = resp.json()

if "data" in data:
    permissions = data["data"]
    granted = [p for p in permissions if p.get("status") == "granted"]
    declined = [p for p in permissions if p.get("status") == "declined"]
    
    print(f"   ✅ Granted: {len(granted)}")
    for p in granted[:10]:
        print(f"      - {p['permission']}")
    
    if declined:
        print(f"   ❌ Declined: {len(declined)}")
        for p in declined:
            print(f"      - {p['permission']}")

# Check pages
print("\n3. Checking Pages...")
url = f"{GRAPH_API}/me/accounts"
params = {"access_token": USER_TOKEN}
resp = requests.get(url, params=params, timeout=15)
data = resp.json()

if "data" in data:
    pages = data["data"]
    if pages:
        print(f"   ✅ Found {len(pages)} page(s):")
        for page in pages:
            print(f"      - {page.get('name', 'Unknown')} (ID: {page['id']})")
    else:
        print(f"   ❌ No pages found")
        print(f"\n   💡 You need to:")
        print(f"      1. Create a Facebook Page: https://www.facebook.com/pages/create")
        print(f"      2. OR get Admin access to an existing page")
        print(f"      3. Then re-run the token generator")

# Check Instagram
print("\n4. Checking Instagram...")
print("   (Requires a Facebook Page first)")

print("\n" + "="*70)
print("  Summary")
print("="*70)

if not pages:
    print("\n⚠️  ISSUE: No Facebook Pages found")
    print("\nSOLUTION:")
    print("   1. Go to: https://www.facebook.com/pages/create")
    print("   2. Create a new Facebook Page (it's free)")
    print("   3. Name it anything (e.g., 'My Business', 'AI Employee Test')")
    print("   4. After creating, run this script again:")
    print("      python watchers/complete_facebook_setup.py")
else:
    print("\n✅ Setup looks good!")

print("\n" + "="*70 + "\n")
