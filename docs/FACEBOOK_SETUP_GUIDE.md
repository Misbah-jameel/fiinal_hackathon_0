# Facebook & Instagram Integration Setup Guide

**Gold Tier — AI Employee Hackathon 0**

This guide walks you through setting up Facebook Page and Instagram Business account integration for your AI Employee.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Facebook App Setup](#1-facebook-app-setup)
3. [Instagram Business Setup](#2-instagram-business-setup)
4. [Generate Access Tokens](#3-generate-access-tokens)
5. [Configure .env File](#4-configure-env-file)
6. [Test Connection](#5-test-connection)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Facebook Page (you must be an admin)
- Instagram Business Account (connected to your Facebook Page)
- Facebook Developer Account
- Python 3.13+ with `requests` package installed

---

## 1. Facebook App Setup

### Step 1.1: Create Facebook Developer Account

1. Go to [https://developers.facebook.com/](https://developers.facebook.com/)
2. Click **Get Started** or **Log In**
3. Accept the terms and complete your developer profile

### Step 1.2: Create a New App

1. Click **My Apps** → **Create App**
2. Select **Business** as the app type
3. Fill in:
   - **App Name**: `AI Employee Social Integration`
   - **App Contact Email**: your email
   - **Business Account**: Select or create a business account
4. Click **Create App**

### Step 1.3: Add Pages API

1. In your App Dashboard, scroll to **Add Products to Your App**
2. Find **Pages** and click **Set Up**
3. This enables Facebook Page access

### Step 1.4: Configure App Settings

1. Go to **Settings** → **Basic**
2. Note your **App ID** and **App Secret** (you'll need these)
3. Add your app domain (optional for local development)
4. Set **App Mode** to **Live** (required for production use)

---

## 2. Instagram Business Setup

### Step 2.1: Convert Instagram to Business Account

1. Open Instagram app → Go to your profile
2. Tap **Settings** → **Account**
3. Select **Switch to Professional Account**
4. Choose **Business** (not Creator)
5. Connect to your Facebook Page

### Step 2.2: Add Instagram Graph API

1. In your Facebook App Dashboard
2. Go to **Add Products to Your App**
3. Find **Instagram Graph API** and click **Set Up**
4. This enables Instagram data access

### Step 2.3: Configure Instagram Basic Display (Optional)

For additional features, also add:
- **Instagram Basic Display** → **Set Up**
- Configure OAuth redirect URI: `https://localhost`

---

## 3. Generate Access Tokens

### Method A: Using Graph API Explorer (Recommended for Testing)

#### Step 3.1: Get Page Access Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Click **Get Token** → **Get Page Access Token**
4. Select your Page
5. Add permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_read_user_content`
   - `pages_manage_metadata`
6. Click **Generate Access Token**
7. Copy the token → This is your `FACEBOOK_ACCESS_TOKEN`

#### Step 3.2: Get Page ID

1. Go to your Facebook Page
2. Click **About** → **Page Info**
3. Find **Page ID** (or use Graph API: `https://graph.facebook.com/v19.0/me?fields=id,name&access_token=YOUR_TOKEN`)
4. Copy → This is your `FACEBOOK_PAGE_ID`

#### Step 3.3: Get Instagram User ID

1. In Graph API Explorer, run:
   ```
   GET /{your-page-id}?fields=instagram_business_account&access_token={your-page-token}
   ```
2. Copy the `id` from `instagram_business_account` → This is your `INSTAGRAM_USER_ID`

#### Step 3.4: Get Instagram Access Token

Use the same Page Access Token for Instagram (they share the same token when accounts are linked).

Copy → This is your `INSTAGRAM_ACCESS_TOKEN`

### Method B: Generate Long-Lived Token (Production)

Page tokens from Method A expire in ~60 days. For a long-lived token:

1. Exchange short-lived token for long-lived:
   ```bash
   curl -G "https://graph.facebook.com/v19.0/oauth/access_token" \
     -d "grant_type=fb_exchange_token" \
     -d "client_id={app-id}" \
     -d "client_secret={app-secret}" \
     -d "fb_exchange_token={short-lived-token}"
   ```

2. The response contains your long-lived token (valid ~60 days)

**Note:** For truly permanent tokens, you need app review by Facebook. For hackathon purposes, 60-day tokens are sufficient.

---

## 4. Configure .env File

Open your `.env` file and add:

```bash
# ------------------------------------------------------------------
# Facebook & Instagram  (Gold Tier)
# ------------------------------------------------------------------
FACEBOOK_ACCESS_TOKEN=EAAc...your_long_token_here
FACEBOOK_PAGE_ID=123456789012345
INSTAGRAM_ACCESS_TOKEN=EAAc...same_token_as_facebook
INSTAGRAM_USER_ID=17841400000000000
```

**Important:**
- Never commit `.env` to git
- Keep tokens secure
- Tokens expire after ~60 days (set a reminder to refresh)

---

## 5. Test Connection

### Step 5.1: Install Dependencies

```bash
pip install requests python-dotenv
```

### Step 5.2: Run Test Script

```bash
python watchers/test_facebook.py
```

**Expected Output:**
```
==================================================
  Facebook/Instagram Credential Test
==================================================

── Facebook ──────────────────────────────
✅ Page: Your Page Name
   Fans: 1234
   Talking about: 56

── Instagram ─────────────────────────────
✅ Instagram: @your_username
   Followers: 5678
   Posts: 123

── Summary ───────────────────────────────
   Facebook: ✅ Ready
   Instagram: ✅ Ready

✅ All credentials valid! Start watcher:
   python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch
```

### Step 5.3: Start the Watcher

```bash
# Test run (check once)
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault

# Continuous monitoring (runs every 5 minutes)
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch

# Check status
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --status
```

---

## 6. Verify Integration

### Check Action Files

After running the watcher, check:

```
AI_Employee_Vault/
└── Needs_Action/
    ├── FACEBOOK_COMMENT_abc123_20260317_143022.md
    └── INSTAGRAM_COMMENT_xyz789_20260317_143045.md
```

### Test Posting (Dry Run)

```bash
# Configure MCP server in Claude Code
# Then test posting (DRY_RUN=true by default)
claude /social_post_facebook --message "Test post from AI Employee"
```

Check `AI_Employee_Vault/Pending_Approval/` for approval file.

---

## Troubleshooting

### Error: "Authentication failed"

**Cause:** Invalid or expired access token

**Solution:**
1. Regenerate token using Graph API Explorer
2. Update `.env` with new token
3. Restart watcher

### Error: "Permission denied"

**Cause:** Missing permissions on token

**Solution:**
1. Regenerate token with all required permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_read_user_content`
   - `instagram_basic`
   - `instagram_manage_comments`
2. Make sure your app is in **Live** mode

### Error: "No Instagram Business Account linked"

**Cause:** Instagram account not connected to Facebook Page

**Solution:**
1. Go to Facebook Page → Settings → Instagram
2. Click **Connect Account**
3. Log in to Instagram and authorize
4. Run: `python watchers/test_facebook.py --get-ig-id`

### Error: "Rate limit exceeded"

**Cause:** Too many API calls

**Solution:**
- Watcher automatically handles rate limiting with exponential backoff
- Wait 1 hour for rate limit to reset
- Reduce check frequency if needed (edit `check_interval` in watcher)

### Error: "Graph API version deprecated"

**Cause:** Using outdated API version

**Solution:**
- Update `GRAPH_API` constant in `facebook_watcher.py` to latest version
- Current: `https://graph.facebook.com/v19.0`

---

## API Reference

### Facebook Graph API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /{page-id}/feed` | Get page posts |
| `GET /{page-id}/comments` | Get post comments |
| `GET /{page-id}/conversations` | Get Messenger messages |
| `POST /{page-id}/feed` | Create page post |
| `GET /{page-id}` | Get page info |

### Instagram Graph API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /{ig-user-id}/media` | Get user's posts |
| `GET /{media-id}/comments` | Get media comments |
| `GET /{ig-user-id}/tags` | Get tagged mentions |
| `POST /{ig-user-id}/media` | Create media |
| `POST /{ig-user-id}/media_publish` | Publish media |
| `GET /{ig-user-id}` | Get account info |

---

## Security Best Practices

1. **Never commit tokens** to version control
2. **Use environment variables** (`.env` file)
3. **Rotate tokens regularly** (every 60 days)
4. **Limit permissions** to only what's needed
5. **Monitor API usage** in Facebook Developer Dashboard
6. **Use DRY_RUN=true** until ready for production

---

## Next Steps

After setup is complete:

1. ✅ Test watcher: `python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch`
2. ✅ Test posting: `claude /social_post_facebook --message "Hello from AI Employee!"`
3. ✅ Configure MCP server in Claude Code settings
4. ✅ Run full demo: `python demo_flow.py --vault ./AI_Employee_Vault`

---

## Resources

- [Facebook Graph API Docs](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API Docs](https://developers.facebook.com/docs/instagram-api)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [Pages API Reference](https://developers.facebook.com/docs/pages/api)
- [Access Token Documentation](https://developers.facebook.com/docs/facebook-login/access-tokens)

---

**Need Help?**

Run the auth guide:
```bash
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --auth
```

Or check the troubleshooting section above.
