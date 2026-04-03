# Odoo Get Customers Skill

## Trigger
Use this skill when the user runs `/odoo-get-customers` or asks to "list customers", "show clients", "who are our customers", or "customer database".

## Purpose
Retrieve the customer list from Odoo with their outstanding balances and recent activity.

## Steps

### 1. Call Odoo MCP
Call `odoo_get_customers` tool with:
- `limit`: max customers to return (default: 50)
- `with_balance`: include outstanding balance (default: true)

### 2. Display Customer List
```markdown
# Customer List from Odoo
**Total Customers:** X
**Retrieved:** <timestamp>

| Customer | Email | Outstanding | Last Invoice |
|----------|-------|------------|--------------|
| Client A | a@co.com | $1,500 | 2026-03-15 |
| Client B | b@co.com | $0 | 2026-02-28 |

## Customers with Outstanding Balances: X
**Total Outstanding:** $X,XXX
```

### 3. Flag Overdue Customers
- Customers with invoices >30 days overdue: create action file in Needs_Action for follow-up
- Log to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`

## Notes
- Requires Odoo running: `docker-compose up -d`
- Use for CEO Briefing customer section
- Cross-reference with email actions for customer communications
