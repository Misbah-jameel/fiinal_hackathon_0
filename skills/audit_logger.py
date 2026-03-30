#!/usr/bin/env python3
"""
audit_logger.py - AI Employee Gold Tier
----------------------------------------
Comprehensive Audit Logging System

Provides:
- Structured JSON audit logs
- Daily markdown summaries
- Search and filter capabilities
- Compliance reporting
- Action trail reconstruction

Usage:
    python skills/audit_logger.py --vault ./AI_Employee_Vault --status
    python skills/audit_logger.py --vault ./AI_Employee_Vault --report today
    python skills/audit_logger.py --vault ./AI_Employee_Vault --search "email"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
AUDIT_DIR = VAULT / "Audit"
JSON_LOGS_DIR = AUDIT_DIR / "json"
MD_LOGS_DIR = VAULT / "Logs"
RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "90"))


class AuditLogger:
    """Structured audit logger for AI Employee actions."""
    
    def __init__(self, vault: Path = VAULT):
        self.vault = vault
        self.json_logs_dir = JSON_LOGS_DIR
        self.md_logs_dir = MD_LOGS_DIR
        self.json_logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.json_log_file = self.json_logs_dir / f"{self.today}.jsonl"
        self.md_log_file = self.md_logs_dir / f"{self.today}.md"
    
    def log(
        self,
        action_type: str,
        actor: str,
        target: str,
        result: str,
        parameters: dict = None,
        approval_status: str = "auto",
        approved_by: str = None,
        error: str = None,
        metadata: dict = None,
    ):
        """
        Log an audit entry.
        
        Args:
            action_type: Type of action (email_send, payment, post, etc.)
            actor: Who performed the action (claude_code, gmail_watcher, etc.)
            target: What was acted upon (email address, invoice ID, etc.)
            result: Outcome (success, failed, dry_run, pending)
            parameters: Action parameters (redacted if sensitive)
            approval_status: auto, approved, rejected, pending
            approved_by: Human who approved (if applicable)
            error: Error message if failed
            metadata: Additional context
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "result": result,
            "parameters": self._sanitize_parameters(parameters),
            "approval_status": approval_status,
            "approved_by": approved_by,
            "error": error,
            "metadata": metadata or {},
        }
        
        # Append to JSON log (JSONL format for easy streaming)
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Append to markdown log (human-readable)
        self._write_md_entry(entry)
        
        return entry
    
    def _sanitize_parameters(self, params: dict) -> dict:
        """Remove/redact sensitive information from parameters."""
        if not params:
            return {}
        
        sensitive_keys = ["password", "token", "secret", "api_key", "credential", "auth"]
        sanitized = {}
        
        for key, value in params.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_parameters(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [self._sanitize_parameters(v) if isinstance(v, dict) else v for v in value]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _write_md_entry(self, entry: dict):
        """Write entry to markdown log."""
        icon = {
            "success": "✅",
            "failed": "❌",
            "dry_run": "🧪",
            "pending": "⏳",
            "auto": "🤖",
            "approved": "[OK]",
        }.get(entry["result"], "•")
        
        md_entry = (
            f"\n## {entry['timestamp'].replace('T', ' ').split('.')[0]} — {entry['action_type']}\n\n"
            f"- {icon} **Actor:** {entry['actor']}\n"
            f"- **Target:** {entry['target']}\n"
            f"- **Result:** {entry['result']}\n"
            f"- **Approval:** {entry['approval_status']}"
            f"{f' (by: {entry["approved_by"]})' if entry['approved_by'] else ''}\n"
        )
        
        if entry.get("error"):
            md_entry += f"- **Error:** {entry['error']}\n"
        
        if entry.get("parameters"):
            md_entry += f"- **Parameters:**\n"
            for key, value in entry["parameters"].items():
                if value != "***REDACTED***":
                    md_entry += f"  - `{key}`: {value}\n"
        
        with open(self.md_log_file, "a", encoding="utf-8") as f:
            f.write(md_entry)
    
    # ─── Convenience Methods ────────────────────────────────────────────────────
    
    def log_email(self, to: str, subject: str, result: str, actor: str = "claude_code", **kwargs):
        return self.log("email_send", actor, to, result, {"to": to, "subject": subject}, **kwargs)
    
    def log_payment(self, amount: float, recipient: str, result: str, actor: str = "claude_code", **kwargs):
        return self.log("payment", actor, recipient, result, {"amount": amount, "recipient": recipient}, **kwargs)
    
    def log_social_post(self, platform: str, content: str, result: str, actor: str = "claude_code", **kwargs):
        return self.log(f"social_post_{platform}", actor, platform, result, {"platform": platform, "content_length": len(content)}, **kwargs)
    
    def log_invoice(self, invoice_id: str, customer: str, amount: float, result: str, actor: str = "claude_code", **kwargs):
        return self.log("invoice_action", actor, invoice_id, result, {"invoice_id": invoice_id, "customer": customer, "amount": amount}, **kwargs)
    
    def log_watcher_trigger(self, watcher: str, item_type: str, item_id: str, result: str, **kwargs):
        return self.log("watcher_trigger", watcher, item_id, result, {"watcher": watcher, "item_type": item_type}, **kwargs)
    
    def log_approval(self, action_type: str, target: str, approved_by: str, result: str, **kwargs):
        return self.log("approval", "human", target, result, {"action_type": action_type}, approved_by=approved_by, **kwargs)
    
    def log_error(self, component: str, error: str, context: dict = None):
        return self.log("error", component, component, "failed", context or {}, error=error)
    
    # ─── Query Methods ──────────────────────────────────────────────────────────
    
    def search(self, query: str = None, action_type: str = None, actor: str = None, 
               date_from: str = None, date_to: str = None, limit: int = 100) -> list:
        """Search audit logs."""
        results = []
        
        # Determine date range
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        # Iterate through JSONL files
        current = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            log_file = self.json_logs_dir / f"{date_str}.jsonl"
            
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            
                            # Apply filters
                            if query and query.lower() not in json.dumps(entry).lower():
                                continue
                            if action_type and entry["action_type"] != action_type:
                                continue
                            if actor and entry["actor"] != actor:
                                continue
                            
                            results.append(entry)
                            
                            if len(results) >= limit:
                                return results
                        except json.JSONDecodeError:
                            continue
            
            current += timedelta(days=1)
        
        return results
    
    def get_daily_summary(self, date: str = None) -> dict:
        """Get summary for a specific day."""
        if not date:
            date = self.today
        
        log_file = self.json_logs_dir / f"{date}.jsonl"
        if not log_file.exists():
            return {"date": date, "total": 0, "message": "No logs for this date"}
        
        actions = {}
        actors = {}
        results = {}
        total = 0
        
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    total += 1
                    
                    # Count by action type
                    action = entry["action_type"]
                    actions[action] = actions.get(action, 0) + 1
                    
                    # Count by actor
                    actor = entry["actor"]
                    actors[actor] = actors.get(actor, 0) + 1
                    
                    # Count by result
                    result = entry["result"]
                    results[result] = results.get(result, 0) + 1
                except json.JSONDecodeError:
                    continue
        
        return {
            "date": date,
            "total_entries": total,
            "by_action": actions,
            "by_actor": actors,
            "by_result": results,
        }
    
    def get_compliance_report(self, date_from: str = None, date_to: str = None) -> dict:
        """Generate compliance report for audit period."""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        entries = self.search(date_from=date_from, date_to=date_to, limit=10000)
        
        # Analyze patterns
        total_actions = len(entries)
        approved_actions = sum(1 for e in entries if e.get("approval_status") == "approved")
        auto_actions = sum(1 for e in entries if e.get("approval_status") == "auto")
        failed_actions = sum(1 for e in entries if e.get("result") == "failed")
        pending_actions = sum(1 for e in entries if e.get("result") == "pending")
        
        # Find humans who approved
        approvers = set(e.get("approved_by") for e in entries if e.get("approved_by"))
        
        # Action breakdown
        action_breakdown = {}
        for e in entries:
            action = e["action_type"]
            action_breakdown[action] = action_breakdown.get(action, 0) + 1
        
        return {
            "period": {"from": date_from, "to": date_to},
            "total_actions": total_actions,
            "approved_actions": approved_actions,
            "auto_actions": auto_actions,
            "failed_actions": failed_actions,
            "pending_actions": pending_actions,
            "human_approvers": list(approvers),
            "action_breakdown": action_breakdown,
            "success_rate": f"{(total_actions - failed_actions) / total_actions * 100:.1f}%" if total_actions > 0 else "N/A",
        }
    
    def cleanup_old_logs(self, retention_days: int = RETENTION_DAYS):
        """Remove audit logs older than retention period."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        removed = 0
        
        for log_file in self.json_logs_dir.glob("*.jsonl"):
            try:
                # Extract date from filename
                date_str = log_file.stem  # e.g., "2026-01-15"
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff:
                    log_file.unlink()
                    removed += 1
            except Exception:
                continue
        
        # Also cleanup old MD logs
        for log_file in self.md_logs_dir.glob("*.md"):
            try:
                date_str = log_file.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff:
                    log_file.unlink()
                    removed += 1
            except Exception:
                continue
        
        return removed


# ─── Global Logger Instance ─────────────────────────────────────────────────────

_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_action(action_type: str, **kwargs):
    """Convenience function for logging actions."""
    return get_audit_logger().log(action_type, **kwargs)


# ─── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Employee — Audit Logger (Gold Tier)")
    parser.add_argument("--vault", default=str(VAULT), help="Path to vault")
    parser.add_argument("--status", action="store_true", help="Show audit log status")
    parser.add_argument("--report", choices=["today", "week", "month", "custom"], help="Generate report")
    parser.add_argument("--search", type=str, help="Search audit logs")
    parser.add_argument("--date-from", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--date-to", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old logs")
    parser.add_argument("--retention-days", type=int, default=RETENTION_DAYS, help="Retention period")
    args = parser.parse_args()
    
    vault = Path(args.vault)
    logger = AuditLogger(vault)
    
    if args.status:
        # Count log files
        json_count = len(list(JSON_LOGS_DIR.glob("*.jsonl"))) if JSON_LOGS_DIR.exists() else 0
        md_count = len(list(MD_LOGS_DIR.glob("*.md"))) if MD_LOGS_DIR.exists() else 0
        
        # Get today's summary
        today_summary = logger.get_daily_summary()
        
        print(f"\n=== Audit Log Status ===")
        print(f"Vault: {vault}")
        print(f"JSON log files: {json_count}")
        print(f"Markdown log files: {md_count}")
        print(f"\nToday's Summary ({today_summary.get('date', 'N/A')}):")
        print(f"  Total entries: {today_summary.get('total_entries', 0)}")
        
        if today_summary.get("by_action"):
            print(f"  By action:")
            for action, count in today_summary["by_action"].items():
                print(f"    - {action}: {count}")
        
        if today_summary.get("by_result"):
            print(f"  By result:")
            for result, count in today_summary["by_result"].items():
                print(f"    - {result}: {count}")
        print()
    
    elif args.report:
        if args.report == "today":
            date_from = date_to = datetime.now().strftime("%Y-%m-%d")
        elif args.report == "week":
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")
        elif args.report == "month":
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")
        else:
            date_from = args.date_from or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            date_to = args.date_to or datetime.now().strftime("%Y-%m-%d")
        
        report = logger.get_compliance_report(date_from, date_to)
        
        print(f"\n=== Compliance Report ===")
        print(f"Period: {report['period']['from']} to {report['period']['to']}")
        print(f"\nTotal Actions: {report['total_actions']}")
        print(f"Success Rate: {report['success_rate']}")
        print(f"\nBreakdown:")
        print(f"  Approved (human): {report['approved_actions']}")
        print(f"  Auto (no approval): {report['auto_actions']}")
        print(f"  Failed: {report['failed_actions']}")
        print(f"  Pending: {report['pending_actions']}")
        
        if report.get("human_approvers"):
            print(f"\nHuman Approvers: {', '.join(report['human_approvers'])}")
        
        print(f"\nAction Breakdown:")
        for action, count in report["action_breakdown"].items():
            print(f"  {action}: {count}")
        print()
    
    elif args.search:
        results = logger.search(
            query=args.search,
            date_from=args.date_from,
            date_to=args.date_to,
            limit=50
        )
        
        print(f"\n=== Search Results ({len(results)} found) ===\n")
        for entry in results:
            ts = entry["timestamp"].replace("T", " ").split(".")[0]
            print(f"[{ts}] {entry['action_type']} by {entry['actor']} -> {entry['result']}")
            print(f"  Target: {entry['target']}")
            if entry.get("error"):
                print(f"  Error: {entry['error']}")
            print()
    
    elif args.cleanup:
        removed = logger.cleanup_old_logs(args.retention_days)
        print(f"Cleaned up {removed} old log file(s)")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
