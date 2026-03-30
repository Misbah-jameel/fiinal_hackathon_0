---
name: process-vault
description: |
  Process the AI Employee Obsidian vault. Reads items from /Needs_Action, creates
  Plans in /Plans, updates Dashboard.md, and moves completed items to /Done.
  Use this skill when the user wants to run the AI Employee's reasoning loop on
  the vault — triaging inbox items, drafting plans, and updating the dashboard.
---

# Process Vault — AI Employee Reasoning Loop

This skill executes the core reasoning loop of the AI Employee (Bronze Tier).

## Vault Location

The vault is at `./AI_Employee_Vault/` relative to the project root, or at the path
specified by the user. Always resolve the absolute path before operating.

## Step-by-Step Workflow

### Step 1 — Read Company Handbook

Before processing any items, read `Company_Handbook.md` to understand the rules:

```
Read: ./AI_Employee_Vault/Company_Handbook.md
```

This defines priorities, autonomy thresholds, tone, and what requires approval.

---

### Step 2 — Scan /Needs_Action

List all `.md` files in `/Needs_Action/`. For each file:

1. Read the file's YAML frontmatter (`type`, `priority`, `status`).
2. Read the body to understand what action is needed.
3. Classify it: `file_drop`, `email`, `task`, or `other`.

Only process files where `status: pending`. Skip files with `status: in_progress` or `status: done`.

---

### Step 3 — Create a Plan

For each pending item, create a Plan file in `/Plans/`:

**Filename format:** `PLAN_<item_name>_<YYYY-MM-DD>.md`

**Plan template:**

```markdown
---
created: <ISO timestamp>
source_file: <original Needs_Action filename>
status: pending_approval
priority: <P1/P2/P3/P4>
---

## Objective
<One sentence describing what needs to happen>

## Context
<Brief summary of the item — what triggered this, from whom, about what>

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3 (if approval needed, mark: REQUIRES APPROVAL)

## Autonomy Assessment
**Auto-approve:** <yes/no>
**Reason:** <why this does or does not require human approval per Company_Handbook.md>
```

---

### Step 4 — Handle Approval Requirements

If an action requires approval (per Company_Handbook.md), create an approval request
in `/Pending_Approval/` instead of acting directly:

**Filename:** `APPROVAL_<action_type>_<YYYY-MM-DD>.md`

Do NOT take any external action (send email, post, pay) without an approved file
in `/Approved/`.

---

### Step 5 — Update Dashboard.md

After processing all items, update `Dashboard.md`:

1. Update the **Queue Summary** section with current counts.
2. Append to **Recent Activity** with a timestamped entry for each item processed.
3. Update the `last_updated` field in the frontmatter.

**Activity entry format:**
```
- [YYYY-MM-DD HH:MM] <action taken> — <item name>
```

---

### Step 6 — Move Completed Items to /Done

When an item has been fully processed (plan created, no further action required,
or action has been approved and executed):

1. Move the `.md` file from `/Needs_Action/` to `/Done/`.
2. Update its `status` field to `done`.
3. If a companion file (original dropped file) exists in `/Needs_Action/`, move it too.

---

### Step 7 — Log Actions

Append a log entry to `/Logs/YYYY-MM-DD.md`:

```markdown
## <HH:MM:SS> — <action_type>

- **Item:** <filename>
- **Action:** <what was done>
- **Result:** success / pending_approval / skipped
```

Create the log file if it does not exist for today.

---

## Rules Summary (from Company_Handbook.md)

| Action                          | Auto-Approve | Requires Approval |
|---------------------------------|:------------:|:-----------------:|
| Read / summarize files          | ✅           |                   |
| Create Plans                    | ✅           |                   |
| Update Dashboard.md             | ✅           |                   |
| Move files between vault folders| ✅           |                   |
| Send email / message            |              | ✅                |
| Make payment                    |              | ✅                |
| Delete any file                 |              | ✅                |
| Post to social media            |              | ✅                |

---

## Example Invocation

User: `/process-vault`

Claude should:
1. Read Company_Handbook.md
2. Scan /Needs_Action for pending items
3. For each: create a Plan and assess autonomy
4. Update Dashboard.md
5. Move processed items to /Done
6. Write a log entry

Output a brief summary to the user: how many items processed, what plans were created,
what requires approval.

---

## Error Handling

- If `/Needs_Action` is empty: Report "No items to process" and exit cleanly.
- If a file cannot be read: Log the error to `/Logs/errors.md` and skip the file.
- If `Company_Handbook.md` is missing: Halt and inform the user — do not proceed without rules.
- Never silently fail. Always report what happened.
