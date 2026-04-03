# Odoo Get Invoices Skill

## Trigger
Use this skill when the user runs `/odoo-get-invoices` or asks to "show invoices", "list invoices", "get invoices from Odoo", or "what invoices do we have".

## Purpose
Retrieve and display invoice data from Odoo Community via the Odoo MCP server.

## Steps

### 1. Call Odoo MCP
Call `odoo_get_invoices` tool with optional filters:
- `state`: draft, posted, cancel (default: all)
- `limit`: number of invoices (default: 20)
- `date_from` / `date_to`: date range filter

### 2. Format Results
```markdown
# Invoices from Odoo
**Retrieved:** <timestamp>
**Total Shown:** X

| # | Invoice | Customer | Amount | Status | Due Date |
|---|---------|----------|--------|--------|----------|
| 1 | INV/2026/001 | Client A | $1,500 | Posted | 2026-04-15 |
| 2 | INV/2026/002 | Client B | $3,200 | Draft | 2026-04-30 |

**Total Outstanding:** $X,XXX
**Overdue:** X invoices ($X,XXX)
```

### 3. Flag Overdue Invoices
- If any invoices are overdue, create action file in `AI_Employee_Vault/Needs_Action/`
- Log to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`

## Notes
- Requires Odoo running at localhost:8069 (Docker)
- Start Odoo: `docker-compose up -d` from project root
- If Odoo offline: log error, surface in Dashboard
