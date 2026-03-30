# Facebook Posting Workflow with Approval System

**AI Employee Gold Tier**

This document describes the complete Facebook posting workflow with Human-in-the-Loop (HITL) approval.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTENT GENERATION                           │
│  Claude generates post content based on:                       │
│  - Business goals                                               │
│  - Scheduled campaigns                                          │
│  - Response to comments/messages                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  APPROVAL REQUEST CREATED                       │
│  File: /Pending_Approval/APPROVAL_FACEBOOK_POST_*.md           │
│  Contains:                                                      │
│  - Post content                                                 │
│  - Target platform                                              │
│  - Scheduled time (optional)                                    │
│  - Context/reason for post                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    HUMAN REVIEW                                 │
│  Human reviews content in /Pending_Approval/                   │
│  Options:                                                       │
│  1. Move to /Approved/ → Post will be published                │
│  2. Move to /Rejected/ → Post cancelled                        │
│  3. Edit content → Move back to /Pending_Approval/             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTION (HITL Skill)                        │
│  HITL approval skill runs every 5 minutes:                     │
│  - Reads approved files                                         │
│  - Calls MCP social_post_facebook                               │
│  - Logs post ID and timestamp                                   │
│  - Moves to /Done/                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      COMPLETION                                 │
│  - Post published to Facebook                                   │
│  - Action logged to /Logs/                                      │
│  - Audit entry created in /Audit/json/                          │
│  - Analytics tracked in Dashboard.md                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Approval File Template

**Location:** `/Pending_Approval/APPROVAL_FACEBOOK_POST_YYYY-MM-DD_timestamp.md`

```markdown
---
type: social_post
platform: facebook
action: page_post
created: 2026-03-17T10:30:00Z
status: pending_approval
priority: P2
expires: 2026-03-18T10:30:00Z
---

# Facebook Post — Awaiting Approval

**Action:** Post to Facebook Page
**Platform:** Facebook
**Created:** 2026-03-17 10:30 AM
**Priority:** P2 (Normal)

## Content to Post

```
🚀 Exciting news! Our AI Employee system just reached a major milestone:

✅ 6 social media platforms integrated
✅ 500+ automated actions processed
✅ 99.9% uptime maintained

Thank you to our amazing community for your support!

#AIEmployee #Automation #Hackathon2026
```

## Context

**Reason:** Weekly business update (scheduled)
**Campaign:** Q1 2026 Social Media Campaign
**Goal:** Engage followers with progress update

## Metadata

- **Character count:** 245
- **Hashtags:** 3
- **Mentions:** 0
- **Media:** None (text-only post)

## Posting Schedule

**Post immediately upon approval**

OR

**Schedule for:** 2026-03-17 2:00 PM (optimal engagement time)

## Instructions

✅ **To Approve:**
1. Review content above
2. Move this file to `/Approved/` folder
3. Post will be published within 5 minutes

❌ **To Reject:**
1. Move this file to `/Rejected/` folder
2. Add comment explaining rejection (optional)

✏️ **To Edit:**
1. Edit the "Content to Post" section
2. Move back to `/Pending_Approval/` (if you made changes)
3. Or move to `/Approved/` when ready

⚠️ **Safety Checks:**
- [ ] Content aligns with Company Handbook
- [ ] No sensitive information disclosed
- [ ] Tone is professional and friendly
- [ ] Hashtags are relevant
```

---

## Step-by-Step Example

### Scenario: Responding to Customer Inquiry

#### Step 1: Facebook Watcher Detects Comment

```
Facebook Watcher → New comment detected:
- Post: "Product announcement"
- User: "John Doe"
- Comment: "This looks amazing! When will it be available?"
```

#### Step 2: Action File Created

**Location:** `/Needs_Action/FACEBOOK_COMMENT_abc123_20260317_143022.md`

```markdown
---
type: facebook_comment
platform: facebook
item_id: abc123
from: John Doe
received: 2026-03-17T14:30:22Z
priority: P2
status: pending
---

# Facebook Comment — Action Required

**Platform:** Facebook
**Type:** Comment
**From:** John Doe
**Time:** 2026-03-17 2:30 PM

## Content

> This looks amazing! When will it be available?

## Original Post

Product announcement post (ID: xyz789)

## Suggested Actions

1. Draft friendly reply with product availability info
2. Include link to website for more details
3. Place in /Pending_Approval before sending
```

#### Step 3: Reasoning Loop Processes

Claude reads the action file and creates a plan:

**Location:** `/Plans/PLAN_FACEBOOK_REPLY_20260317_143500.md`

```markdown
---
type: response_plan
created: 2026-03-17T14:35:00Z
status: in_progress
---

# Plan: Respond to Facebook Comment

## Analysis

- **Sentiment:** Positive (interested customer)
- **Urgency:** Normal (not urgent)
- **Action needed:** Reply with product info

## Draft Response

```
Hi John! Thanks for your interest! 🎉

Our AI Employee system is available NOW for early adopters. 
You can learn more and sign up at: https://example.com

We're offering special hackathon pricing this week!

Let me know if you have any questions. 😊
```

## Next Steps

1. ✅ Draft created
2. ⏳ Awaiting approval → /Pending_Approval/
3. ⏳ Post after approval
4. ⏳ Log action
```

#### Step 4: Approval File Created

**Location:** `/Pending_Approval/APPROVAL_FACEBOOK_REPLY_20260317_143500.md`

```markdown
---
type: social_post
platform: facebook
action: reply_to_comment
created: 2026-03-17T14:35:00Z
status: pending_approval
parent_comment_id: abc123
---

# Facebook Reply — Awaiting Approval

**Action:** Reply to customer comment
**Platform:** Facebook
**Parent Comment:** "This looks amazing! When will it be available?"

## Reply Content

```
Hi John! Thanks for your interest! 🎉

Our AI Employee system is available NOW for early adopters. 
You can learn more and sign up at: https://example.com

We're offering special hackathon pricing this week!

Let me know if you have any questions. 😊
```

## Instructions

- Move to `/Approved/` to post reply
- Move to `/Rejected/` to cancel
```

#### Step 5: Human Approval

**Human action:** Move file from `/Pending_Approval/` to `/Approved/`

#### Step 6: HITL Executes Post

HITL approval skill runs:

```bash
python skills/hitl_approval.py --vault ./AI_Employee_Vault
```

**Actions:**
1. Scans `/Approved/` folder
2. Finds approval file
3. Calls MCP: `social_post_facebook` with reply parameters
4. Facebook posts the reply
5. Logs post ID and timestamp
6. Moves file to `/Done/`

#### Step 7: Completion Logging

**Location:** `/Logs/2026-03-17.md`

```markdown
- [2026-03-17 14:40:15] [SocialMCP] Facebook reply posted: abc123_reply
- [2026-03-17 14:40:15] [HITL] Action completed: APPROVAL_FACEBOOK_REPLY_20260317_143500.md
- [2026-03-17 14:40:15] [Audit] Entry created: facebook_comment_reply
```

---

## Scheduled Posting Workflow

### Weekly Business Update Example

#### Step 1: Scheduled Trigger

Scheduler runs every Tuesday at 7 AM:

```bash
# In setup_scheduler.py
schedule.every().tuesday.at("07:00").do(run_facebook_poster)
```

#### Step 2: Content Generation

Claude generates post based on:
- Business goals from `Business_Goals.md`
- Recent achievements from `/Done/` folder
- Upcoming events from calendar

**Generated Content:**

```markdown
📊 Weekly Progress Update:

✅ Completed 15 client projects
✅ Added 3 new integrations (Facebook, Instagram, Odoo)
✅ Achieved 99.9% uptime
✅ Responded to 50+ customer inquiries

Thank you to our amazing team! 🙌

#Progress #AIEmployee #Automation
```

#### Step 3: Approval Created

File moved to `/Pending_Approval/` (see template above)

#### Step 4: Human Reviews

**Options:**
- ✅ Approve as-is → Move to `/Approved/`
- ✏️ Edit content → Modify and approve
- ❌ Reject → Move to `/Rejected/` with comment

#### Step 5: Post Published

HITL executes at next cycle (within 5 minutes)

---

## Emergency Posting Workflow

For urgent announcements (outages, critical updates):

### Quick Approval Process

1. **Create urgent approval file** with `priority: P0`
2. **Notify human** via email/SMS (optional integration)
3. **Human approves** → Posts immediately
4. **Log after posting** (retroactive logging)

**Template:**

```markdown
---
type: social_post
platform: facebook
action: urgent_announcement
created: 2026-03-17T10:30:00Z
status: pending_approval
priority: P0  # URGENT
---

# URGENT: Facebook Post — Immediate Approval Required

**Reason:** Service outage notification

## Content

```
⚠️ SERVICE ALERT:

We're currently experiencing intermittent connectivity issues. 
Our team is working on a fix.

Expected resolution: 30 minutes

We apologize for the inconvenience.
```

**Approve:** Move to `/Approved/` → Posts immediately
```

---

## Best Practices

### Content Guidelines

1. **Always include context** in approval file
2. **Specify posting time** (immediate vs scheduled)
3. **Include character count** for awareness
4. **List hashtags** separately for easy review
5. **Add safety checklist** before approval

### Approval Workflow

1. **Review daily:** Check `/Pending_Approval/` folder
2. **Set approval windows:** e.g., 9 AM, 2 PM, 6 PM
3. **Use priority levels:**
   - P0: Urgent (approve within 1 hour)
   - P1: High (approve within 4 hours)
   - P2: Normal (approve within 24 hours)
   - P3: Low (approve when convenient)

### Content Calendar

Maintain content calendar in vault:

**Location:** `/Plans/Content_Calendar_2026_Q1.md`

```markdown
# Q1 2026 Social Media Calendar

## March 2026

| Date | Topic | Platform | Status |
|------|-------|----------|--------|
| Mar 17 | Hackathon Demo | All | ✅ Posted |
| Mar 19 | Feature Highlight | FB, LI | ⏳ Pending |
| Mar 21 | Customer Story | FB, IG, LI | 📝 Draft |
| Mar 24 | Weekly Update | All | 📅 Scheduled |
```

---

## Monitoring & Analytics

### Post Performance

After posting, track metrics:

**Location:** `/Logs/Social_Analytics_2026-03.md`

```markdown
# March 2026 Social Analytics

## Facebook Posts

| Date | Post | Reach | Engagement | Clicks |
|------|------|-------|------------|--------|
| Mar 17 | Weekly Update | 1,234 | 56 | 12 |
| Mar 15 | Product Launch | 3,456 | 128 | 45 |
| Mar 12 | Customer Story | 987 | 34 | 8 |

## Insights Retrieved

Use: `claude /facebook-get-insights`
```

### Approval Metrics

Track approval workflow efficiency:

```markdown
# Approval Workflow Metrics

- **Average approval time:** 2.5 hours
- **Approval rate:** 87%
- **Rejection rate:** 8%
- **Edit rate:** 5%
- **Posts pending:** 2
- **Posts approved today:** 5
```

---

## Troubleshooting

### Approval File Not Moving

**Issue:** File stuck in `/Pending_Approval/`

**Solution:**
1. Check HITL scheduler is running
2. Manually run: `python skills/hitl_approval.py --vault ./AI_Employee_Vault`
3. Check file permissions

### Post Failed After Approval

**Issue:** File in `/Approved/` but post not published

**Solution:**
1. Check MCP server status
2. Verify Facebook token is valid
3. Check logs: `/Logs/SocialMCP_*.md`
4. Retry: Move file back to `/Pending_Approval/`

### Duplicate Posts

**Issue:** Same content posted twice

**Solution:**
1. Check deduplication in watcher
2. Review approval file IDs
3. Clear processed IDs if needed

---

## Resources

- [Facebook Integration Guide](./FACEBOOK_INTEGRATION.md)
- [Setup Guide](./FACEBOOK_SETUP_GUIDE.md)
- [HITL Approval Skill](../skills/hitl_approval.py)
- [MCP Social Server](../mcp/social-server/index.js)

---

**Workflow Status:** ✅ Complete and Production-Ready
