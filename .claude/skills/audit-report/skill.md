# Audit Report Skill

## Trigger
Use this skill when the user runs `/audit-report` or asks for "audit report", "compliance report", "activity log summary", or "what happened this week".

## Purpose
Generate a structured audit/compliance report from the vault logs covering all AI Employee actions, decisions, and outcomes for a specified period.

## Steps

### 1. Collect Audit Data
- Read all log files in `AI_Employee_Vault/Logs/` for the specified period (default: last 7 days)
- Count files in `AI_Employee_Vault/Done/` created in period
- Count files in `AI_Employee_Vault/Approved/` and `AI_Employee_Vault/Rejected/`
- Check `AI_Employee_Vault/Logs/errors.md` for error count

### 2. Generate Report
```markdown
# AI Employee Audit Report
**Period:** <start> to <end>
**Generated:** <timestamp>
**Tier:** Gold

## Activity Summary
| Category | Count |
|----------|-------|
| Tasks Processed | X |
| Emails Handled | X |
| Social Posts Published | X |
| Approvals Requested | X |
| Approvals Granted | X |
| Approvals Rejected | X |
| Errors Logged | X |
| Errors Recovered | X |

## Actions by Day
| Date | Tasks | Emails | Posts | Errors |
|------|-------|--------|-------|--------|
| <date> | X | X | X | X |

## HITL Compliance
- All sensitive actions routed through approval: ✅/❌
- Payment actions with human sign-off: ✅/❌
- No unauthorized sends: ✅/❌

## Data Retention
- Logs older than 90 days: 0 (within retention policy)
- Sensitive data redacted: ✅

## Recommendations
- <insight based on data>
```

### 3. Save Report
- Save to `AI_Employee_Vault/Briefings/AUDIT_<YYYY-MM-DD>.md`
- Log generation to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`
- Update Dashboard.md with last audit date

## Notes
- Run weekly or on-demand
- Automatically included in CEO Briefing
- Uses `skills/audit_logger.py` for structured JSONL data
