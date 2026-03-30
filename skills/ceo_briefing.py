#!/usr/bin/env python3
"""
ceo_briefing.py - AI Employee Gold Tier
----------------------------------------
Generates the "Monday Morning CEO Briefing" by combining:
- Odoo accounting data (revenue, invoices, payments)
- Task completion metrics from /Done folder
- Business goals from Business_Goals.md
- Subscription audit from bank transactions

Outputs a structured briefing file to /Briefings/

Usage:
    python skills/ceo_briefing.py --vault ./AI_Employee_Vault
    python skills/ceo_briefing.py --vault ./AI_Employee_Vault --preview
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Optional Odoo RPC
try:
    import urllib.request
    import urllib.error
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "ai_employee")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

_session_cookie = None


def odoo_rpc(endpoint: str, params: dict) -> dict:
    """Make JSON-RPC call to Odoo."""
    global _session_cookie
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
    if _session_cookie:
        req.add_header("Cookie", f"session_id={_session_cookie}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            # Capture session cookie
            set_cookie = resp.getheader("set-cookie")
            if set_cookie:
                import re
                match = re.search(r"session_id=([^;]+)", set_cookie)
                if match:
                    _session_cookie = match.group(1)

            data = json.loads(resp.read())
            if "error" in data:
                msg = data["error"].get("data", {}).get("message", str(data["error"]))
                raise RuntimeError(msg)
            return data.get("result", {})
    except Exception as e:
        raise ConnectionError(f"Odoo RPC error: {e}")


def odoo_authenticate() -> int:
    """Authenticate with Odoo and return UID."""
    result = odoo_rpc("/web/session/authenticate", {
        "db": ODOO_DB,
        "login": ODOO_USER,
        "password": ODOO_PASSWORD,
    })
    if not result or not result.get("uid"):
        raise RuntimeError("Odoo authentication failed")
    return result["uid"]


def odoo_get_revenue(date_from: str = None, date_to: str = None) -> dict:
    """Get revenue summary from Odoo accounting."""
    try:
        uid = odoo_authenticate()
    except Exception:
        return {"error": "Odoo not available"}

    # Get posted invoices
    domain = [["move_type", "=", "out_invoice"], ["state", "=", "posted"]]
    if date_from:
        domain.append(["invoice_date", ">=", date_from])
    if date_to:
        domain.append(["invoice_date", "<=", date_to])

    invoices = odoo_rpc("/web/dataset/call_kw", {
        "model": "account.move",
        "method": "search_read",
        "args": [domain],
        "kwargs": {"fields": ["name", "amount_total", "amount_residual", "partner_id", "invoice_date"], "limit": 100},
    })

    total_revenue = sum(inv.get("amount_total", 0) for inv in invoices)
    total_outstanding = sum(inv.get("amount_residual", 0) for inv in invoices)
    paid_count = sum(1 for inv in invoices if inv.get("amount_residual", 0) == 0)

    return {
        "total_revenue": total_revenue,
        "total_outstanding": total_outstanding,
        "invoice_count": len(invoices),
        "paid_count": paid_count,
        "invoices": invoices[:10],  # Top 10 for briefing
    }


def odoo_get_balance() -> dict:
    """Get accounting balance summary."""
    try:
        uid = odoo_authenticate()
    except Exception:
        return {"error": "Odoo not available"}

    # Receivables
    receivables = odoo_rpc("/web/dataset/call_kw", {
        "model": "account.move.line",
        "method": "search_read",
        "args": [[["account_id.account_type", "=", "asset_receivable"], ["reconciled", "=", False]]],
        "kwargs": {"fields": ["amount_residual"], "limit": 1000},
    })
    total_receivable = sum(line.get("amount_residual", 0) for line in receivables)

    # Payables
    payables = odoo_rpc("/web/dataset/call_kw", {
        "model": "account.move.line",
        "method": "search_read",
        "args": [[["account_id.account_type", "=", "liability_payable"], ["reconciled", "=", False]]],
        "kwargs": {"fields": ["amount_residual"], "limit": 1000},
    })
    total_payable = sum(abs(line.get("amount_residual", 0)) for line in payables)

    return {
        "receivables": total_receivable,
        "payables": total_payable,
        "net": total_receivable - total_payable,
    }


def get_task_metrics() -> dict:
    """Analyze completed tasks from /Done folder."""
    done_dir = VAULT / "Done"
    if not done_dir.exists():
        return {"total": 0, "this_week": 0, "items": []}

    # Get files from last 7 days
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    items = []
    for f in done_dir.glob("*.md"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime > week_ago:
                items.append({"name": f.name, "completed": mtime.isoformat()})
        except Exception:
            pass

    return {
        "total": len(list(done_dir.glob("*.md"))),
        "this_week": len(items),
        "recent": items[:5],
    }


def get_business_goals() -> dict:
    """Read business goals from Business_Goals.md."""
    goals_file = VAULT / "Business_Goals.md"
    if not goals_file.exists():
        return {"monthly_goal": 1000, "active_projects": []}

    content = goals_file.read_text(encoding="utf-8")

    # Simple parsing
    monthly_goal = 1000
    active_projects = []

    for line in content.split("\n"):
        if "Monthly goal:" in line:
            try:
                monthly_goal = int(line.split("$")[1].strip().replace(",", ""))
            except Exception:
                pass
        if line.strip().startswith("1.") or line.strip().startswith("2."):
            active_projects.append(line.strip())

    return {
        "monthly_goal": monthly_goal,
        "active_projects": active_projects,
    }


def analyze_subscriptions() -> list:
    """Flag potentially unused subscriptions."""
    # This would integrate with bank transactions
    # For now, return a placeholder
    return [
        {"name": "Review software subscriptions", "reason": "No usage data available", "cost": "TBD"},
    ]


def generate_briefing(period_days: int = 7, preview: bool = False) -> str:
    """Generate the full CEO Briefing document."""

    # Get data
    today = datetime.now()
    date_from = (today - timedelta(days=period_days)).strftime("%Y-%m-%d")
    date_to = today.strftime("%Y-%m-%d")

    revenue_data = odoo_get_revenue(date_from, date_to)
    balance_data = odoo_get_balance()
    task_metrics = get_task_metrics()
    goals = get_business_goals()
    subscriptions = analyze_subscriptions()

    # Calculate metrics
    revenue = revenue_data.get("total_revenue", 0) if isinstance(revenue_data, dict) else 0
    outstanding = revenue_data.get("total_outstanding", 0) if isinstance(revenue_data, dict) else 0
    invoice_count = revenue_data.get("invoice_count", 0) if isinstance(revenue_data, dict) else 0

    receivables = balance_data.get("receivables", 0) if isinstance(balance_data, dict) else 0
    payables = balance_data.get("payables", 0) if isinstance(balance_data, dict) else 0

    goal = goals.get("monthly_goal", 1000)
    progress_pct = (revenue / goal * 100) if goal > 0 else 0

    # Determine trend
    if progress_pct >= 80:
        trend = "🟢 On track"
    elif progress_pct >= 50:
        trend = "🟡 Moderate progress"
    else:
        trend = "🔴 Behind target"

    # Generate briefing
    briefing = f"""---
generated: {today.isoformat()}
period: {date_from} to {date_to}
type: ceo_briefing
---

# Monday Morning CEO Briefing

**Generated:** {today.strftime("%A, %B %d, %Y at %I:%M %p")}
**Period:** {date_from} to {date_to}

---

## Executive Summary

{trend}. Revenue is ${revenue:.2f} this period ({progress_pct:.1f}% of ${goal:.2f} monthly goal).

---

## Revenue Report

| Metric | Amount |
|--------|--------|
| **Revenue This Period** | ${revenue:.2f} |
| **Monthly Goal** | ${goal:.2f} |
| **Progress** | {progress_pct:.1f}% |
| **Outstanding Invoices** | ${outstanding:.2f} |
| **Invoices Sent** | {invoice_count} |

### Recent Invoices
"""

    if isinstance(revenue_data, dict) and revenue_data.get("invoices"):
        for inv in revenue_data["invoices"][:5]:
            partner = inv.get("partner_id", ["?", "Unknown"])[1] if isinstance(inv.get("partner_id"), list) else "Unknown"
            briefing += f"- **{inv.get('name', 'N/A')}** — {partner}: ${inv.get('amount_total', 0):.2f} ({inv.get('payment_state', 'draft')})\n"
    else:
        briefing += "- _No invoice data available (Odoo may not be running)_\n"

    briefing += f"""
---

## Accounting Balance

| Metric | Amount |
|--------|--------|
| **Receivables** (owed to us) | ${receivables:.2f} |
| **Payables** (we owe) | ${payables:.2f} |
| **Net Position** | ${receivables - payables:.2f} |

---

## Completed Tasks

**This Week:** {task_metrics['this_week']} tasks completed
**All Time:** {task_metrics['total']} tasks completed

### Recent Completions
"""

    if task_metrics.get("recent"):
        for item in task_metrics["recent"]:
            briefing += f"- [x] {item['name']}\n"
    else:
        briefing += "- _No tasks completed this week_\n"

    briefing += f"""
---

## Active Projects

"""
    if goals.get("active_projects"):
        for proj in goals["active_projects"]:
            briefing += f"- {proj}\n"
    else:
        briefing += "- _No active projects defined_\n"

    briefing += f"""
---

## Proactive Suggestions

### Cost Optimization
"""
    for sub in subscriptions:
        briefing += f"- ⚠️ **{sub['name']}**: {sub['reason']} (Cost: {sub['cost']})\n"

    briefing += f"""
### Upcoming Actions Needed
"""
    if outstanding > 0:
        briefing += f"- 💰 Follow up on ${outstanding:.2f} in outstanding invoices\n"
    if receivables > payables * 2:
        briefing += "- 💵 Consider transferring excess receivables to savings\n"

    briefing += f"""
---

## Bottlenecks Identified

"""
    # Simple bottleneck detection
    bottlenecks = []
    if task_metrics['this_week'] < 3:
        bottlenecks.append("- Low task completion rate this week")
    if progress_pct < 30:
        bottlenecks.append("- Revenue significantly behind monthly target")
    if outstanding > revenue * 0.5:
        bottlenecks.append("- High outstanding invoice ratio (>50% of revenue)")

    if bottlenecks:
        briefing += "\n".join(bottlenecks) + "\n"
    else:
        briefing += "- _No significant bottlenecks detected_\n"

    briefing += f"""
---

## Approval Queue Status

"""
    pending_dir = VAULT / "Pending_Approval"
    if pending_dir.exists():
        pending = list(pending_dir.glob("*.md"))
        if pending:
            briefing += f"**{len(pending)} item(s) awaiting approval:**\n"
            for p in pending[:5]:
                briefing += f"- {p.name}\n"
            if len(pending) > 5:
                briefing += f"- _...and {len(pending) - 5} more_\n"
        else:
            briefing += "- _No items pending approval_\n"
    else:
        briefing += "- _No approval queue found_\n"

    briefing += f"""
---

*Generated by AI Employee v0.2 (Gold Tier)*
*Next briefing: {today.strftime("%A")} in 7 days*
"""

    return briefing


def main():
    parser = argparse.ArgumentParser(description="AI Employee — CEO Briefing Generator (Gold Tier)")
    parser.add_argument("--vault", default=str(VAULT), help="Path to vault")
    parser.add_argument("--period", type=int, default=7, help="Period in days (default: 7)")
    parser.add_argument("--preview", action="store_true", help="Print to stdout instead of saving")
    args = parser.parse_args()

    vault = Path(args.vault)

    # Generate briefing
    print(f"Generating CEO Briefing (period: {args.period} days)...")

    try:
        briefing = generate_briefing(period_days=args.period, preview=args.preview)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.preview:
        print("\n" + "=" * 60)
        print(briefing)
        print("=" * 60)
    else:
        # Save to Briefings folder
        briefings_dir = vault / "Briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        weekday = today  # Could add weekday name
        filename = f"{today}_CEO_Briefing.md"
        filepath = briefings_dir / filename

        filepath.write_text(briefing, encoding="utf-8")
        print(f"\n[OK] CEO Briefing saved to: {filepath}")

        # Also update Dashboard.md
        dashboard_file = vault / "Dashboard.md"
        if dashboard_file.exists():
            content = dashboard_file.read_text(encoding="utf-8")
            # Add briefing link to recent activity section
            if f"[{today}]" not in content:
                content = content.replace(
                    "## Recent Activity",
                    f"## Recent Activity\n- [{today}] CEO Briefing generated -> [Briefings/{filename}](Briefings/{filename})",
                    1
                )
                dashboard_file.write_text(content, encoding="utf-8")
                print(f"[OK] Dashboard.md updated")

    print("\nDone!")


if __name__ == "__main__":
    main()
