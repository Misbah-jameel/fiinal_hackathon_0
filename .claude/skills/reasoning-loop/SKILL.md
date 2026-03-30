---
name: reasoning-loop
description: |
  Run the AI Employee's full Silver-tier reasoning loop. Scans all Watcher outputs
  across /Needs_Action, applies Company_Handbook rules, creates detailed Plan.md files
  with prioritized steps, routes sensitive actions to /Pending_Approval, and updates
  Dashboard.md. Use this as the core "brain" that turns raw inbox items into structured plans.
---

# Reasoning Loop — AI Employee Brain (Silver Tier)

This is the Silver Tier upgrade of the Bronze `process-vault` skill. It handles
multi-source inputs (Gmail + File System + LinkedIn), applies deeper reasoning,
and produces structured `Plan.md` files with full context.

---

## When to Run

- After any Watcher deposits new files into `/Needs_Action/`
- On a scheduled basis (e.g., every 30 minutes via Task Scheduler)
- Manually, when you want Claude to process the queue

---

## Full Reasoning Loop — Step by Step

### Step 1 — Load Rules

Read the following files before reasoning on any item:

```
AI_Employee_Vault/Company_Handbook.md     ← Rules of engagement
AI_Employee_Vault/Business_Goals.md       ← Current objectives and KPIs
AI_Employee_Vault/Dashboard.md            ← Current system state
```

If `Business_Goals.md` does not exist, create it using the template below and
ask the owner to fill in their Q1 goals.

**Business_Goals.md template:**
```markdown
---
last_updated: YYYY-MM-DD
review_frequency: weekly
---

## Q1 2026 Objectives

### Revenue Target
- Monthly goal: $10,000
- Current MTD: $0

### Key Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |

### Active Projects
1. Project Alpha — Due: TBD — Budget: $0

### Subscription Audit Rules
Flag if: no login in 30 days, cost up >20%, duplicate tool
```

---

### Step 2 — Scan /Needs_Action

List all `.md` files in `/Needs_Action/`. Group by type:

| Type | Source | Examples |
|------|---------|---------|
| `email` | Gmail Watcher | Client queries, invoices, follow-ups |
| `file_drop` | File System Watcher | Documents, PDFs, spreadsheets |
| `communication` | Manual / other | WhatsApp, messages |
| `linkedin` | LinkedIn Watcher | Comments, DMs, connection requests |

Only process files where frontmatter `status: pending`.
Sort by priority: P1 → P2 → P3 → P4.

---

### Step 3 — Reason on Each Item

For each pending item, apply this reasoning chain:

```
1. IDENTIFY: What is this? (email, task, document, notification)
2. CLASSIFY: Who sent it? What do they want?
3. CONNECT: Does this relate to a Business_Goal or active project?
4. PRIORITIZE: P1/P2/P3/P4 per Company_Handbook §3
5. DECIDE: Can I act autonomously? Or does this need approval?
6. PLAN: What are the exact next steps?
```

---

### Step 4 — Create Plan.md

For every item, create a Plan file in `/Plans/`:

**Filename:** `PLAN_<slug>_<YYYY-MM-DD>.md`

**Full Plan template:**

```markdown
---
created: 2026-02-26T10:00:00
source_file: Needs_Action/<filename>.md
source_type: email | file_drop | communication | linkedin
status: in_progress
priority: P1 | P2 | P3 | P4
sla_deadline: 2026-02-27T10:00:00
related_goal: <Business_Goals section if applicable>
---

## Objective
<Single sentence — what outcome are we driving toward?>

## Context
<2–4 sentences: who, what, why, any relevant history>

## Reasoning
<Why is this priority P[n]? What rule from Company_Handbook applies?>

## Action Steps
- [x] Item received and classified
- [ ] Step 2 — <description>
- [ ] Step 3 — <description> ← REQUIRES APPROVAL (if sensitive)
- [ ] Step 4 — Update Dashboard.md
- [ ] Step 5 — Move to /Done/

## Autonomy Assessment
**Can act autonomously:** Yes / No
**Reason:** <Cite specific handbook rule>
**Approval file needed:** Yes / No → `/Pending_Approval/<filename>`

## Dependencies
- Waiting on: <owner action / other plan / external system>

## Notes
<Any observations, warnings, or context for the owner>
```

---

### Step 5 — Route Sensitive Actions

For every step marked **REQUIRES APPROVAL**, create an approval request:

**File:** `AI_Employee_Vault/Pending_Approval/APPROVAL_<type>_<YYYY-MM-DD>.md`

```markdown
---
type: approval_request
action: send_email | post_linkedin | make_payment | delete_file
related_plan: Plans/PLAN_<slug>_<date>.md
created: 2026-02-26T10:00:00
expires: 2026-02-27T10:00:00
status: pending
---

## Action Requested
<Clear one-line description of what will happen if approved>

## Details
| Field | Value |
|-------|-------|
| Action | Send email to client@example.com |
| Subject | Invoice #123 — $800 |
| Risk | Low / Medium / High |

## To Approve
Move this file to `/Approved/` folder.

## To Reject
Move this file to `/Rejected/` folder.

## Auto-expires
If not approved by <timestamp>, this request will be archived.
```

---

### Step 6 — Update Dashboard.md

After processing all items, update Dashboard.md:

**Update these sections:**
1. `last_updated` timestamp in frontmatter
2. System Status table — update queue counts
3. Queue Summary — list each pending item with one-line status
4. Recent Activity — append timestamped entries
5. Weekly Snapshot counters

**Activity log format:**
```
- [2026-02-26 10:05] Processed EMAIL_18f3a2b1.md → Plan created, approval requested
- [2026-02-26 10:05] Processed FILE_invoice.md → Plan created, pending owner review
```

---

### Step 7 — Write Audit Log

Append to `/Logs/YYYY-MM-DD.md` (create if missing):

```markdown
## HH:MM:SS — reasoning_loop_run

- **Items processed:** N
- **Plans created:** N
- **Approval requests created:** N
- **Items auto-completed:** N
- **Errors:** 0

### Item Detail
| Item | Type | Priority | Outcome |
|------|------|----------|---------|
| EMAIL_xyz.md | email | P2 | Plan created, approval requested |
| FILE_abc.md | file_drop | P3 | Plan created, pending review |
```

---

### Step 8 — Move Processed Items

When an item has a Plan and all autonomous steps are done:
- Move `.md` from `/Needs_Action/` → `/Done/`
- Update its `status` field to `done`
- Move any companion files (e.g., `.txt`, `.pdf`) too

Do NOT move items that still have open steps requiring approval.

---

## Output Summary to User

After the loop completes, report:

```
Reasoning Loop Complete — 2026-02-26 10:05

Items processed : 3
Plans created   : 3
Needs approval  : 2  → check /Pending_Approval/
Auto-completed  : 1
Errors          : 0

Approval queue:
  • APPROVAL_send_email_2026-02-26.md  (reply to client invoice query)
  • APPROVAL_linkedin_post_2026-02-26.md  (LinkedIn win post draft)
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| `Company_Handbook.md` missing | HALT — log error, notify owner |
| `Business_Goals.md` missing | Create template, continue with warning |
| Item file unreadable | Log to `/Logs/errors.md`, skip item |
| /Needs_Action is empty | Report "Queue is clear." and exit |
| Unknown item type | Classify as `other`, assign P3, flag for owner review |
