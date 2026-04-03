# Error Recovery Skill

## Trigger
Use this skill when the user runs `/error-recovery` or asks to "check errors", "recover from failures", "run health check + fix errors", or "diagnose system issues".

## Purpose
Scan the AI Employee system for errors, apply recovery logic, and restore normal operation. Uses `skills/error_recovery.py` as the backend.

## Steps

### 1. Scan Error Log
- Read `AI_Employee_Vault/Logs/errors.md`
- List files in `AI_Employee_Vault/Quarantine/` (corrupted files)
- Check `AI_Employee_Vault/Logs/<today>.md` for recent errors

### 2. Check System Health
For each component, verify it is functional:
- **Gmail Watcher** — can it reach Gmail API?
- **Email MCP** — is `mcp/email-server/index.js` running?
- **Odoo MCP** — can it reach Odoo (localhost:8069)?
- **Social MCP** — are Twitter/Facebook/LinkedIn tokens valid?
- **Obsidian Vault** — are all required folders present?

### 3. Apply Recovery Actions

| Error Type | Recovery Action |
|-----------|----------------|
| Stale lock files | Remove `.lock` files from vault folders |
| Quarantined files | Review and either restore or archive |
| API token expired | Flag in Dashboard, note which service |
| MCP server down | Restart instruction logged |
| Missing vault folders | Re-create missing directories |
| Duplicate action files | Move duplicates to Done with `_duplicate` suffix |

### 4. Generate Recovery Report
```markdown
# Error Recovery Report — <YYYY-MM-DD HH:MM>

## Errors Found: X
## Errors Fixed: X
## Manual Intervention Needed: X

### Fixed
- <error> → <fix applied>

### Needs Manual Attention
- <error> → <recommended action>
```

### 5. Update Dashboard
- Update `AI_Employee_Vault/Dashboard.md` system health section
- Clear resolved errors from `AI_Employee_Vault/Logs/errors.md`
- Log recovery run to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`

## Notes
- Run this after any unexpected system behavior
- Included in CEO Briefing automatically
- Never deletes files — moves to Quarantine for human review
