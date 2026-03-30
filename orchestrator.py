#!/usr/bin/env python3
"""
orchestrator.py - AI Employee Gold Tier
----------------------------------------
Master Orchestrator for AI Employee

Coordinates:
- Watcher health monitoring
- Reasoning loop triggering
- HITL approval processing
- CEO briefing generation
- Error recovery checks

Usage:
    python orchestrator.py --vault ./AI_Employee_Vault
    python orchestrator.py --vault ./AI_Employee_Vault --once  # Single run
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
SKILLS_DIR = Path(__file__).parent / "skills"
WATCHERS_DIR = Path(__file__).parent / "watchers"

# Configuration
CHECK_INTERVAL = int(os.getenv("ORCHESTRATOR_INTERVAL", "60"))  # seconds
MAX_CONSECUTIVE_ERRORS = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "5"))


class Orchestrator:
    """Main orchestrator for AI Employee."""
    
    def __init__(self, vault: Path):
        self.vault = vault
        self.consecutive_errors = 0
        self.last_reasoning_run = None
        self.last_approval_run = None
        self.last_health_check = None
        
        # Ensure required directories exist
        (vault / "In_Progress").mkdir(parents=True, exist_ok=True)
        (vault / "Quarantine").mkdir(parents=True, exist_ok=True)
        (vault / "Audit" / "json").mkdir(parents=True, exist_ok=True)
    
    def run_reasoning_loop(self) -> bool:
        """Trigger reasoning loop."""
        try:
            script = SKILLS_DIR / "reasoning_loop.py"
            result = subprocess.run(
                ["python", str(script), "--vault", str(self.vault)],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                self.last_reasoning_run = datetime.now()
                self.consecutive_errors = 0
                return True
            else:
                self._log_error("reasoning_loop", result.stderr)
                return False
                
        except Exception as e:
            self._log_error("reasoning_loop", str(e))
            return False
    
    def run_hitl_approval(self) -> bool:
        """Trigger HITL approval processor."""
        try:
            script = SKILLS_DIR / "hitl_approval.py"
            result = subprocess.run(
                ["python", str(script), "--vault", str(self.vault)],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                self.last_approval_run = datetime.now()
                self.consecutive_errors = 0
                return True
            else:
                self._log_error("hitl_approval", result.stderr)
                return False
                
        except Exception as e:
            self._log_error("hitl_approval", str(e))
            return False
    
    def check_watcher_health(self) -> dict:
        """Check if all watchers are running."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "watchers": {},
            "overall": "healthy",
        }
        
        # Check PM2 processes
        try:
            result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                procs = json.loads(result.stdout)
                watcher_names = ["gmail-watcher", "file-watcher", "linkedin-watcher",
                               "twitter-watcher", "facebook-watcher", "instagram-watcher"]

                for name in watcher_names:
                    proc = next((p for p in procs if p["name"] == name), None)
                    if proc:
                        status = proc.get("pm2_env", {}).get("status", "unknown")
                        health["watchers"][name] = status
                        if status != "online":
                            health["overall"] = "degraded"
                    else:
                        health["watchers"][name] = "not_found"
                        health["overall"] = "degraded"
        except Exception as e:
            health["overall"] = "error"
            health["error"] = str(e)
        
        return health
    
    def check_vault_queues(self) -> dict:
        """Check queue depths."""
        queues = {
            "needs_action": len(list((self.vault / "Needs_Action").glob("*.md"))) if (self.vault / "Needs_Action").exists() else 0,
            "in_progress": len(list((self.vault / "In_Progress").glob("*.md"))) if (self.vault / "In_Progress").exists() else 0,
            "pending_approval": len(list((self.vault / "Pending_Approval").glob("*.md"))) if (self.vault / "Pending_Approval").exists() else 0,
            "approved": len(list((self.vault / "Approved").glob("*.md"))) if (self.vault / "Approved").exists() else 0,
        }
        
        # Alert if queues are growing too large
        alerts = []
        if queues["needs_action"] > 50:
            alerts.append(f"Large Needs_Action queue: {queues['needs_action']}")
        if queues["pending_approval"] > 20:
            alerts.append(f"Large Pending_Approval queue: {queues['pending_approval']}")
        
        return {"queues": queues, "alerts": alerts}
    
    def run_ceo_briefing_if_due(self) -> bool:
        """Run CEO briefing if it's Monday morning."""
        now = datetime.now()
        
        # Check if already run today
        briefings_dir = self.vault / "Briefings"
        if briefings_dir.exists():
            today = now.strftime("%Y-%m-%d")
            existing = list(briefings_dir.glob(f"{today}*.md"))
            if existing:
                return True  # Already run
        
        # Check if Monday (weekday() == 0)
        if now.weekday() != 0:
            return True  # Not Monday, skip
        
        # Check if between 7-9 AM
        if now.hour < 7 or now.hour > 9:
            return True  # Not in time window
        
        # Run briefing
        try:
            script = SKILLS_DIR / "ceo_briefing.py"
            result = subprocess.run(
                ["python", str(script), "--vault", str(self.vault)],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                self._log_info("ceo_briefing", "Generated successfully")
                return True
            else:
                self._log_error("ceo_briefing", result.stderr)
                return False
                
        except Exception as e:
            self._log_error("ceo_briefing", str(e))
            return False
    
    def run_error_recovery_check(self) -> bool:
        """Run error recovery health check."""
        try:
            script = SKILLS_DIR / "error_recovery.py"
            result = subprocess.run(
                ["python", str(script), "--vault", str(self.vault), "--check"],
                capture_output=True, text=True, timeout=60
            )
            
            # Parse output for health status
            if "overall: healthy" in result.stdout.lower() or "overall:healthy" in result.stdout.lower():
                return True
            else:
                self._log_info("error_recovery", f"System degraded: {result.stdout[:200]}")
                return False
                
        except Exception as e:
            self._log_error("error_recovery", str(e))
            return False
    
    def _log_info(self, component: str, message: str):
        """Log info message."""
        self._log("INFO", component, message)
    
    def _log_error(self, component: str, message: str):
        """Log error message."""
        self._log("ERROR", component, message)
        self.consecutive_errors += 1
    
    def _log(self, level: str, component: str, message: str):
        """Log message to orchestrator log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = self.vault / "Logs" / "orchestrator.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry = f"- [{timestamp}] [{level}] [{component}] {message}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        # Also print to console
        print(f"[{timestamp}] [{level}] [{component}] {message}")
    
    def run_cycle(self):
        """Run one orchestration cycle."""
        self._log_info("orchestrator", "Starting cycle...")
        
        # 1. Check watcher health
        health = self.check_watcher_health()
        if health["overall"] != "healthy":
            self._log_error("watchers", f"Health check failed: {health}")
        
        # 2. Check queue depths
        queues = self.check_vault_queues()
        for alert in queues.get("alerts", []):
            self._log_info("queues", f"Alert: {alert}")
        
        # 3. Run reasoning loop if Needs_Action has items
        needs_action_count = queues["queues"].get("needs_action", 0)
        if needs_action_count > 0:
            self._log_info("orchestrator", f"Running reasoning loop ({needs_action_count} items)")
            self.run_reasoning_loop()
        
        # 4. Run HITL approval if Approved has items
        approved_count = queues["queues"].get("approved", 0)
        if approved_count > 0:
            self._log_info("orchestrator", f"Running HITL approval ({approved_count} items)")
            self.run_hitl_approval()
        
        # 5. Check if CEO briefing is due
        self.run_ceo_briefing_if_due()
        
        # 6. Error recovery check (every 5 cycles)
        if not self.last_health_check or (datetime.now() - self.last_health_check).seconds > 300:
            self.run_error_recovery_check()
            self.last_health_check = datetime.now()
        
        # Check for consecutive errors
        if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            self._log_error("orchestrator", f"Max consecutive errors ({MAX_CONSECUTIVE_ERRORS}) reached. Pausing...")
            time.sleep(300)  # Pause for 5 minutes
            self.consecutive_errors = 0
        
        self._log_info("orchestrator", "Cycle complete")
    
    def run(self, once: bool = False):
        """Run orchestrator loop."""
        self._log_info("orchestrator", f"Starting (once={once}, interval={CHECK_INTERVAL}s)")
        
        while True:
            try:
                self.run_cycle()
                
                if once:
                    break
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                self._log_info("orchestrator", "Stopped by user")
                break
            except Exception as e:
                self._log_error("orchestrator", f"Cycle failed: {e}")
                if once:
                    raise


def main():
    global CHECK_INTERVAL
    
    parser = argparse.ArgumentParser(description="AI Employee — Orchestrator (Gold Tier)")
    parser.add_argument("--vault", default=str(VAULT), help="Path to vault")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL, help="Check interval in seconds")
    args = parser.parse_args()

    CHECK_INTERVAL = args.interval

    vault = Path(args.vault)

    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}")
        sys.exit(1)

    orchestrator = Orchestrator(vault)
    orchestrator.run(once=args.once)


if __name__ == "__main__":
    main()
