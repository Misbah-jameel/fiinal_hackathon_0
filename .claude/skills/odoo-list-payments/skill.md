# Odoo List Payments Skill

## Trigger
Use this skill when the user runs `/odoo-list-payments` or asks for "list payments", "payment history", "what payments came in", or "recent transactions".

## Purpose
Retrieve recent payment records from Odoo — both incoming (customer payments) and outgoing (vendor payments).

## Steps

### 1. Call Odoo MCP
Call `odoo_list_payments` tool with:
- `days`: lookback period (default: 7)
- `payment_type`: inbound, outbound, or all

### 2. Display Payments
```markdown
# Payment History — Last <X> Days

## Incoming Payments (Received)
| Date | Customer | Amount | Reference |
|------|----------|--------|-----------|
| 2026-04-01 | Client A | $1,500 | INV/001 |

**Total Received:** $X,XXX

## Outgoing Payments (Sent)
| Date | Vendor | Amount | Reference |
|------|--------|--------|-----------|
| 2026-03-30 | Vendor B | $500 | BILL/001 |

**Total Sent:** $X,XXX

## Net Cash Flow: $X,XXX
```

### 3. Flag Large Payments
- Any outgoing payment >$500: verify it has an approval record
- Log to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`

## Notes
- Requires Odoo running: `docker-compose up -d`
- Included in CEO Briefing automatically
- Cross-reference with Company Handbook $50 approval threshold
