#!/usr/bin/env python3
"""
Odoo Setup Script -- AI Employee Gold Tier
==========================================
Initializes Odoo with demo data for the AI Employee:
- Creates the database if it doesn't exist
- Creates sample customers
- Creates sample invoices
- Verifies MCP connection

Usage:
    python odoo/setup_odoo.py              # Check connection + init DB if needed
    python odoo/setup_odoo.py --seed       # Add demo data
    python odoo/setup_odoo.py --status     # Check Odoo health
"""

import sys
import json
import argparse
import urllib.request
import urllib.error
from datetime import date

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "ai_employee")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
ODOO_MASTER_PWD = os.getenv("ODOO_MASTER_PASSWORD", "admin_master_pass")

# Global session cookie storage
_session_cookie = None
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())


def rpc(endpoint: str, params: dict) -> dict:
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "call",
        "id": 1,
        "params": params,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{ODOO_URL}{endpoint}",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with _opener.open(req, timeout=30) as resp:
            data = json.loads(resp.read())
            if "error" in data:
                msg = data["error"].get("data", {}).get("message", str(data["error"]))
                raise RuntimeError(msg)
            return data.get("result", {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise ConnectionError(f"HTTP {e.code} from Odoo: {body[:200]}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot connect to Odoo at {ODOO_URL}: {e}")


def list_databases() -> list:
    """List all Odoo databases."""
    result = rpc("/web/database/list", {})
    return result if isinstance(result, list) else []


def create_database() -> bool:
    """Create the Odoo database via manager API."""
    print(f"  Creating database '{ODOO_DB}'...")
    try:
        result = rpc("/web/database/create", {
            "master_pwd": ODOO_MASTER_PWD,
            "name": ODOO_DB,
            "lang": "en_US",
            "password": ODOO_PASSWORD,
            "login": ODOO_USER,
            "demo": True,  # Include demo data
            "phone": "",
            "country_code": "us",
        })
        print(f"  [OK] Database '{ODOO_DB}' created!")
        return True
    except Exception as e:
        print(f"  [FAIL] Database creation failed: {e}")
        return False


def authenticate() -> int:
    result = rpc("/web/session/authenticate", {
        "db": ODOO_DB,
        "login": ODOO_USER,
        "password": ODOO_PASSWORD,
    })
    if not result or not result.get("uid"):
        raise RuntimeError("Authentication failed -- check ODOO_USER and ODOO_PASSWORD")
    return result["uid"]


def search_read(uid: int, model: str, domain: list, fields: list, limit: int = 10) -> list:
    return rpc("/web/dataset/call_kw", {
        "model": model,
        "method": "search_read",
        "args": [domain],
        "kwargs": {"fields": fields, "limit": limit},
    })


def create_record(uid: int, model: str, vals: dict) -> int:
    result = rpc("/web/dataset/call_kw", {
        "model": model,
        "method": "create",
        "args": [[vals]],
        "kwargs": {},
    })
    # Odoo 17 returns a list [id]; extract the integer
    return result[0] if isinstance(result, list) else result


def check_status():
    print(f"\n{'='*50}")
    print(f"  Odoo Health Check")
    print(f"  URL: {ODOO_URL}")
    print(f"  DB:  {ODOO_DB}")
    print(f"{'='*50}\n")

    # 1. Check if Odoo is reachable
    try:
        dbs = list_databases()
        print(f"[OK] Odoo reachable. Databases: {dbs}")
    except ConnectionError as e:
        print(f"[FAIL] Connection failed: {e}")
        print("\n  Start Odoo with: docker compose up -d")
        return False

    # 2. Create DB if missing
    if ODOO_DB not in dbs:
        print(f"[!] Database '{ODOO_DB}' not found. Creating...")
        if not create_database():
            return False
        print("    Wait 30s for Odoo to initialize the DB...")
        import time; time.sleep(30)

    # 3. Authenticate
    try:
        uid = authenticate()
        print(f"[OK] Authentication: uid={uid}")
    except RuntimeError as e:
        print(f"[FAIL] Auth error: {e}")
        return False

    # 4. Check accounting module
    try:
        invoices = search_read(uid, "account.move", [["move_type", "=", "out_invoice"]], ["name"], 1)
        print(f"[OK] Accounting module: {len(invoices)} invoice(s)")
    except Exception as e:
        print(f"[WARN] Accounting module: {e}")

    # 5. Check customers
    try:
        customers = search_read(uid, "res.partner", [["customer_rank", ">", 0]], ["name"], 5)
        print(f"[OK] Customers: {len(customers)} found")
    except Exception as e:
        print(f"[WARN] Customers: {e}")

    print(f"\n[OK] Odoo is healthy!")
    print(f"     Open UI: {ODOO_URL}/web")
    print(f"     Run /ceo-briefing to get a financial summary")
    return True


def seed_demo_data():
    print("\n[SEED] Adding demo data to Odoo...\n")

    try:
        uid = authenticate()
    except Exception as e:
        print(f"[FAIL] {e}")
        print("Start Odoo first: docker compose up -d")
        print("Then run: python odoo/setup_odoo.py --status")
        return

    # -- Create customers --
    customers_data = [
        {"name": "Acme Corp", "email": "billing@acme.com", "phone": "+1-555-0100",
         "customer_rank": 1, "is_company": True},
        {"name": "TechStart LLC", "email": "accounts@techstart.io", "phone": "+1-555-0200",
         "customer_rank": 1, "is_company": True},
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1-555-0301",
         "customer_rank": 1},
    ]

    partner_ids = []
    for c in customers_data:
        existing = search_read(uid, "res.partner", [["name", "=", c["name"]]], ["id", "name"], 1)
        if existing:
            print(f"  [SKIP] Customer exists: {c['name']}")
            partner_ids.append(existing[0]["id"])
        else:
            pid = create_record(uid, "res.partner", c)
            print(f"  [OK] Created customer: {c['name']} (id={pid})")
            partner_ids.append(pid)

    # -- Create draft invoices --
    today = date.today().isoformat()
    invoices_data = [
        {
            "partner_id": partner_ids[0],
            "move_type": "out_invoice",
            "invoice_date": today,
            "invoice_line_ids": [[0, 0, {
                "name": "AI Employee Monthly Retainer",
                "quantity": 1,
                "price_unit": 500.00,
            }]],
        },
        {
            "partner_id": partner_ids[1],
            "move_type": "out_invoice",
            "invoice_date": today,
            "invoice_line_ids": [[0, 0, {
                "name": "Consulting Services -- March 2026",
                "quantity": 8,
                "price_unit": 125.00,
            }]],
        },
    ]

    for inv in invoices_data:
        inv_id = create_record(uid, "account.move", inv)
        print(f"  [OK] Created draft invoice (id={inv_id})")

    print(f"\n[OK] Demo data seeded!")
    print(f"     View invoices: {ODOO_URL}/odoo/accounting")
    print(f"     View customers: {ODOO_URL}/odoo/contacts")


def main():
    parser = argparse.ArgumentParser(description="Odoo Setup for AI Employee Gold Tier")
    parser.add_argument("--status", action="store_true", help="Check Odoo health")
    parser.add_argument("--seed", action="store_true", help="Add demo customers and invoices")
    args = parser.parse_args()

    if args.status or (not args.seed):
        ok = check_status()
        if not ok:
            sys.exit(1)

    if args.seed:
        seed_demo_data()


if __name__ == "__main__":
    main()
