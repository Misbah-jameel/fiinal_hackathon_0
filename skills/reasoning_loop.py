#!/usr/bin/env python3
"""
reasoning_loop.py - AI Employee Gold Tier
------------------------------------------
Main reasoning loop that:
1. Scans /Needs_Action for new items
2. Reads Company_Handbook.md for rules
3. Creates Plan.md files for each item
4. Routes sensitive actions to /Pending_Approval
5. Updates Dashboard.md
6. Moves processed items to /Done

Usage:
    python skills/reasoning_loop.py --vault ./AI_Employee_Vault
    python skills/reasoning_loop.py --vault ./AI_Employee_Vault --preview
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))


def parse_frontmatter(content: str) -> dict:
    """Extract YAML-like frontmatter from markdown."""
    fm = {}
    lines = content.split("\n")
    in_fm = False
    for line in lines:
        if line.strip() == "---":
            if not in_fm:
                in_fm = True
                continue
            else:
                break
        if in_fm and ":" in line:
            key, value = line.split(":", 1)
            fm[key.strip()] = value.strip()
    return fm


def get_priority(item_type: str, content: str, frontmatter: dict) -> str:
    """Determine priority based on content."""
    # Check frontmatter first
    if "priority" in frontmatter:
        return frontmatter["priority"]

    # Check content for keywords
    text = content.lower()
    p1_keywords = ["urgent", "asap", "emergency", "critical", "immediately"]
    p2_keywords = ["invoice", "payment", "deadline", "due", "overdue", "contract"]
    p4_keywords = ["newsletter", "unsubscribe", "fyi", "update", "digest"]

    for kw in p1_keywords:
        if kw in text:
            return "P1"
    for kw in p2_keywords:
        if kw in text:
            return "P2"
    for kw in p4_keywords:
        if kw in text:
            return "P4"

    return "P3"


def needs_approval(item_type: str, frontmatter: dict, content: str) -> bool:
    """Determine if item requires human approval."""
    # Always approve: emails, payments, social posts
    if item_type in ("email", "payment", "social_post"):
        return True

    # Check for financial keywords
    if any(kw in content.lower() for kw in ["payment", "invoice", "bank", "transfer"]):
        return True

    # Check amount thresholds
    if "amount" in frontmatter:
        try:
            amount = float(frontmatter["amount"])
            if amount > 50:  # Company_Handbook §2
                return True
        except Exception:
            pass

    return False


def create_plan(item_file: Path, vault: Path) -> Path:
    """Create a Plan.md file for an item."""
    content = item_file.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)

    item_type = fm.get("type", "unknown")
    priority = get_priority(item_type, content, fm)
    requires_approval = needs_approval(item_type, fm, content)

    plans_dir = vault / "Plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    plan_name = item_file.name.replace(".md", "_PLAN.md")
    plan_path = plans_dir / plan_name

    # Generate suggested actions based on type
    suggested_actions = []
    if item_type == "email":
        suggested_actions = [
            "Review email content and sender",
            "Draft reply (requires approval per Company_Handbook §1)",
            "Update Dashboard.md after processing",
        ]
    elif item_type == "linkedin":
        suggested_actions = [
            "Review LinkedIn notification",
            "Draft engagement response (requires approval)",
            "Consider creating content from this interaction",
        ]
    elif item_type == "twitter":
        suggested_actions = [
            "Review tweet/mention",
            "Draft reply if needed (requires approval)",
            "Log interaction",
        ]
    elif item_type in ("facebook", "instagram"):
        suggested_actions = [
            f"Review {item_type} engagement",
            "Draft response if needed (requires approval)",
            "Update social media log",
        ]
    elif "invoice" in content.lower() or "payment" in content.lower():
        suggested_actions = [
            "Verify invoice/payment details",
            "Check against Company_Handbook §2 (flag >$50)",
            "Create approval request if needed",
            "Log transaction",
        ]
    else:
        suggested_actions = [
            "Review item content",
            "Determine required action",
            "Execute or route for approval",
        ]

    plan_content = f"""---
created: {datetime.now().isoformat()}
status: pending
priority: {priority}
source: {item_file.name}
requires_approval: {str(requires_approval).lower()}
---

# Plan: {item_file.stem}

**Type:** {item_type}
**Priority:** {priority}
**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Source Content
See: [{item_file.name}]({item_file.name})

## Required Actions
"""

    for i, action in enumerate(suggested_actions, 1):
        plan_content += f"{i}. [ ] {action}\n"

    if requires_approval:
        plan_content += f"""
## Approval Required
⚠️ This item requires human approval before proceeding.
Action will be routed to /Pending_Approval/
"""

    plan_content += f"""
## Execution Log
- [ ] Actions completed
- [ ] Dashboard.md updated
- [ ] Moved to /Done/

---
*Generated by AI Employee Reasoning Loop v0.2*
"""

    plan_path.write_text(plan_content, encoding="utf-8")
    return plan_path


def create_approval_request(item_file: Path, vault: Path) -> Path:
    """Create an approval request file."""
    content = item_file.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)

    pending_dir = vault / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    approval_name = f"APPROVAL_{item_file.name}"
    approval_path = pending_dir / approval_name

    approval_content = f"""---
created: {datetime.now().isoformat()}
status: pending_approval
source: {item_file.name}
type: {fm.get('type', 'unknown')}
---

# Approval Request

**Source:** [{item_file.name}]({item_file.name})
**Type:** {fm.get('type', 'unknown')}
**Priority:** {fm.get('priority', 'P3')}

## Original Content
```
{content[:1000]}{'...' if len(content) > 1000 else ''}
```

## Required Action
Please review and approve the suggested actions from the Plan file.

## Instructions
- Move this file to /Approved/ to proceed
- Move to /Rejected/ to cancel
- Add comments by editing this file

---
*Created by AI Employee Reasoning Loop*
"""

    approval_path.write_text(approval_content, encoding="utf-8")
    return approval_path


def update_dashboard(vault: Path, processed_count: int, approval_count: int):
    """Update Dashboard.md with latest activity."""
    dashboard_file = vault / "Dashboard.md"
    if not dashboard_file.exists():
        return

    content = dashboard_file.read_text(encoding="utf-8")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Count items in each folder
    needs_action = len(list((vault / "Needs_Action").glob("*.md"))) if (vault / "Needs_Action").exists() else 0
    pending = len(list((vault / "Pending_Approval").glob("*.md"))) if (vault / "Pending_Approval").exists() else 0
    done = len(list((vault / "Done").glob("*.md"))) if (vault / "Done").exists() else 0

    new_content = f"""# AI Employee Dashboard

**Last Updated:** {timestamp}

---

## Quick Status

| Queue | Count |
|-------|-------|
| 📥 Needs Action | {needs_action} |
| ⏳ Pending Approval | {pending} |
| ✅ Done | {done} |

---

## Recent Activity

- [{timestamp}] Processed {processed_count} item(s), {approval_count} sent for approval

"""

    # Append rest of original content after the Recent Activity section
    parts = content.split("## Recent Activity", 1)
    if len(parts) > 1:
        # Keep everything after the original Recent Activity header
        rest = parts[1]
        # Remove old activity entries (keep last 5)
        lines = rest.split("\n")
        recent_lines = [line for line in lines if line.strip().startswith("- [")][:5]
        if recent_lines:
            new_content += "\n".join(recent_lines) + "\n"

    dashboard_file.write_text(new_content, encoding="utf-8")


def run_reasoning_loop(vault: Path, preview: bool = False) -> tuple[int, int]:
    """Run the full reasoning loop."""
    needs_action_dir = vault / "Needs_Action"

    if not needs_action_dir.exists():
        print("No /Needs_Action directory found.")
        return 0, 0

    items = list(needs_action_dir.glob("*.md"))
    if not items:
        print("No items in /Needs_Action/")
        return 0, 0

    print(f"Processing {len(items)} item(s)...")

    processed = 0
    approvals = 0

    for item_file in items:
        print(f"\n  Processing: {item_file.name}")

        # Create plan
        plan_path = create_plan(item_file, vault)
        print(f"    -> Created plan: {plan_path.name}")

        # Check if approval needed
        content = item_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)

        if needs_approval(fm.get("type", "unknown"), fm, content):
            approval_path = create_approval_request(item_file, vault)
            print(f"    -> Created approval request: {approval_path.name}")
            approvals += 1
        else:
            # Can process directly (for non-sensitive items)
            print(f"    -> Can process directly (no approval needed)")

        processed += 1

    # Update dashboard
    if not preview:
        update_dashboard(vault, processed, approvals)

    return processed, approvals


def main():
    parser = argparse.ArgumentParser(description="AI Employee — Reasoning Loop (Gold Tier)")
    parser.add_argument("--vault", default=str(VAULT), help="Path to vault")
    parser.add_argument("--preview", action="store_true", help="Preview only, don't write files")
    args = parser.parse_args()

    vault = Path(args.vault)

    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}")
        sys.exit(1)

    print(f"=== AI Employee Reasoning Loop ===")
    print(f"Vault: {vault}")

    processed, approvals = run_reasoning_loop(vault, preview=args.preview)

    print(f"\n=== Summary ===")
    print(f"Processed: {processed} item(s)")
    print(f"Approvals created: {approvals}")

    if args.preview:
        print("\n[PREVIEW MODE - No files written]")


if __name__ == "__main__":
    main()
