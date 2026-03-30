---
name: linkedin-poster
description: |
  Compose and publish LinkedIn posts for the AI Employee's business presence.
  Drafts posts based on business goals and recent activity from the vault,
  places them in /Pending_Approval for human review, then posts via LinkedIn API
  once approved. Use this to generate sales content, share updates, or announce wins.
---

# LinkedIn Poster — AI Employee Social Media Skill

This skill handles the full LinkedIn posting workflow:
**Draft → Review → Approve → Post → Log**

All posts require human approval before publishing (per Company_Handbook §4).

---

## Setup

### 1. LinkedIn API Credentials

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create an app → Request **Share on LinkedIn** and **Sign In with LinkedIn** products
3. Get `Client ID` and `Client Secret`
4. Set redirect URI: `http://localhost:8080/callback`
5. Add to `.env`:

```
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_PERSON_URN=urn:li:person:YOUR_ID
```

### 2. Install dependencies

```bash
pip install requests python-dotenv
```

### 3. Authenticate (one-time)

```bash
python watchers/linkedin_watcher.py --auth
```

---

## Workflow: Compose a Post

When invoked with `/linkedin-poster`, Claude will:

### Step 1 — Read business context

Read these vault files to understand what to post about:
- `AI_Employee_Vault/Company_Handbook.md` — brand voice and tone rules
- `AI_Employee_Vault/Business_Goals.md` — current targets and projects
- `AI_Employee_Vault/Done/` — recently completed tasks (wins to share)
- `AI_Employee_Vault/Dashboard.md` — weekly snapshot

### Step 2 — Draft post content

Draft 1–3 LinkedIn post variations. Follow Company_Handbook tone rules:
- Professional, warm, direct
- No jargon unless audience is technical
- Include a clear call to action
- Optimal length: 150–300 words for engagement
- Use line breaks for readability (LinkedIn renders them)
- Add 3–5 relevant hashtags at the end

**Post types to rotate:**
| Type | Purpose | Frequency |
|------|---------|-----------|
| Win/Result | "We just completed X for a client..." | Weekly |
| Insight | "3 things I learned about AI automation..." | Weekly |
| Question | "What's your biggest workflow bottleneck?" | Bi-weekly |
| Offer | "We're opening 2 spots for AI automation..." | Monthly |

### Step 3 — Write draft to /Pending_Approval

Save draft as:

```
AI_Employee_Vault/Pending_Approval/LINKEDIN_<slug>_<YYYY-MM-DD>.md
```

**Draft file format:**

```markdown
---
type: linkedin_post
status: pending_approval
created: 2026-02-26T09:00:00
post_type: win
scheduled_for: 2026-02-27T09:00:00
---

## LinkedIn Post Draft

---

[Post content here]

We just helped a client cut their invoice processing time by 80% using an
AI automation system built with Claude Code.

Here's what we did:
→ Built a File System Watcher to detect incoming invoices
→ Claude auto-classified and drafted replies
→ Human approved in one click

If you're spending more than 2 hours/week on routine business tasks,
let's talk.

#AIAutomation #ClaudeCode #ProductivityHacks #DigitalFTE #AIEmployee

---

## Approval Instructions

- **To approve:** Move this file to `/Approved/`
- **To reject:** Move this file to `/Rejected/`
- **To edit:** Modify the post content above, then move to `/Approved/`

## Scheduled For
2026-02-27 at 09:00 (peak LinkedIn engagement window)
```

### Step 4 — Wait for owner approval

Do NOT post until the owner moves the file to `/Approved/`.

### Step 5 — Post to LinkedIn (after approval detected)

When the orchestrator detects an approved LinkedIn file:

```bash
python watchers/linkedin_watcher.py --post "AI_Employee_Vault/Approved/LINKEDIN_<slug>.md"
```

Or via the LinkedIn API directly:

```python
# POST https://api.linkedin.com/v2/ugcPosts
payload = {
    "author": "urn:li:person:{PERSON_ID}",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {"text": post_content},
            "shareMediaCategory": "NONE"
        }
    },
    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
}
```

### Step 6 — Log and update Dashboard

After posting:
- Log to `/Logs/YYYY-MM-DD.md` with post ID and timestamp
- Update `Dashboard.md` Recent Activity
- Move approved file to `/Done/`

---

## LinkedIn Watcher (Monitor for Engagement Opportunities)

The LinkedIn Watcher monitors your LinkedIn notifications for:
- Comments mentioning your business keywords
- Connection requests from target profiles
- Messages containing sales trigger words

```bash
python watchers/linkedin_watcher.py --vault ./AI_Employee_Vault --watch
```

Detected opportunities are saved to `/Needs_Action/LINKEDIN_<type>_<timestamp>.md`.

---

## Scheduling Posts

For regular posting cadence, set up scheduling:

```
/schedule-task
```

Recommended schedule:
- **Tuesday & Thursday, 8–10 AM** — highest LinkedIn engagement
- **Weekly on Monday** — generate post drafts for the week

---

## Handbook Compliance

| Rule | Applied |
|------|---------|
| §1 — No posting without approval | All drafts go to /Pending_Approval first |
| §4 — Autonomy: social posts always need approval | Enforced — never auto-post |
| §5 — Professional, warm, direct tone | Applied to all draft content |
| §6 — Log all external API calls | LinkedIn API calls logged to /Logs/ |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `401 Unauthorized` | Access token expired — re-run `--auth` |
| Post not appearing | Check LinkedIn app has Share product approved |
| Rate limit hit | LinkedIn allows ~150 posts/day; space posts out |
| Draft rejected by owner | Update content, move back to `/Pending_Approval/` |
