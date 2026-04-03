# Odoo Get Revenue Skill

## Trigger
Use this skill when the user runs `/odoo-get-revenue` or asks for "revenue report", "how much did we make", "monthly revenue", or "sales this month".

## Purpose
Retrieve revenue data from Odoo for the current and previous months.

## Steps

### 1. Call Odoo MCP
Call `odoo_get_revenue` tool with:
- `period`: current_month, last_month, last_30_days, ytd (year to date)

### 2. Display Revenue Report
```markdown
# Revenue Report — <Month> <Year>

## This Month
- **Invoiced:** $X,XXX
- **Collected:** $X,XXX
- **Outstanding:** $X,XXX

## Last Month
- **Invoiced:** $X,XXX
- **Collected:** $X,XXX

## Year to Date
- **Total Revenue:** $X,XXX
- **vs Last Year:** +X% / -X%

## Top Customers
| Customer | Revenue |
|----------|---------|
| Client A | $X,XXX |
| Client B | $X,XXX |
```

### 3. Save and Alert
- Save to `AI_Employee_Vault/Accounting/<YYYY-MM>.md`
- If revenue is down >20% MoM: flag in Dashboard as alert
- Log to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`

### 4. Update Dashboard
Add revenue snapshot to Dashboard.md financial section.

## Notes
- Requires Odoo running: `docker-compose up -d`
- Included automatically in CEO Briefing every Monday
- If Odoo offline: note "Odoo offline — check docker-compose status"
