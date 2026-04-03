# Odoo Create Invoice Skill

## Trigger
Use this skill when the user runs `/odoo-create-invoice` or asks to "create an invoice", "bill a client", or "make a new invoice in Odoo".

## Purpose
Draft a new invoice in Odoo via MCP, route through HITL approval before posting (draft-only by default).

## Steps

### 1. Gather Invoice Details
Ask or extract from context:
- Customer name / Odoo partner ID
- Invoice lines (description, quantity, unit price)
- Due date
- Notes

### 2. Create Approval File
Create `AI_Employee_Vault/Pending_Approval/APPROVAL_CREATE_INVOICE_<YYYY-MM-DD>.md`:
```
---
type: odoo_create_invoice
status: pending_approval
created: <timestamp>
---

# Create Invoice — Pending Approval

## Customer: <name>
## Lines:
| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| <desc> | 1 | $X | $X |

## Total: $X
## Due Date: <date>

## Action Required
Move to /Approved/ to create in Odoo, or /Rejected/ to cancel.
```

### 3. Wait for Approval
- Inform user: "Invoice draft in /Pending_Approval/ — move to /Approved/ to create"
- Do NOT create in Odoo until approved

### 4. On Approval (via /hitl-approval)
- Call `odoo_create_invoice` MCP tool (creates as DRAFT in Odoo)
- Log result to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`
- Log to `AI_Employee_Vault/Accounting/` summary
- Update Dashboard.md

## Notes
- Invoices are created in DRAFT state — requires manual confirmation in Odoo UI to post
- Payments are NEVER initiated automatically
- Flag any amount over $500 per Company Handbook rules
