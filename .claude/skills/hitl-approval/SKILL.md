---
name: hitl-approval
description: |
  Manage the Human-in-the-Loop (HITL) approval workflow. Reviews /Pending_Approval
  for items awaiting decision, checks /Approved and /Rejected for owner decisions,
  executes approved actions via MCP, cancels rejected ones, and logs everything.
  Use this skill to process the approval queue and act on owner decisions.
---

# HITL Approval — Human-in-the-Loop Workflow (Silver Tier)

The HITL workflow is the AI Employee's safety system. Sensitive actions are never
taken automatically — they wait in `/Pending_Approval/` until the owner moves
them to `/Approved/` or `/Rejected/`.

---

## How HITL Works

```
Claude creates action  →  /Pending_Approval/  →  Owner reviews
                                                        ↓
                           /Rejected/  ←  No    Owner decides    Yes  →  /Approved/
                               ↓                                               ↓
                         Log + Archive                          Orchestrator executes
                                                                      ↓
                                                                 /Done/ + Log
```

---

## Folder Roles

| Folder | Purpose |
|--------|---------|
| `/Pending_Approval/` | Items waiting for owner decision |
| `/Approved/` | Owner said YES — orchestrator will execute |
| `/Rejected/` | Owner said NO — action cancelled |
| `/Done/` | Executed and logged |

---

## When Invoked: `/hitl-approval`

Claude will:

1. Scan `/Pending_Approval/` for pending items
2. Scan `/Approved/` for newly approved items → execute them
3. Scan `/Rejected/` for rejected items → clean up
4. Update Dashboard.md and log all activity

---

## Step 1 — Scan Pending Queue

Read all `.md` files in `/Pending_Approval/` with `status: pending`.

For each item, display a summary:

```
Pending Approval Queue (3 items):

1. EMAIL_invoice_client_2026-02-26.md  [P2]
   → Send invoice to client@example.com ($1,500)
   → Expires: 2026-02-27 10:30

2. LINKEDIN_win_post_2026-02-26.md  [P3]
   → Post LinkedIn update about project completion
   → Expires: 2026-02-28 09:00

3. APPROVAL_payment_vendor_2026-02-26.md  [P1]
   → Pay vendor@example.com $450 for services
   → Expires: 2026-02-26 18:00  ⚠ EXPIRING SOON
```

---

## Step 2 — Process Approved Items

Scan `/Approved/` for `.md` files. For each:

### Email approved → send via MCP
```python
# Reads EMAIL_*.md from /Approved/
# Calls email MCP: email_send(to, subject, body, attachment)
# Logs result
# Moves to /Done/
```

### LinkedIn post approved → post via API
```python
# Reads LINKEDIN_*.md from /Approved/
# Calls LinkedIn API: POST /v2/ugcPosts
# Logs result with post ID
# Moves to /Done/
```

### Payment approved → create payment record
```python
# Reads APPROVAL_payment_*.md from /Approved/
# Creates /Accounting/Payment_<id>.md record
# Does NOT auto-pay — creates record for manual execution
# Moves to /Done/
```

### Unknown action type → alert owner
```
Unknown action type in approved file. Skipping. Owner review needed.
```

---

## Step 3 — Process Rejected Items

Scan `/Rejected/` for `.md` files. For each:

1. Update file `status` to `rejected`
2. Log the rejection with timestamp
3. Update the related Plan: mark step as `rejected`
4. Move file from `/Rejected/` to `/Done/` (archive)

**Rejection log format:**
```markdown
## HH:MM:SS — action_rejected

- **File:** APPROVAL_payment_vendor_2026-02-26.md
- **Action:** Pay vendor@example.com $450
- **Rejected at:** 2026-02-26T14:30:00
- **Related Plan:** Plans/PLAN_vendor_payment_2026-02-26.md
- **Next step:** Owner should create new plan or close task
```

---

## Step 4 — Handle Expired Approvals

Check all `/Pending_Approval/` items for `expires` timestamp.
If expired and still `status: pending`:

1. Update status to `expired`
2. Move to `/Done/` with `expired` status
3. Log the expiry
4. Notify owner via Dashboard.md

```markdown
## ⚠ Expired Approval
- APPROVAL_payment_vendor_2026-02-26.md expired at 2026-02-26T18:00
- Action was NOT taken. Recreate if still needed.
```

---

## Step 5 — Update Dashboard

After processing all queues, update `Dashboard.md`:

```markdown
### Pending Approval
- LINKEDIN_win_post_2026-02-26.md — LinkedIn post (awaiting approval)

### Recently Executed
- [2026-02-26 14:00] EMAIL_invoice_client sent ✓
- [2026-02-26 14:05] LINKEDIN_project_update posted ✓

### Recently Rejected
- [2026-02-26 14:30] APPROVAL_payment_vendor rejected ✗
```

---

## Step 6 — Write Audit Log

Append to `/Logs/YYYY-MM-DD.md`:

```markdown
## HH:MM:SS — hitl_approval_run

- **Pending scanned:** 3
- **Approved executed:** 1 (email sent)
- **Rejected archived:** 1
- **Expired archived:** 0
- **Still pending:** 1

### Execution Detail
| File | Action | Result |
|------|--------|--------|
| EMAIL_invoice_client.md | send_email | ✓ success |
| APPROVAL_payment_vendor.md | payment_record | ✗ rejected |
```

---

## Approval File Spec

All approval files must have this frontmatter:

```yaml
---
type: approval_request
action: send_email | post_linkedin | make_payment | delete_file | other
related_plan: Plans/PLAN_<slug>_<date>.md
created: ISO8601
expires: ISO8601
status: pending | approved | rejected | expired
---
```

---

## Handbook Compliance

| Rule | HITL Enforcement |
|------|-----------------|
| §1 — No send without approval | EMAIL_ files blocked until /Approved/ |
| §2 — Payments always need approval | PAYMENT_ files blocked until /Approved/ |
| §4 — Social posts need approval | LINKEDIN_ files blocked until /Approved/ |
| §4 — File deletes need approval | DELETE_ files blocked until /Approved/ |
| §6 — Log all external API calls | Every execution logged to /Logs/ |
| §9 — Never silently fail | All errors surfaced to Dashboard.md |

---

## Orchestrator Integration

The HITL skill is called by `orchestrator.py` on a loop:

```python
# orchestrator.py watches /Approved/ and /Rejected/ folders
# When new files appear, it triggers the HITL execution

observer.schedule(ApprovalHandler(vault_path), str(approved_dir), recursive=False)
observer.schedule(RejectionHandler(vault_path), str(rejected_dir), recursive=False)
```

You can also trigger it manually:

```bash
python orchestrator.py --process-approvals
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Approved file not executed | Check orchestrator is running; check MCP connection |
| Action executed twice | Check for duplicate files in /Approved/ |
| Expired items piling up | Lower expiry window or check owner review cadence |
| Unknown action type error | Inspect frontmatter `action` field for typos |
