# Twitter Poster Skill

## Trigger
Use this skill when the user runs `/twitter-poster` or asks to "post a tweet", "tweet about", "post on Twitter/X", or "schedule a Twitter post".

## Purpose
Draft and publish Twitter/X posts for business development and thought leadership.

## Steps

### 1. Read Context
- Read `AI_Employee_Vault/Company_Handbook.md` for tone guidelines
- Read `AI_Employee_Vault/Dashboard.md` for recent activity context
- Read `AI_Employee_Vault/Business_Goals.md` if it exists

### 2. Draft Tweet
Based on the context and user request, draft a tweet that:
- Is under 280 characters
- Matches the professional, warm, direct tone from the Handbook
- Includes relevant hashtags (2-3 max)
- Has a clear value proposition or insight
- Optionally includes a call to action

### 3. Create Approval File
Create `AI_Employee_Vault/Pending_Approval/APPROVAL_TWITTER_POST_<date>_<ts>.md`:

```markdown
---
type: twitter_post
platform: twitter
created: <ISO timestamp>
status: pending_approval
---

# Twitter Post — Awaiting Approval

## Draft Tweet

> <tweet content>

**Character count:** <n>/280

## Hashtags
<hashtags>

## Rationale
<why this tweet, what goal it serves>

## Instructions
- Move to /Approved/ to publish
- Move to /Rejected/ to cancel
- Edit content above if changes needed, then approve
```

### 4. If Previously Approved (from /Approved/)
- Call `social_post_tweet` with the approved content
- Move approval file to `Done/`
- Log: `- [timestamp] Tweet posted — "<first 50 chars>"`
- Update Dashboard.md

### 5. Report to User
- Show the draft tweet
- Confirm approval file location
- Remind user to move to /Approved/ to publish

## Notes
- DRY_RUN=true by default — tweets won't post until credentials are set and DRY_RUN=false
- For Twitter credentials: run `python watchers/twitter_watcher.py --auth`
- All tweets require approval regardless of content
