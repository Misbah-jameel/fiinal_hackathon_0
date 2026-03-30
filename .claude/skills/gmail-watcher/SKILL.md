---
name: gmail-watcher
description: |
  Run and manage the Gmail Watcher for the AI Employee. Monitors Gmail for unread
  important emails and creates structured action files in /Needs_Action. Use this
  skill to start the watcher, check its status, or diagnose Gmail API issues.
  Requires Google OAuth credentials configured in .env
---

# Gmail Watcher — AI Employee Perception Layer

The Gmail Watcher is one of the AI Employee's sensory scripts. It polls Gmail
every 2 minutes for unread, important emails and writes `.md` action files into
`/Needs_Action/` for Claude to process.

---

## Prerequisites

### 1. Google Cloud Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Gmail API**
3. Go to **Credentials** → Create **OAuth 2.0 Client ID** (Desktop App)
4. Download `credentials.json` → place at project root (never in vault)
5. Add to `.env`:

```
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Required packages: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`

### 3. First-run OAuth (one-time browser login)

```bash
python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --auth
```

A browser window will open. Log in and grant access. Token saved to `token.json`.

---

## Start the Watcher

```bash
# Default (checks every 120 seconds)
python watchers/gmail_watcher.py --vault ./AI_Employee_Vault

# Custom interval
python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --interval 60

# Dry run (log detected emails, don't write action files)
DRY_RUN=true python watchers/gmail_watcher.py --vault ./AI_Employee_Vault
```

---

## What It Does

For every **unread + important** Gmail message found:

1. Fetches subject, sender, and snippet
2. Marks the email ID as processed (no duplicates)
3. Creates `/Needs_Action/EMAIL_<id>.md` with:
   - YAML frontmatter: `type`, `from`, `subject`, `received`, `priority`, `status`
   - Email snippet / body
   - Suggested actions checklist

---

## Action File Format

```markdown
---
type: email
from: client@example.com
subject: Invoice #123 - Payment Due
received: 2026-02-26T10:30:00
priority: P2
status: pending
gmail_id: 18f3a2b1c9d4e5f6
---

## Email: Invoice #123 - Payment Due

**From:** client@example.com
**Received:** 2026-02-26 10:30

### Snippet
"Hi, just a reminder that invoice #123 for $800 is due on March 1st..."

### Suggested Actions
- [ ] Review full email in Gmail
- [ ] Reply to sender (REQUIRES APPROVAL)
- [ ] Create invoice record in /Accounting/
- [ ] Flag payment > $50 for approval (per Company_Handbook §2)
```

---

## Gmail Query Filter

The watcher uses this Gmail search query by default:

```
is:unread is:important
```

To customize (edit `gmail_watcher.py`):

```python
GMAIL_QUERY = "is:unread is:important -category:promotions -category:social"
```

---

## Priority Assignment Logic

| Keyword in Subject/Snippet | Auto-Assigned Priority |
|----------------------------|------------------------|
| urgent, asap, emergency    | P1                     |
| invoice, payment, deadline | P2                     |
| (default)                  | P3                     |
| newsletter, FYI, update    | P4                     |

---

## Process New Emails

After the watcher creates action files, run the reasoning loop:

```
/reasoning-loop
```

Or process the full vault:

```
/process-vault
```

---

## Stop the Watcher

```bash
# If running in foreground: Ctrl+C

# If running via PM2:
pm2 stop gmail-watcher
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `403 Forbidden` | Re-run `--auth` flag; check Gmail API is enabled in Cloud Console |
| `token.json` expired | Delete `token.json` and re-run `--auth` |
| No emails detected | Check Gmail query filter; verify emails are marked Important |
| Duplicate action files | Check `processed_ids` set; restart watcher clears in-memory state |
| Watcher crashes overnight | Use PM2: `pm2 start watchers/gmail_watcher.py --interpreter python3` |
