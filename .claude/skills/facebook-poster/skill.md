# Facebook & Instagram Poster Skill

## Trigger
Use this skill when the user runs `/facebook-poster` or asks to "post on Facebook", "post on Instagram", "share on Facebook/Instagram", or "create a social post".

## Purpose
Draft and publish posts to Facebook Page and/or Instagram Business Account.

## Steps

### 1. Read Context
- Read `AI_Employee_Vault/Company_Handbook.md` for tone guidelines
- Read `AI_Employee_Vault/Dashboard.md` for recent activity
- Read `AI_Employee_Vault/Business_Goals.md` if it exists

### 2. Determine Platform
Based on request:
- "Facebook" → Facebook Page only
- "Instagram" → Instagram only (requires image URL)
- "both" or unspecified → both platforms

### 3. Draft Post Content
- **Facebook:** Text post, up to 500 words, professional yet engaging
- **Instagram:** Caption + image URL required, concise caption with hashtags (5-10)
- Match tone from Company Handbook: professional, warm, direct

### 4. Create Approval File
Create `AI_Employee_Vault/Pending_Approval/APPROVAL_<PLATFORM>_POST_<date>_<ts>.md`:

```markdown
---
type: social_post
platform: <facebook|instagram|both>
created: <ISO timestamp>
status: pending_approval
---

# <Platform> Post — Awaiting Approval

## Post Content

> <content>

**Platform:** <platform>
**Image URL:** <if Instagram>

## Rationale
<why this post, what goal it serves>

## Instructions
- Move to /Approved/ to publish
- Move to /Rejected/ to cancel
```

### 5. If Previously Approved (from /Approved/)
- For Facebook: call `social_post_facebook`
- For Instagram: call `social_post_instagram`
- For both: call `social_post_all`
- Move approval file to Done/
- Log action
- Update Dashboard.md

### 6. Report to User
- Show draft content
- Confirm approval file location

## Notes
- Facebook credentials: FACEBOOK_ACCESS_TOKEN + FACEBOOK_PAGE_ID in .env
- Instagram credentials: INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_USER_ID in .env
- Setup guide: `python watchers/facebook_watcher.py --auth`
- Instagram always requires an image URL — text-only posts not supported by API
