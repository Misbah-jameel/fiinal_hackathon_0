# Odoo Get Balance Skill

## Trigger
Use this skill when the user runs `/odoo-get-balance` or asks for "account balance", "receivables", "payables", "what's owed to us", or "financial position".

## Purpose
Retrieve the current financial position from Odoo — total receivables, payables, and cash balance.

## Steps

### 1. Call Odoo MCP
Call `odoo_get_balance` tool to get:
- Total Accounts Receivable (money owed TO us)
- Total Accounts Payable (money we OWE)
- Net position

### 2. Display Results
```markdown
# Financial Balance — <YYYY-MM-DD>

| Account | Amount |
|---------|--------|
| Accounts Receivable | $X,XXX |
| Accounts Payable | ($X,XXX) |
| **Net Position** | **$X,XXX** |

**Status:** 🟢 Positive / 🔴 Negative
```

### 3. Alerts
- If payables > receivables: flag in Dashboard
- If any receivable > 30 days overdue: create action file in Needs_Action
- Log to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`

### 4. Update Dashboard
Add balance snapshot to `AI_Employee_Vault/Dashboard.md` financial section.

## Notes
- Requires Odoo running: `docker-compose up -d`
- If Odoo offline: note "Odoo offline — manual review needed"
- Included automatically in CEO Briefing
