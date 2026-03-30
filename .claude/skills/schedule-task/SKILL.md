---
name: schedule-task
description: |
  Set up and manage scheduled tasks for the AI Employee using Windows Task Scheduler
  or PM2. Use this skill to automate recurring jobs: run the reasoning loop every
  30 minutes, trigger LinkedIn posting on Tuesday/Thursday mornings, generate weekly
  CEO briefings, or keep watcher scripts alive 24/7.
---

# Schedule Task — AI Employee Scheduler (Silver Tier)

This skill sets up automated scheduling so the AI Employee runs continuously
without manual intervention. Uses Windows Task Scheduler (primary) and PM2 (for
process persistence).

---

## What to Schedule

| Job | Trigger | Command |
|-----|---------|---------|
| Gmail Watcher | On startup, keep alive | PM2 daemon |
| File System Watcher | On startup, keep alive | PM2 daemon |
| LinkedIn Watcher | On startup, keep alive | PM2 daemon |
| Reasoning Loop | Every 30 minutes | Task Scheduler |
| HITL Approval Check | Every 5 minutes | Task Scheduler |
| LinkedIn Post Draft | Tue & Thu 7:00 AM | Task Scheduler |
| Weekly CEO Briefing | Monday 7:00 AM | Task Scheduler |
| Dashboard Refresh | Every 15 minutes | Task Scheduler |

---

## Part A — Persistent Watchers with PM2

PM2 keeps watcher scripts alive and restarts them if they crash.

### Install PM2

```bash
npm install -g pm2
```

### Start all watchers

```bash
# Start Gmail Watcher
pm2 start watchers/gmail_watcher.py --name gmail-watcher --interpreter python3 -- --vault ./AI_Employee_Vault

# Start File System Watcher
pm2 start watchers/filesystem_watcher.py --name file-watcher --interpreter python3 -- --vault ./AI_Employee_Vault

# Start LinkedIn Watcher
pm2 start watchers/linkedin_watcher.py --name linkedin-watcher --interpreter python3 -- --vault ./AI_Employee_Vault
```

### Persist across reboots

```bash
pm2 save
pm2 startup
# Follow the printed command (run it as admin)
```

### Check watcher status

```bash
pm2 status
pm2 logs gmail-watcher --lines 50
```

### Restart a crashed watcher

```bash
pm2 restart gmail-watcher
pm2 restart all
```

---

## Part B — Scheduled Jobs with Windows Task Scheduler

Use Task Scheduler for timed Claude Code invocations.

### Method: PowerShell wrapper script

Create `scheduler/run_claude.ps1`:

```powershell
# scheduler/run_claude.ps1
param([string]$Skill, [string]$Vault = "D:\fiinal_hackathon_0\AI_Employee_Vault")

Set-Location "D:\fiinal_hackathon_0"
$env:VAULT_PATH = $Vault

# Run Claude with the specified skill
$output = claude --print "/$Skill" 2>&1

# Log output
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logFile = "$Vault\Logs\scheduler.log"
Add-Content -Path $logFile -Value "[$timestamp] $Skill run completed"
Add-Content -Path $logFile -Value $output
```

### Create scheduled tasks via PowerShell (run as Administrator)

**Reasoning Loop — every 30 minutes:**

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -File D:\fiinal_hackathon_0\scheduler\run_claude.ps1 -Skill reasoning-loop"

$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)

Register-ScheduledTask `
    -TaskName "AIEmployee_ReasoningLoop" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest `
    -Description "AI Employee reasoning loop every 30 minutes"
```

**HITL Approval Check — every 5 minutes:**

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -File D:\fiinal_hackathon_0\scheduler\run_claude.ps1 -Skill hitl-approval"

$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)

Register-ScheduledTask `
    -TaskName "AIEmployee_HITLApproval" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest `
    -Description "AI Employee HITL approval check every 5 minutes"
```

**LinkedIn Post Draft — Tuesday & Thursday 7:00 AM:**

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -File D:\fiinal_hackathon_0\scheduler\run_claude.ps1 -Skill linkedin-poster"

$triggerTue = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At "7:00AM"
$triggerThu = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At "7:00AM"

Register-ScheduledTask `
    -TaskName "AIEmployee_LinkedInPoster" `
    -Action $action `
    -Trigger @($triggerTue, $triggerThu) `
    -RunLevel Highest `
    -Description "AI Employee LinkedIn post draft — Tue & Thu 7AM"
```

**Weekly CEO Briefing — Monday 7:00 AM:**

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -File D:\fiinal_hackathon_0\scheduler\run_claude.ps1 -Skill reasoning-loop"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "7:00AM"

Register-ScheduledTask `
    -TaskName "AIEmployee_WeeklyCEOBriefing" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest `
    -Description "AI Employee weekly CEO briefing every Monday 7AM"
```

---

## Part C — Quick Setup Script

Run this once to set up everything:

```bash
python scheduler/setup_scheduler.py
```

The setup script will:
1. Install PM2 (if not present)
2. Start all watcher daemons
3. Create all Task Scheduler jobs
4. Verify everything is running
5. Print status summary

---

## Verify All Jobs

```bash
python scheduler/setup_scheduler.py --status
```

Expected output:
```
PM2 Daemons:
  ✓ gmail-watcher    (online, uptime: 2h)
  ✓ file-watcher     (online, uptime: 2h)
  ✓ linkedin-watcher (online, uptime: 2h)

Task Scheduler Jobs:
  ✓ AIEmployee_ReasoningLoop    (next: 2026-02-26 10:30)
  ✓ AIEmployee_HITLApproval     (next: 2026-02-26 10:05)
  ✓ AIEmployee_LinkedInPoster   (next: 2026-02-27 07:00 Thu)
  ✓ AIEmployee_WeeklyCEOBriefing(next: 2026-03-02 07:00 Mon)
```

---

## Disable / Remove a Job

```bash
# PM2
pm2 stop gmail-watcher
pm2 delete gmail-watcher

# Task Scheduler
Unregister-ScheduledTask -TaskName "AIEmployee_ReasoningLoop" -Confirm:$false
```

---

## Scheduler Log

All scheduled runs are logged to:

```
AI_Employee_Vault/Logs/scheduler.log
```

Format:
```
[2026-02-26 10:00:00] reasoning-loop run completed
[2026-02-26 10:00:05] hitl-approval run completed
[2026-02-26 10:30:00] reasoning-loop run completed
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Task Scheduler job not running | Check "Run with highest privileges" is checked |
| PM2 watcher not restarting | Run `pm2 resurrect` after reboot |
| `claude` command not found in Task Scheduler | Use full path: `C:\Users\<user>\AppData\Roaming\npm\claude.cmd` |
| Reasoning loop running too often | Increase interval in Task Scheduler trigger |
| Logs not written | Check vault path in `run_claude.ps1` |
