# Instagram Poster Skill

## Trigger
Use this skill when the user runs `/instagram-poster` or asks to "post on Instagram", "create Instagram post", or "share on Instagram".

## Purpose
Draft an Instagram post based on business goals and recent vault activity, route it through HITL approval, then publish via the Social MCP server.

## Steps

### 1. Read Context
- Read `AI_Employee_Vault/Business_Goals.md`
- Read `AI_Employee_Vault/Company_Handbook.md`
- Check `AI_Employee_Vault/Done/` for recent activity to highlight

### 2. Draft Instagram Post
- Write engaging caption (max 2200 characters)
- Include relevant hashtags (10-30 hashtags)
- Suggest image description if no image provided
- Format for Instagram best practices (line breaks, emojis if appropriate)

### 3. Create Approval File
Create `AI_Employee_Vault/Pending_Approval/INSTAGRAM_POST_<YYYY-MM-DD>.md`:
```
---
type: instagram_post
status: pending_approval
created: <timestamp>
platform: instagram
---

# Instagram Post — Pending Approval

## Caption
<full caption with hashtags>

## Suggested Image
<description or "No image — text post">

## Action Required
Move this file to /Approved/ to publish, or /Rejected/ to cancel.
```

### 4. Wait for Approval
- Inform user: "Instagram post drafted and waiting in /Pending_Approval/"
- Do NOT publish until file appears in /Approved/

### 5. On Approval (via /hitl-approval)
- Call `social_post_instagram` MCP tool with the caption
- Log result to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`
- Move approval file to `AI_Employee_Vault/Done/`
- Update `AI_Employee_Vault/Dashboard.md`

## Notes
- DRY_RUN=true by default (check .env)
- Instagram requires a Facebook Page linked to a Business account
- Image posts perform better than text-only
- Best posting times: 11am-1pm and 7pm-9pm
