#!/usr/bin/env python3
"""
error_recovery.py - AI Employee Gold Tier
------------------------------------------
Error Recovery and Graceful Degradation Module

Provides:
- Retry logic with exponential backoff
- Error quarantine for corrupted files
- Process health monitoring
- Auto-restart capabilities
- Human notification on critical failures

Usage:
    python skills/error_recovery.py --vault ./AI_Employee_Vault --check
    python skills/error_recovery.py --vault ./AI_Employee_Vault --retry-failed
"""

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
QUARANTINE_DIR = VAULT / "Quarantine"
ERROR_LOG = VAULT / "Logs" / "errors.json"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "60.0"))


class TransientError(Exception):
    """Temporary error that can be retried (network timeout, rate limit)."""
    pass


class PermanentError(Exception):
    """Permanent error that should not be retried (auth failure, invalid data)."""
    pass


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open - too many failures."""
    pass


# ─── Retry Decorator ────────────────────────────────────────────────────────────

def with_retry(max_attempts: int = MAX_RETRIES, base_delay: float = BASE_DELAY, max_delay: float = MAX_DELAY):
    """
    Decorator for retry logic with exponential backoff.
    
    Usage:
        @with_retry(max_attempts=3, base_delay=1.0)
        def send_email(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    last_error = e
                    if attempt == max_attempts - 1:
                        log_error(func.__name__, str(e), "max_retries_exceeded", args, kwargs)
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    log_error(func.__name__, str(e), f"retrying_in_{delay}s", args, kwargs)
                    time.sleep(delay)
                except PermanentError:
                    # Don't retry permanent errors
                    raise
                except Exception as e:
                    # Unknown errors - treat as transient
                    last_error = e
                    if attempt == max_attempts - 1:
                        log_error(func.__name__, str(e), "unknown_error_max_retries", args, kwargs)
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    log_error(func.__name__, str(e), f"unknown_retrying_in_{delay}s", args, kwargs)
                    time.sleep(delay)
            
            raise last_error
        return wrapper
    return decorator


# ─── Error Logging ──────────────────────────────────────────────────────────────

def log_error(function: str, error: str, context: str, args: tuple = None, kwargs: dict = None):
    """Log error to JSON error log."""
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "function": function,
        "error": str(error),
        "context": context,
        "args_summary": str(args)[:200] if args else None,
        "kwargs_summary": str(kwargs)[:200] if kwargs else None,
    }
    
    # Append to error log
    errors = []
    if ERROR_LOG.exists():
        try:
            errors = json.loads(ERROR_LOG.read_text())
        except Exception:
            errors = []
    
    errors.append(error_entry)
    
    # Keep last 1000 errors
    errors = errors[-1000:]
    
    ERROR_LOG.write_text(json.dumps(errors, indent=2))
    
    # Also log to daily markdown log
    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = VAULT / "Logs" / f"{today}.md"
    with open(daily_log, "a", encoding="utf-8") as f:
        f.write(f"\n- [{datetime.now().strftime('%H:%M:%S')}] [ERROR] [{function}] {error}\n")


def log_warning(function: str, message: str):
    """Log warning to daily log."""
    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = VAULT / "Logs" / f"{today}.md"
    daily_log.parent.mkdir(parents=True, exist_ok=True)
    
    with open(daily_log, "a", encoding="utf-8") as f:
        f.write(f"\n- [{datetime.now().strftime('%H:%M:%S')}] [WARNING] [{function}] {message}\n")


# ─── Quarantine Management ──────────────────────────────────────────────────────

def quarantine_file(file_path: Path, reason: str) -> Path:
    """Move corrupted/problematic file to quarantine."""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine_name = f"{timestamp}_{file_path.name}"
    quarantine_path = QUARANTINE_DIR / quarantine_name
    
    # Create metadata file
    meta_path = quarantine_path.with_suffix(".meta.json")
    meta = {
        "original_path": str(file_path),
        "quarantine_reason": reason,
        "quarantine_time": datetime.now().isoformat(),
        "original_content": file_path.read_text(encoding="utf-8") if file_path.exists() else None,
    }
    
    if file_path.exists():
        shutil.move(str(file_path), str(quarantine_path))
    
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    
    log_warning("quarantine_file", f"Quarantined {file_path.name}: {reason}")
    
    return quarantine_path


def restore_from_quarantine(quarantine_path: Path) -> Path:
    """Restore file from quarantine to original location."""
    if not quarantine_path.exists():
        raise FileNotFoundError(f"Quarantine file not found: {quarantine_path}")
    
    meta_path = quarantine_path.with_suffix(".meta.json")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata not found for: {quarantine_path}")
    
    meta = json.loads(meta_path.read_text())
    original_path = Path(meta["original_path"])
    
    # Restore file
    original_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(quarantine_path), str(original_path))
    
    # Remove metadata
    meta_path.unlink()
    
    log_warning("restore_from_quarantine", f"Restored {quarantine_path.name}")
    
    return original_path


def list_quarantine() -> list:
    """List all quarantined files."""
    if not QUARANTINE_DIR.exists():
        return []
    
    quarantine_files = []
    for f in QUARANTINE_DIR.glob("*.md"):
        meta_path = f.with_suffix(".meta.json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            quarantine_files.append({
                "file": f.name,
                "original": meta.get("original_path", "unknown"),
                "reason": meta.get("quarantine_reason", "unknown"),
                "time": meta.get("quarantine_time", "unknown"),
            })
    
    return quarantine_files


# ─── Graceful Degradation ───────────────────────────────────────────────────────

class GracefulDegradation:
    """
    Manages graceful degradation when components fail.
    
    Usage:
        degradation = GracefulDegradation()
        
        if degradation.is_degraded("gmail_api"):
            # Queue emails locally instead
            queue_email_locally(...)
        else:
            # Send via API
            send_via_gmail(...)
    """
    
    def __init__(self, vault: Path = VAULT):
        self.vault = vault
        self.status_file = vault / ".degradation_status.json"
        self.status = self._load_status()
    
    def _load_status(self) -> dict:
        if self.status_file.exists():
            try:
                return json.loads(self.status_file.read_text())
            except Exception:
                pass
        return {}
    
    def _save_status(self):
        self.status_file.write_text(json.dumps(self.status, indent=2))
    
    def mark_degraded(self, component: str, reason: str, auto_recovery_time: int = 3600):
        """Mark a component as degraded."""
        self.status[component] = {
            "status": "degraded",
            "reason": reason,
            "since": datetime.now().isoformat(),
            "auto_recovery_at": (datetime.now() + timedelta(seconds=auto_recovery_time)).isoformat(),
        }
        self._save_status()
        log_warning("graceful_degradation", f"{component} marked degraded: {reason}")
    
    def mark_healthy(self, component: str):
        """Mark a component as healthy."""
        if component in self.status:
            del self.status[component]
            self._save_status()
    
    def is_degraded(self, component: str) -> bool:
        """Check if component is degraded."""
        if component not in self.status:
            return False
        
        status = self.status[component]
        
        # Check auto-recovery
        if status.get("status") == "degraded":
            recovery_time = status.get("auto_recovery_at")
            if recovery_time and datetime.now().isoformat() > recovery_time:
                self.mark_healthy(component)
                return False
        
        return status.get("status") == "degraded"
    
    def get_status(self) -> dict:
        """Get full degradation status."""
        return {
            "is_degraded": len(self.status) > 0,
            "degraded_components": list(self.status.keys()),
            "details": self.status,
        }


# ─── Circuit Breaker ────────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Circuit breaker pattern for failing services.
    
    Usage:
        breaker = CircuitBreaker("gmail_api", failure_threshold=5, recovery_timeout=300)
        
        with breaker:
            send_email(...)
    """
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.status_file = VAULT / f".circuit_{name}.json"
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        if self.status_file.exists():
            try:
                return json.loads(self.status_file.read_text())
            except Exception:
                pass
        return {"failures": 0, "state": "closed", "last_failure": None}
    
    def _save_state(self):
        self.status_file.write_text(json.dumps(self.state, indent=2))
    
    def __enter__(self):
        if self.state["state"] == "open":
            # Check if recovery timeout has passed
            if self.state.get("opened_at"):
                opened_at = datetime.fromisoformat(self.state["opened_at"])
                if datetime.now() - opened_at > timedelta(seconds=self.recovery_timeout):
                    self.state["state"] = "half-open"
                    self._save_state()
                    log_warning("circuit_breaker", f"{self.name} entering half-open state")
                else:
                    raise CircuitBreakerOpen(f"Circuit breaker {self.name} is open")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Success
            if self.state["state"] == "half-open":
                self.state["state"] = "closed"
                self.state["failures"] = 0
                self._save_state()
                log_warning("circuit_breaker", f"{self.name} circuit closed (recovered)")
        else:
            # Failure
            self.state["failures"] = self.state.get("failures", 0) + 1
            self.state["last_failure"] = datetime.now().isoformat()
            
            if self.state["failures"] >= self.failure_threshold:
                self.state["state"] = "open"
                self.state["opened_at"] = datetime.now().isoformat()
                log_warning("circuit_breaker", f"{self.name} circuit OPEN (failures={self.state['failures']})")
            
            self._save_state()
        
        return False  # Don't suppress exception


# ─── Health Check ───────────────────────────────────────────────────────────────

def check_system_health(vault: Path = VAULT) -> dict:
    """Check overall system health."""
    health = {
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "overall": "healthy",
    }
    
    # Check directories
    required_dirs = ["Needs_Action", "Pending_Approval", "Approved", "Done", "Plans", "Logs"]
    for dir_name in required_dirs:
        dir_path = vault / dir_name
        health["components"][dir_name] = {
            "status": "healthy" if dir_path.exists() else "missing",
            "type": "directory",
        }
    
    # Check for error patterns
    if ERROR_LOG.exists():
        try:
            errors = json.loads(ERROR_LOG.read_text())
            recent_errors = [e for e in errors if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(hours=1)]
            if len(recent_errors) > 10:
                health["components"]["error_rate"] = {
                    "status": "warning",
                    "message": f"{len(recent_errors)} errors in last hour",
                }
                health["overall"] = "degraded"
        except Exception:
            pass
    
    # Check quarantine
    quarantine_count = len(list((vault / "Quarantine").glob("*.md"))) if (vault / "Quarantine").exists() else 0
    if quarantine_count > 0:
        health["components"]["quarantine"] = {
            "status": "warning",
            "message": f"{quarantine_count} file(s) in quarantine",
        }
    
    # Check degradation status
    degradation = GracefulDegradation(vault)
    deg_status = degradation.get_status()
    if deg_status["is_degraded"]:
        health["components"]["degradation"] = deg_status
        health["overall"] = "degraded"
    
    return health


# ─── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Employee — Error Recovery (Gold Tier)")
    parser.add_argument("--vault", default=str(VAULT), help="Path to vault")
    parser.add_argument("--check", action="store_true", help="Check system health")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed operations")
    parser.add_argument("--quarantine-list", action="store_true", help="List quarantined files")
    parser.add_argument("--quarantine-restore", type=str, help="Restore file from quarantine")
    args = parser.parse_args()
    
    vault = Path(args.vault)
    
    if args.check:
        health = check_system_health(vault)
        print(f"\n=== System Health Check ===")
        print(f"Timestamp: {health['timestamp']}")
        print(f"Overall Status: {health['overall'].upper()}")
        print("\nComponents:")
        for name, status in health["components"].items():
            icon = "[OK]" if status["status"] == "healthy" else "[!]"
            print(f"  {icon} {name}: {status['status']}")
            if "message" in status:
                print(f"       -> {status['message']}")
        print()
    
    elif args.retry_failed:
        print("Retry functionality requires integration with specific operations.")
        print("This is a framework - implement retry logic in your watchers.")
    
    elif args.quarantine_list:
        files = list_quarantine()
        if not files:
            print("No files in quarantine.")
        else:
            print(f"\n=== Quarantined Files ({len(files)}) ===\n")
            for f in files:
                print(f"File: {f['file']}")
                print(f"  Original: {f['original']}")
                print(f"  Reason: {f['reason']}")
                print(f"  Time: {f['time']}")
                print()
    
    elif args.quarantine_restore:
        quarantine_path = VAULT / "Quarantine" / args.quarantine_restore
        try:
            restored = restore_from_quarantine(quarantine_path)
            print(f"Restored: {restored}")
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
