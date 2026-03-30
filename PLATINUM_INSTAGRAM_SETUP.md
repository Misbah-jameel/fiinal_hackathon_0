# Instagram Integration Setup — Platinum Tier

## Overview
Instagram integration is **already built** into the codebase! You just need to configure the credentials.

---

## Step 1: Get Instagram Business Account

### Requirements:
1. **Instagram Business Account** (convert from personal if needed)
2. **Facebook Page** linked to your Instagram
3. **Facebook Developer Account**

### Convert to Business Account:
1. Open Instagram → Settings → Account
2. Tap "Switch to Professional Account"
3. Select "Business" (not Creator)
4. Connect to a Facebook Page (create one if you don't have)

---

## Step 2: Create Facebook App

### 2.1 Go to Facebook Developers
1. Visit: https://developers.facebook.com/
2. Click "My Apps" → "Create App"
3. Select **"Business"** as app type
4. Fill in:
   - App Name: `AI Employee Platinum`
   - App Contact Email: your email
   - Business Account: select or create

### 2.2 Add Instagram Graph API
1. In your App Dashboard, scroll to "Add Products"
2. Find **"Instagram Graph API"** → Click "Set Up"
3. Also add **"Pages API"** (required for Instagram)

### 2.3 Generate Access Token

#### Option A: Using Graph API Explorer (Easiest)
1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app from dropdown
3. Click "Get Token" → "Get User Access Token"
4. Select permissions:
   - `instagram_basic`
   - `instagram_manage_comments`
   - `instagram_manage_insights`
   - `pages_show_list`
   - `pages_read_engagement`
5. Click "Generate Token"
6. Copy the **Access Token**

#### Option B: Using Access Token Tool
1. Go to: https://developers.facebook.com/tools/accesstoken/
2. Select your app
3. Click "Get Token" → "Get Long-Lived User Access Token"
4. Copy the token (valid for 60 days)

### 2.4 Get Instagram User ID
1. Go to Graph API Explorer
2. Run this query:
   ```
   GET /me?fields=instagram_business_account
   ```
3. Copy the `id` from response → This is your **Instagram User ID**

### 2.5 Get Facebook Page ID
1. Go to your Facebook Page
2. Click "About" → Scroll to "Page ID"
3. OR use Graph API Explorer:
   ```
   GET /me/accounts
   ```
4. Copy the `id` of your page

---

## Step 3: Configure .env File

Open `.env` and update these values:

```bash
# Facebook & Instagram (Gold Tier)
FACEBOOK_ACCESS_TOKEN=EAAxxxx...your_long_token_here...
FACEBOOK_PAGE_ID=123456789012345
INSTAGRAM_ACCESS_TOKEN=EAAxxxx...same_token_or_separate...
INSTAGRAM_USER_ID=17841400000000000
```

**Important Notes:**
- Token must be **long-lived** (60 days, not 1-hour)
- Never commit `.env` to git
- Token expires → set calendar reminder to refresh

---

## Step 4: Test Instagram Integration

### Test 1: Verify Credentials
```bash
cd D:\fiinal_hackathon_0
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --platform instagram
```

Expected output:
```
[INFO] Instagram Watcher started (interval: 5 min)
[INFO] Connected to Instagram Business Account: your_username
```

### Test 2: Check Instagram Comments
```bash
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --platform instagram --test
```

### Test 3: Manual Trigger
1. Post something on Instagram
2. Add a comment to your post
3. Wait 5 minutes (or restart watcher)
4. Check `AI_Employee_Vault/Needs_Action/` for new action file

---

## Step 5: Instagram Features Available

### What the Watcher Monitors:
| Feature | Description | Interval |
|---------|-------------|----------|
| **Comments** | New comments on your posts | 5 min |
| **Mentions** | When someone mentions you | 5 min |
| **DMs** | Direct messages (via Messenger) | 5 min |
| **Followers** | New followers (basic count) | 15 min |

### Action Files Created:
```
AI_Employee_Vault/Needs_Action/
├── INSTAGRAM_comment_12345_20260313_220000.md
├── INSTAGRAM_mention_67890_20260313_220500.md
└── INSTAGRAM_dm_11111_20260313_221000.md
```

### Sample Action File:
```markdown
---
type: instagram_comment
post_id: "17895123456789012"
from: @username
received: 2026-03-13T22:00:00
priority: P3
status: pending
---

# Instagram Comment — Action Required

**Type:** Comment
**From:** @username
**Time:** 2026-03-13 22:00

## Content

> Great product! How much does it cost?

## Suggested Actions

1. Draft a friendly reply
2. Include pricing information
3. Place in /Pending_Approval before posting
```

---

## Step 6: Instagram Posting (Social MCP)

### Post to Instagram via Claude Code:

```bash
claude /instagram-poster
```

**Workflow:**
1. Claude generates post content
2. Creates approval file in `/Pending_Approval/`
3. You approve by moving to `/Approved/`
4. HITL executes via Instagram Graph API
5. Logs action and moves to `/Done/`

### Supported Post Types:
- ✅ Image posts (with caption)
- ✅ Carousel posts (multiple images)
- ✅ Stories (via API)
- ❌ Reels (API limitation)

---

## Step 7: Cross-Post Feature

Post to **all platforms** at once:

```bash
claude /social-post-all
```

This will:
1. Generate content
2. Create approval files for:
   - Twitter/X
   - Facebook
   - Instagram
   - LinkedIn
3. Execute after approval

---

## Troubleshooting

### Error: "Invalid Access Token"
**Solution:** Token expired or wrong permissions
- Generate new long-lived token
- Ensure `instagram_basic` permission is selected

### Error: "Page Not Connected"
**Solution:** Instagram not linked to Facebook Page
- Go to Instagram Settings → Account → Linked Accounts
- Connect to your Facebook Page

### Error: "Business Account Required"
**Solution:** Account type is Personal/Creator
- Convert to Business Account in Instagram Settings

### Watcher Not Picking Up Comments
**Solution:** Check logs
```bash
pm2 logs facebook-watcher
```

---

## Next Steps: Platinum Deployment

Once Instagram is working:

1. ✅ Instagram integration complete
2. ⏭️ Deploy to Cloud VM (Oracle/AWS)
3. ⏭️ Setup Cloud vs Local work zones
4. ⏭️ Configure Vault Sync via Git
5. ⏭️ Implement Claim-by-move rules

---

## Quick Reference

### Get Credentials:
- Facebook Developers: https://developers.facebook.com/
- Graph API Explorer: https://developers.facebook.com/tools/explorer/
- Access Token Tool: https://developers.facebook.com/tools/accesstoken/

### Required Permissions:
- `instagram_basic`
- `instagram_manage_comments`
- `instagram_manage_insights`
- `pages_show_list`
- `pages_read_engagement`

### API Endpoints:
- Base URL: `https://graph.facebook.com/v19.0/`
- Instagram User: `GET /{ig-user-id}?fields=media`
- Media Comments: `GET /{media-id}/comments`

---

**Status:** Instagram code is **ready** — just add credentials to `.env`!
