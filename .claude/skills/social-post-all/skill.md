# Social Post All Skill

## Trigger
Use this skill when the user runs `/social-post-all` or asks to "cross-post", "post everywhere", "post on all platforms", or "social blast".

## Purpose
Draft a single message adapted for all social platforms (LinkedIn, Twitter/X, Facebook, Instagram), route through HITL approval, then publish everywhere simultaneously via Social MCP.

## Steps

### 1. Read Context
- Read `AI_Employee_Vault/Business_Goals.md`
- Read `AI_Employee_Vault/Company_Handbook.md`
- Identify the topic/message to share

### 2. Draft Platform-Specific Versions
Adapt the core message for each platform's format and audience:

| Platform | Max Length | Style |
|----------|-----------|-------|
| LinkedIn | 3000 chars | Professional, detailed |
| Twitter/X | 280 chars | Punchy, hashtags |
| Facebook | 63206 chars | Conversational |
| Instagram | 2200 chars | Visual storytelling + hashtags |

### 3. Create Approval File
Create `AI_Employee_Vault/Pending_Approval/SOCIAL_ALL_<YYYY-MM-DD>.md`:
```
---
type: social_post_all
status: pending_approval
created: <timestamp>
platforms: [linkedin, twitter, facebook, instagram]
---

# Cross-Platform Post — Pending Approval

## LinkedIn Version
<linkedin text>

## Twitter/X Version
<tweet text>

## Facebook Version
<facebook text>

## Instagram Version
<instagram caption + hashtags>

## Action Required
Move to /Approved/ to publish on ALL platforms, or /Rejected/ to cancel.
```

### 4. Wait for Approval
- Inform user the cross-post is drafted and in /Pending_Approval/
- Do NOT publish until approved

### 5. On Approval (via /hitl-approval)
- Call `social_post_all` MCP tool with all platform versions
- Log each result to `AI_Employee_Vault/Logs/<YYYY-MM-DD>.md`
- Move approval file to `AI_Employee_Vault/Done/`
- Update `AI_Employee_Vault/Dashboard.md`

## Notes
- DRY_RUN=true by default (check .env to enable real posting)
- All 4 platforms must have valid credentials configured in .env
- Failed platforms are logged but don't block successful ones
