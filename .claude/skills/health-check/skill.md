# Health Check Skill

## Trigger
Use this skill when the user runs `/health-check` or asks "is everything working?", "system status", "check all services", or "run diagnostics".

## Purpose
Quick diagnostic check of all AI Employee components — watchers, MCP servers, vault structure, and credentials.

## Steps

### 1. Check Vault Structure
Verify all required folders exist:
- `AI_Employee_Vault/Inbox/` ✅/❌
- `AI_Employee_Vault/Needs_Action/` ✅/❌
- `AI_Employee_Vault/Plans/` ✅/❌
- `AI_Employee_Vault/Pending_Approval/` ✅/❌
- `AI_Employee_Vault/Approved/` ✅/❌
- `AI_Employee_Vault/Rejected/` ✅/❌
- `AI_Employee_Vault/Done/` ✅/❌
- `AI_Employee_Vault/Logs/` ✅/❌
- `AI_Employee_Vault/Briefings/` ✅/❌
- `AI_Employee_Vault/Accounting/` ✅/❌

### 2. Check Key Files
- `AI_Employee_Vault/Dashboard.md` — exists and recently updated?
- `AI_Employee_Vault/Company_Handbook.md` — exists?
- `.env` file — exists (don't read contents)?
- `hooks/ralph_wiggum.py` — exists?

### 3. Check MCP Servers
- `mcp/email-server/index.js` — file exists ✅/❌
- `mcp/odoo-server/index.js` — file exists ✅/❌
- `mcp/social-server/index.js` — file exists ✅/❌
- `mcp/email-server/node_modules/` — npm installed ✅/❌

### 4. Check Watcher Scripts
- `watchers/filesystem_watcher.py` ✅/❌
- `watchers/gmail_watcher.py` ✅/❌
- `watchers/linkedin_watcher.py` ✅/❌
- `watchers/twitter_watcher.py` ✅/❌
- `watchers/facebook_watcher.py` ✅/❌

### 5. Check Queue Sizes
- `/Needs_Action/` count — alert if >10
- `/Pending_Approval/` count — list items if any
- `/Approved/` count — unprocessed approvals

### 6. Generate Health Report
```
# AI Employee Health Check — <YYYY-MM-DD HH:MM>

## Overall Status: 🟢 HEALTHY / 🟡 DEGRADED / 🔴 CRITICAL

## Vault Structure:     ✅ All folders present
## Key Files:           ✅ All present
## MCP Servers:         ✅/⚠️ X/3 operational
## Watcher Scripts:     ✅ All present
## Queue Status:        ✅/⚠️ X items pending

## Issues Found:
- <issue> → <recommended fix>

## Recommendations:
- <action item>
```

### 7. Update Dashboard
Add health check result to `AI_Employee_Vault/Dashboard.md` system status section.

## Notes
- Run this at start of any session
- Non-destructive — read-only checks
- Does NOT test live API connections (that requires credentials)
