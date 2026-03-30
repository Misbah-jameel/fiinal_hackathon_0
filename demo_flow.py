#!/usr/bin/env python3
"""
demo_flow.py - AI Employee Gold Tier End-to-End Demo
-----------------------------------------------------
Tests all Gold Tier features in a single demo flow:

1. Create test email action file
2. Run reasoning loop
3. Create approval request
4. Auto-approve and execute
5. Generate CEO briefing
6. Check error recovery
7. Generate audit report

Usage:
    python demo_flow.py --vault ./AI_Employee_Vault
    python demo_flow.py --vault ./AI_Employee_Vault --dry-run
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
SKILLS_DIR = Path(__file__).parent / "skills"


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_step(step: int, title: str):
    """Print step header."""
    print(f"\n[Step {step}] {title}\n")


def run_command(cmd: list, description: str) -> bool:
    """Run command and report result."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run with project root as working directory
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120,
            cwd=str(Path(__file__).parent)
        )
        if result.returncode == 0:
            print(f"✅ SUCCESS")
            if result.stdout:
                print(f"Output: {result.stdout[:500]}")
            return True
        else:
            print(f"❌ FAILED: {result.stderr[:200] if result.stderr else 'No error output'}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def create_test_email_action(vault: Path) -> Path:
    """Create a test email action file."""
    needs_action = vault / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"EMAIL_demo_test_{timestamp}.md"
    filepath = needs_action / filename
    
    content = f"""---
type: email
from: demo.client@example.com
subject: Demo: Request for Invoice
received: {datetime.now().isoformat()}
priority: P2
status: pending
---

## Email: Demo Test - Request for Invoice

**From:** demo.client@example.com
**Received:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Priority:** P2

### Content

Hi,

Could you please send me an invoice for the consulting services provided last week? 
The amount we discussed was $500.

Thanks,
Demo Client

### Suggested Actions
- [ ] Review email
- [ ] Create invoice in Odoo
- [ ] Send invoice via email
"""
    
    filepath.write_text(content, encoding="utf-8")
    return filepath


def create_test_social_action(vault: Path) -> Path:
    """Create a test social media action file."""
    needs_action = vault / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"TWITTER_demo_test_{timestamp}.md"
    filepath = needs_action / filename
    
    content = f"""---
type: twitter_mention
tweet_id: "12345678"
from: @demo_user
received: {datetime.now().isoformat()}
priority: P3
status: pending
---

# Twitter Mention — Action Required

**Type:** Mention
**From:** @demo_user
**Time:** {datetime.now().isoformat()}

## Content

> Great product! Would love to learn more about your AI Employee solution.

## Suggested Actions

1. Draft a friendly reply
2. Include link to website
3. Place in /Pending_Approval before sending
"""
    
    filepath.write_text(content, encoding="utf-8")
    return filepath


def demo_gold_tier(vault: Path, dry_run: bool = False):
    """Run full Gold Tier demo flow."""
    
    print_header("AI Employee Gold Tier — End-to-End Demo")
    print(f"Vault: {vault}")
    print(f"Dry Run: {dry_run}")
    
    steps_passed = 0
    steps_total = 7
    
    # ────────────────────────────────────────────────────────────────
    # Step 1: Create test action files
    # ────────────────────────────────────────────────────────────────
    print_step(1, "Creating test action files")
    
    email_file = create_test_email_action(vault)
    print(f"✅ Created: {email_file.name}")
    
    social_file = create_test_social_action(vault)
    print(f"✅ Created: {social_file.name}")
    
    steps_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    # Step 2: Run reasoning loop
    # ────────────────────────────────────────────────────────────────
    print_step(2, "Running Reasoning Loop")
    
    script = SKILLS_DIR / "reasoning_loop.py"
    if run_command(
        ["python", str(script), "--vault", str(vault)],
        "Processing action files and creating plans"
    ):
        steps_passed += 1
    
    # Show created plans
    plans_dir = vault / "Plans"
    if plans_dir.exists():
        plans = list(plans_dir.glob("*.md"))
        print(f"\n📋 Created {len(plans)} plan file(s):")
        for p in plans[-3:]:
            print(f"  - {p.name}")
    
    # ────────────────────────────────────────────────────────────────
    # Step 3: Check approval queue
    # ────────────────────────────────────────────────────────────────
    print_step(3, "Checking Approval Queue")
    
    pending_dir = vault / "Pending_Approval"
    if pending_dir.exists():
        pending = list(pending_dir.glob("*.md"))
        print(f"⏳ {len(pending)} item(s) pending approval:")
        for p in pending:
            print(f"  - {p.name}")
    else:
        print("No items pending approval")
    
    steps_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    # Step 4: Auto-approve (for demo) and execute
    # ────────────────────────────────────────────────────────────────
    print_step(4, "Auto-Approving and Executing (Demo Mode)")
    
    if pending_dir.exists():
        approved_dir = vault / "Approved"
        approved_dir.mkdir(parents=True, exist_ok=True)
        
        # Move pending to approved (simulating human approval)
        for p in pending_dir.glob("*.md"):
            shutil.move(str(p), str(approved_dir / p.name))
            print(f"✓ Approved: {p.name}")
    
    # Run HITL approval
    script = SKILLS_DIR / "hitl_approval.py"
    cmd = ["python", str(script), "--vault", str(vault)]
    if dry_run:
        cmd.append("--dry-run")
    
    if run_command(cmd, "Executing approved actions"):
        steps_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    # Step 5: Generate CEO Briefing
    # ────────────────────────────────────────────────────────────────
    print_step(5, "Generating CEO Briefing")
    
    script = SKILLS_DIR / "ceo_briefing.py"
    cmd = ["python", str(script), "--vault", str(vault), "--period", "7"]

    if run_command(cmd, "Creating Monday Morning CEO Briefing"):
        steps_passed += 1

        # Show briefing file
        briefings_dir = vault / "Briefings"
        if briefings_dir.exists():
            briefings = sorted(briefings_dir.glob("*.md"), reverse=True)
            if briefings:
                print(f"\n📄 Latest briefing: {briefings[0].name}")
                content = briefings[0].read_text(encoding="utf-8")
                print(f"\n📊 Preview (first 500 chars):\n{content[:500]}...")
    
    # ────────────────────────────────────────────────────────────────
    # Step 6: Error Recovery Check
    # ────────────────────────────────────────────────────────────────
    print_step(6, "Running Error Recovery Check")
    
    script = SKILLS_DIR / "error_recovery.py"
    if run_command(
        ["python", str(script), "--vault", str(vault), "--check"],
        "System health check"
    ):
        steps_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    # Step 7: Generate Audit Report
    # ────────────────────────────────────────────────────────────────
    print_step(7, "Generating Audit Report")
    
    script = SKILLS_DIR / "audit_logger.py"
    if run_command(
        ["python", str(script), "--vault", str(vault), "--status"],
        "Audit log status"
    ):
        steps_passed += 1
    
    # ────────────────────────────────────────────────────────────────
    # Summary
    # ────────────────────────────────────────────────────────────────
    print_header("Demo Summary")
    print(f"Steps Passed: {steps_passed}/{steps_total}")
    print(f"Success Rate: {steps_passed/steps_total*100:.1f}%")
    
    if steps_passed == steps_total:
        print("\n🎉 All Gold Tier features working correctly!")
    else:
        print(f"\n⚠️ {steps_total - steps_passed} step(s) had issues")
    
    # Show final queue status
    print("\n📊 Final Queue Status:")
    queues = {
        "Needs_Action": len(list((vault / "Needs_Action").glob("*.md"))) if (vault / "Needs_Action").exists() else 0,
        "In_Progress": len(list((vault / "In_Progress").glob("*.md"))) if (vault / "In_Progress").exists() else 0,
        "Pending_Approval": len(list((vault / "Pending_Approval").glob("*.md"))) if (vault / "Pending_Approval").exists() else 0,
        "Approved": len(list((vault / "Approved").glob("*.md"))) if (vault / "Approved").exists() else 0,
        "Done": len(list((vault / "Done").glob("*.md"))) if (vault / "Done").exists() else 0,
    }
    
    for queue, count in queues.items():
        print(f"  {queue}: {count}")
    
    print("\n✅ Demo complete!")
    print("\nNext steps:")
    print("  1. Review generated files in the vault")
    print("  2. Set DRY_RUN=false in .env for real actions")
    print("  3. Configure OAuth credentials for social media")
    print("  4. Start Odoo for accounting integration")


def main():
    parser = argparse.ArgumentParser(description="AI Employee — Gold Tier Demo Flow")
    parser.add_argument("--vault", default=str(VAULT), help="Path to vault")
    parser.add_argument("--dry-run", action="store_true", help="Log only, don't execute real actions")
    args = parser.parse_args()
    
    vault = Path(args.vault)
    
    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}")
        print("Creating vault structure...")
        vault.mkdir(parents=True, exist_ok=True)
    
    demo_gold_tier(vault, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
