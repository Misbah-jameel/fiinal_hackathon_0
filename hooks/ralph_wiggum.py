#!/usr/bin/env python3
"""
Ralph Wiggum Stop Hook — AI Employee Gold Tier
-----------------------------------------------
Reads the Claude Code stop hook event from stdin (JSON).
If there are unfinished items in Needs_Action or Pending_Approval,
exits with code 1 to signal Claude to keep going.
If everything is clear, exits with code 0 (allow stop).

Named after Ralph Wiggum: "I'm helping!" — keeps Claude iterating
until the task is truly complete.

Usage (auto-invoked by Claude Code on Stop event):
  python hooks/ralph_wiggum.py

Configuration via environment:
  VAULT_PATH: Path to Obsidian vault (default: ./AI_Employee_Vault)
  MAX_ITERATIONS: Max loop iterations before forcing stop (default: 10)
  ITERATION_FILE: File to track iteration count (default: .ralph_iteration)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

VAULT = Path(os.getenv("VAULT_PATH", "D:/fiinal_hackathon_0/AI_Employee_Vault"))
NEEDS_ACTION = VAULT / "Needs_Action"
PENDING_APPROVAL = VAULT / "Pending_Approval"
IN_PROGRESS = VAULT / "In_Progress"
LOG_DIR = VAULT / "Logs"
ITERATION_FILE = VAULT / ".ralph_iteration"
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))


def log(message: str, level: str = "INFO"):
    """Log message to daily log file."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = LOG_DIR / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{today}_ralph.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"- [{timestamp}] [{level}] [Ralph Wiggum Hook] {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass  # Never crash the hook


def get_iteration_count() -> int:
    """Get current iteration count."""
    if ITERATION_FILE.exists():
        try:
            return int(ITERATION_FILE.read_text().strip())
        except Exception:
            return 0
    return 0


def increment_iteration() -> int:
    """Increment and return iteration count."""
    count = get_iteration_count() + 1
    ITERATION_FILE.write_text(str(count))
    return count


def reset_iteration():
    """Reset iteration counter."""
    if ITERATION_FILE.exists():
        ITERATION_FILE.unlink()


def check_unfinished_work() -> tuple[bool, str, list]:
    """
    Returns (should_continue, reason, items).
    True = unfinished work exists → Claude should keep going.
    """
    reasons = []
    items = []

    # Check Needs_Action
    if NEEDS_ACTION.exists():
        na_items = list(NEEDS_ACTION.glob("*.md"))
        if na_items:
            reasons.append(f"{len(na_items)} item(s) in /Needs_Action")
            items.extend([("needs_action", f.name) for f in na_items[:5]])

    # Check In_Progress (claim-by-move rule)
    if IN_PROGRESS.exists():
        ip_items = list(IN_PROGRESS.glob("*.md"))
        if ip_items:
            reasons.append(f"{len(ip_items)} item(s) in /In_Progress")
            items.extend([("in_progress", f.name) for f in ip_items[:5]])

    # Check Pending_Approval for items not yet acted on
    if PENDING_APPROVAL.exists():
        pending = list(PENDING_APPROVAL.glob("*.md"))
        if pending:
            reasons.append(f"{len(pending)} item(s) in /Pending_Approval waiting for review")
            items.extend([("pending_approval", f.name) for f in pending[:5]])

    if reasons:
        return True, " | ".join(reasons), items
    return False, "All queues clear", []


def get_health_status() -> dict:
    """Get system health status for debugging."""
    return {
        "needs_action_count": len(list(NEEDS_ACTION.glob("*.md"))) if NEEDS_ACTION.exists() else 0,
        "in_progress_count": len(list(IN_PROGRESS.glob("*.md"))) if IN_PROGRESS.exists() else 0,
        "pending_approval_count": len(list(PENDING_APPROVAL.glob("*.md"))) if PENDING_APPROVAL.exists() else 0,
        "iteration_count": get_iteration_count(),
        "max_iterations": MAX_ITERATIONS,
    }


def main():
    # Read stop hook event from stdin
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        event = {}

    stop_reason = event.get("stop_reason", "unknown")
    log(f"Stop hook triggered: stop_reason={stop_reason}")

    # Only intervene on natural end_turn stops, not errors or tool_use
    if stop_reason not in ("end_turn", "max_tokens", ""):
        log(f"Allowing stop (stop_reason={stop_reason})")
        reset_iteration()
        sys.exit(0)

    # Check iteration limit
    iteration = get_iteration_count()
    if iteration >= MAX_ITERATIONS:
        log(f"MAX ITERATIONS REACHED ({MAX_ITERATIONS}) - forcing stop", "WARNING")
        print(f"\n[Ralph Wiggum] Max iterations ({MAX_ITERATIONS}) reached. Stopping.")
        print("Some items may remain unprocessed. Please review manually.")
        reset_iteration()
        sys.exit(0)

    should_continue, reason, items = check_unfinished_work()

    if should_continue:
        new_iteration = increment_iteration()
        log(f"CONTINUING (iteration {new_iteration}/{MAX_ITERATIONS}) — {reason}")

        # Print message for Claude to see and act on
        print(f"\n[Ralph Wiggum] 🔄 Unfinished work detected (iteration {new_iteration}/{MAX_ITERATIONS}):")
        print(f"    {reason}")
        print("\n📋 Items needing attention:")
        for item_type, item_name in items:
            print(f"    • [{item_type}] {item_name}")
        print("\n💡 Please process all items in /Needs_Action, /In_Progress, and /Pending_Approval before stopping.")
        sys.exit(1)  # Signal Claude Code to continue
    else:
        log(f"STOPPING — {reason}")
        reset_iteration()
        sys.exit(0)  # All clear, allow stop


if __name__ == "__main__":
    main()
