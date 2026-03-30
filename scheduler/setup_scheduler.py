"""
setup_scheduler.py - One-command Silver Tier scheduler setup for Windows.

Sets up:
  - PM2 daemon processes for all watcher scripts
  - Windows Task Scheduler jobs for reasoning loop, HITL, LinkedIn, CEO briefing

Usage:
    python scheduler/setup_scheduler.py          # Full setup
    python scheduler/setup_scheduler.py --status # Check status only
    python scheduler/setup_scheduler.py --remove # Remove all jobs
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Scheduler] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Scheduler")

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PS1_SCRIPT = PROJECT_ROOT / "scheduler" / "run_claude.ps1"

PM2_WATCHERS = [
    {
        "name": "gmail-watcher",
        "script": str(PROJECT_ROOT / "watchers" / "gmail_watcher.py"),
        "args": f"--vault {VAULT_PATH}",
    },
    {
        "name": "file-watcher",
        "script": str(PROJECT_ROOT / "watchers" / "filesystem_watcher.py"),
        "args": f"--vault {VAULT_PATH}",
    },
    {
        "name": "linkedin-watcher",
        "script": str(PROJECT_ROOT / "watchers" / "linkedin_watcher.py"),
        "args": f"--vault {VAULT_PATH} --watch",
    },
    # Gold Tier watchers
    {
        "name": "twitter-watcher",
        "script": str(PROJECT_ROOT / "watchers" / "twitter_watcher.py"),
        "args": f"--vault {VAULT_PATH} --watch",
    },
    {
        "name": "facebook-watcher",
        "script": str(PROJECT_ROOT / "watchers" / "facebook_watcher.py"),
        "args": f"--vault {VAULT_PATH} --watch",
    },
]

SCHEDULED_TASKS = [
    {
        "name": "AIEmployee_ReasoningLoop",
        "skill": "reasoning-loop",
        "description": "AI Employee reasoning loop every 30 minutes",
        "trigger": "every_30_min",
    },
    {
        "name": "AIEmployee_HITLApproval",
        "skill": "hitl-approval",
        "description": "AI Employee HITL approval check every 5 minutes",
        "trigger": "every_5_min",
    },
    {
        "name": "AIEmployee_LinkedInPoster",
        "skill": "linkedin-poster",
        "description": "AI Employee LinkedIn post draft — Tue & Thu 7AM",
        "trigger": "tue_thu_7am",
    },
    {
        "name": "AIEmployee_TwitterPoster",
        "skill": "twitter-poster",
        "description": "AI Employee Twitter post draft — Tue & Thu 8AM",
        "trigger": "tue_thu_7am",
    },
    {
        "name": "AIEmployee_WeeklyCEOBriefing",
        "skill": "ceo-briefing",
        "description": "AI Employee weekly CEO briefing every Monday 7AM",
        "trigger": "monday_7am",
    },
]


def run(cmd: list, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def pm2_available() -> bool:
    return shutil.which("pm2") is not None


def setup_pm2():
    if not pm2_available():
        logger.warning("PM2 not found. Install with: npm install -g pm2")
        return False

    for watcher in PM2_WATCHERS:
        try:
            cmd = [
                "pm2", "start", watcher["script"],
                "--name", watcher["name"],
                "--interpreter", "python3",
                "--",
            ] + watcher["args"].split()
            result = run(cmd, check=False)
            if result.returncode == 0:
                logger.info(f"PM2: started {watcher['name']}")
            else:
                # May already be running
                logger.info(f"PM2: {watcher['name']} already running or error — {result.stderr.strip()[:80]}")
        except Exception as e:
            logger.error(f"PM2 error for {watcher['name']}: {e}")

    try:
        run(["pm2", "save"])
        logger.info("PM2: process list saved (will survive reboot)")
    except Exception:
        logger.warning("PM2 save failed — run 'pm2 save' manually")

    return True


def write_ps1_script():
    """Write the PowerShell wrapper that Task Scheduler calls."""
    PS1_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# run_claude.ps1 - AI Employee Task Scheduler wrapper
param([string]$Skill, [string]$Vault = "{VAULT_PATH}")

Set-Location "{PROJECT_ROOT}"
$env:VAULT_PATH = $Vault

try {{
    $output = claude --print "/$Skill" 2>&1
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logFile = Join-Path $Vault "Logs\\scheduler.log"
    Add-Content -Path $logFile -Value "[$timestamp] $Skill completed"
    if ($output) {{
        Add-Content -Path $logFile -Value $output
    }}
}} catch {{
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Error "[$timestamp] $Skill failed: $_"
}}
"""
    PS1_SCRIPT.write_text(content, encoding="utf-8")
    logger.info(f"Written: {PS1_SCRIPT}")


def register_task(task: dict):
    """Register a single Task Scheduler job via PowerShell."""
    trigger_map = {
        "every_30_min": (
            "$trigger = New-ScheduledTaskTrigger "
            "-RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)"
        ),
        "every_5_min": (
            "$trigger = New-ScheduledTaskTrigger "
            "-RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)"
        ),
        "tue_thu_7am": (
            "$triggerTue = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At '7:00AM'; "
            "$triggerThu = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At '7:00AM'; "
            "$trigger = @($triggerTue, $triggerThu)"
        ),
        "monday_7am": (
            "$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '7:00AM'"
        ),
    }

    trigger_ps = trigger_map.get(task["trigger"], trigger_map["every_30_min"])
    ps_script = f"""
{trigger_ps}
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -File \\"{PS1_SCRIPT}\\" -Skill {task['skill']}"
Register-ScheduledTask `
    -TaskName "{task['name']}" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest `
    -Description "{task['description']}" `
    -Force
"""
    result = subprocess.run(
        ["powershell", "-NonInteractive", "-Command", ps_script],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        logger.info(f"Task Scheduler: registered {task['name']}")
    else:
        logger.warning(f"Task Scheduler: {task['name']} failed — {result.stderr.strip()[:120]}")
        logger.info("  (Run as Administrator to register tasks)")


def setup_scheduler():
    write_ps1_script()
    for task in SCHEDULED_TASKS:
        register_task(task)


def print_status():
    print("\n=== AI Employee Status ===\n")

    # PM2
    if pm2_available():
        result = run(["pm2", "jlist"], check=False)
        if result.returncode == 0:
            try:
                procs = json.loads(result.stdout)
                watcher_names = {w["name"] for w in PM2_WATCHERS}
                print("PM2 Daemons:")
                for p in procs:
                    if p["name"] in watcher_names:
                        status = p.get("pm2_env", {}).get("status", "unknown")
                        icon = "✓" if status == "online" else "✗"
                        print(f"  {icon} {p['name']} ({status})")
            except Exception:
                print("  (Could not parse PM2 output)")
    else:
        print("PM2: not installed")

    # Task Scheduler
    print("\nTask Scheduler Jobs:")
    for task in SCHEDULED_TASKS:
        result = subprocess.run(
            ["powershell", "-Command",
             f"(Get-ScheduledTask -TaskName '{task['name']}' -ErrorAction SilentlyContinue).State"],
            capture_output=True, text=True
        )
        state = result.stdout.strip() or "not registered"
        icon = "✓" if state == "Ready" else "✗"
        print(f"  {icon} {task['name']} ({state})")
    print()


def remove_all():
    logger.info("Removing all AI Employee scheduled tasks...")
    for task in SCHEDULED_TASKS:
        subprocess.run(
            ["powershell", "-Command",
             f"Unregister-ScheduledTask -TaskName '{task['name']}' -Confirm:$false -ErrorAction SilentlyContinue"],
            capture_output=True
        )
        logger.info(f"Removed: {task['name']}")

    if pm2_available():
        for watcher in PM2_WATCHERS:
            run(["pm2", "delete", watcher["name"]], check=False)
            logger.info(f"Stopped PM2: {watcher['name']}")


def main():
    parser = argparse.ArgumentParser(description="AI Employee — Scheduler Setup (Silver Tier)")
    parser.add_argument("--status", action="store_true", help="Show status of all jobs")
    parser.add_argument("--remove", action="store_true", help="Remove all scheduled tasks and PM2 daemons")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.remove:
        remove_all()
        return

    logger.info("Setting up Gold Tier scheduler...")
    pm2_ok = setup_pm2()
    setup_scheduler()
    logger.info("Setup complete. Run with --status to verify.")
    print_status()


if __name__ == "__main__":
    main()
