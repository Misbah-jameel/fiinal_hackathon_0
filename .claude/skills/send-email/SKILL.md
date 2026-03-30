---
name: send-email
description: |
  Send emails via the Email MCP server. Drafts emails based on vault context,
  creates approval files in /Pending_Approval, and sends only after human approval.
  Use this skill to reply to clients, send invoices, or follow up on tasks.
  NEVER sends without explicit owner approval — all sends require /Approved file.
---

# Send Email — AI Employee Email Action Skill (MCP)

This skill manages the full email send workflow:
**Draft → /Pending_Approval → Owner Approves → MCP Sends → Log**

All emails require human approval before sending (per Company_Handbook §1 and §4).

---

## Setup — Email MCP Server

The email MCP server handles the actual sending via Gmail API.

### 1. Install and start the MCP server

```bash
# Install dependencies
cd mcp/email-server
npm install

# Start the MCP server
node index.js
```

The server runs on `http://localhost:3100` by default.

### 2. Register in Claude Code settings

Add to `~/.config/claude-code/mcp.json` (or local `.mcp.json`):

```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["./mcp/email-server/index.js"],
      "env": {
        "GMAIL_CREDENTIALS": "./credentials.json",
        "GMAIL_TOKEN": "./token.json",
        "DRY_RUN": "true"
      }
    }
  ]
}
```

### 3. Verify MCP connection

```bash
claude mcp list
```

Expected output:
```
✓ email  (connected)
```

---

## Workflow: Draft and Send an Email

### Step 1 — Identify the email need

Claude reads the source item in `/Needs_Action/` or a Plan in `/Plans/`
to understand what email is needed:

- Who to send to (from known contacts or vault)
- Subject line
- Body content (per Company_Handbook §5 tone rules)

### Step 2 — Compose the draft

Apply Company_Handbook §5 tone rules:
- Professional, warm, direct
- Under 150 words unless detail is necessary
- Always include a clear call to action
- Subject line: clear and specific

### Step 3 — Create approval file

Save draft to:

```
AI_Employee_Vault/Pending_Approval/EMAIL_<slug>_<YYYY-MM-DD>.md
```

**Approval file format:**

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Invoice #123 — January 2026
related_plan: Plans/PLAN_invoice_2026-02-26.md
created: 2026-02-26T10:30:00
expires: 2026-02-27T10:30:00
status: pending
---

## Email Ready to Send

**To:** client@example.com
**Subject:** Invoice #123 — January 2026

---

Dear [Client Name],

Please find attached your invoice for January 2026 services.

**Amount Due:** $1,500
**Due Date:** March 1, 2026

Please don't hesitate to reach out if you have any questions.

Best regards,
[Your Name]

---

## Attachment
`/Vault/Invoices/2026-01_Client.pdf` (if applicable)

## To Approve
Move this file to `/Approved/` to send the email.

## To Reject
Move this file to `/Rejected/` to cancel.

## To Edit
Modify content above, then move to `/Approved/`.
```

### Step 4 — Wait for approval

Do NOT send until owner moves file to `/Approved/`.

### Step 5 — Send via MCP (after approval detected)

When the Orchestrator detects the approved email file, it calls the MCP:

```python
# orchestrator.py detects /Approved/EMAIL_*.md
# Calls email MCP tool:

await email_mcp.send_email({
    "to": "client@example.com",
    "subject": "Invoice #123 — January 2026",
    "body": "Dear Client...",
    "attachment": "/Vault/Invoices/2026-01_Client.pdf"  # optional
})
```

Or trigger manually:

```bash
python orchestrator.py --send-approved
```

### Step 6 — Log and cleanup

After successful send:
- Log to `/Logs/YYYY-MM-DD.md`:
  ```
  ## HH:MM:SS — email_sent
  - To: client@example.com
  - Subject: Invoice #123
  - Approved by: human
  - Result: success
  - Message-ID: <id>
  ```
- Update Dashboard.md Recent Activity
- Move approved file to `/Done/`
- Update related Plan status to `completed`

---

## Dry Run Mode

Test the full flow without actually sending:

```bash
DRY_RUN=true python orchestrator.py --send-approved
```

Output:
```
[DRY RUN] Would send email to client@example.com
[DRY RUN] Subject: Invoice #123 — January 2026
[DRY RUN] Attachment: /Vault/Invoices/2026-01_Client.pdf
```

Always test with DRY_RUN=true before enabling live sends.

---

## Rate Limiting

Per Company_Handbook security principles, the MCP enforces:
- Maximum **10 emails per hour**
- Maximum **50 emails per day**
- Alert owner if limit is approached

---

## Handbook Compliance

| Rule | Enforced |
|------|---------|
| §1 — No send without approval | Approval file required before MCP call |
| §1 — No unknown contacts | Warn if recipient not in known contacts list |
| §2 — Log all financial emails | Invoice/payment emails tagged and logged |
| §4 — Email always needs approval | Hard-coded: approval check in orchestrator |
| §5 — Tone rules | Applied during draft composition |
| §6 — Log all API calls | Every MCP send logged to /Logs/ |

---

## MCP Server Reference

The `mcp/email-server/` contains a Node.js MCP server exposing these tools:

| Tool | Description |
|------|-------------|
| `email_send` | Send an email with optional attachment |
| `email_draft` | Save a draft to Gmail (does not send) |
| `email_search` | Search Gmail inbox |
| `email_get` | Fetch a specific email by ID |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| MCP not connected | Run `node mcp/email-server/index.js` and check `claude mcp list` |
| `403 Forbidden` | Re-authenticate Gmail OAuth token |
| Email not delivered | Check spam folder; verify sender domain |
| Approval file not detected | Ensure orchestrator is running: `python orchestrator.py` |
| Rate limit hit | Wait 1 hour or check if send loop is stuck |
