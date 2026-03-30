# API Credentials Setup Guide - Platinum Tier

**Status:** Ready to Configure
**Time Required:** ~20 minutes

---

## Overview

| API | Purpose | Status | Time |
|-----|---------|--------|------|
| Gmail | Email monitoring | ⏳ Pending | 5 min |
| Twitter/X | Social media | ⏳ Pending | 5 min |
| Facebook | Social media | ⏳ Pending | 5 min |
| Instagram | Social media | ⏳ Pending | 5 min |
| LinkedIn | Professional posts | ✅ Already Configured | - |
| Odoo | Accounting/ERP | ⏳ Pending | 5 min |

---

## 1. Gmail API Credentials

### 1.1 Create Google Cloud Project
1. Visit: https://console.cloud.google.com/
2. Click **Create Project**
3. Name: `AI Employee`
4. Click **Create**

### 1.2 Enable Gmail API
1. Go to: **APIs & Services → Library**
2. Search: "Gmail API"
3. Click **Enable**

### 1.3 Create OAuth Credentials
1. Go to: **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Web application**
4. Name: `AI Employee Gmail`
5. Authorized redirect URIs: `http://localhost:8080`
6. Click **Create**

### 1.4 Download Credentials
- Copy **Client ID**
- Copy **Client Secret**
- Download JSON file

### 1.5 Add to .env
```bash
# Gmail/Google Credentials
GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8080
```

### 1.6 Generate Token
```bash
cd D:\fiinal_hackathon_0
python watchers/gmail_watcher.py --auth
```

---

## 2. Twitter/X API Credentials

### 2.1 Apply for Developer Account
1. Visit: https://developer.twitter.com/
2. Click **Apply for a developer account**
3. Choose: **Hobby** (Free tier)
4. Fill in application details
5. Wait for approval (usually instant)

### 2.2 Create App
1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Click **Create Project**
   - Name: `AI Employee`
   - Use case: `Automation`
3. Click **Create App**
   - Name: `AI Employee Twitter`

### 2.3 Get Credentials
1. Go to your App → **Keys and tokens**
2. Copy the following:
   - **API Key** (Consumer Key)
   - **API Key Secret** (Consumer Secret)
   - **Access Token**
   - **Access Token Secret**
   - **Bearer Token**

### 2.4 Add to .env
```bash
# Twitter/X API
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```

---

## 3. Facebook Graph API Credentials

### 3.1 Create Facebook App
1. Visit: https://developers.facebook.com/
2. Click **My Apps → Create App**
3. App type: **Business**
4. Name: `AI Employee`
5. Click **Create App**

### 3.2 Add Instagram Graph API
1. In App Dashboard, scroll to **Add Products**
2. Find **Instagram Graph API** → Click **Set Up**
3. Also add **Pages API**

### 3.3 Generate Access Token
1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app
3. Click **Get Token → Get User Access Token**
4. Select permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_manage_comments`
   - `instagram_manage_insights`
5. Click **Generate Token**
6. Copy **Access Token**

### 3.4 Get Page ID
1. Go to your Facebook Page
2. Click **About**
3. Copy **Page ID**

### 3.5 Get Instagram User ID
1. In Graph API Explorer, run:
   ```
   GET /me?fields=instagram_business_account
   ```
2. Copy the `id` from response

### 3.6 Add to .env
```bash
# Facebook & Instagram
FACEBOOK_ACCESS_TOKEN=your_access_token_here
FACEBOOK_PAGE_ID=your_page_id_here
INSTAGRAM_ACCESS_TOKEN=your_access_token_here
INSTAGRAM_USER_ID=your_instagram_user_id_here
```

---

## 4. LinkedIn API Credentials

### 4.1 Status: Already Configured ✅

Your `.env` file already has LinkedIn credentials:
```bash
LINKEDIN_CLIENT_ID=863hhmvy7of6t7
LINKEDIN_CLIENT_SECRET=WPL_AP1.kRlwH2Z15BwAs1eI.q0gADQ==
LINKEDIN_ACCESS_TOKEN=AQWDHe_R2GQ1v649VZfu8I2DGm9qaTGyeQ7Nf4bMeaY2twpmPPdX9uPa0wgCDSUpcwgHp2VGJNYBzUBKjS4NpWzxFpW-A3_V8tXHUpUNMeamXD9S88kPdVGmZY03Q8ihtdrNcaaWafREH7FBarpvZuBFa-hN-WSOYw0zFGEZ9EdPKxz1fUOAZ4x-ljGx30SFqfjjGx30SFqfjj...
```

### 4.2 Test LinkedIn
```bash
python watchers/linkedin_watcher.py --status
```

---

## 5. Odoo ERP Credentials

### 5.1 Local Odoo (Docker)
```bash
# Start Odoo locally
cd D:\fiinal_hackathon_0
docker-compose up -d odoo db
```

### 5.2 Access Odoo
1. Visit: http://localhost:8069
2. Default credentials:
   - **Email:** admin
   - **Password:** admin

### 5.3 Add to .env
```bash
# Odoo ERP
ODOO_URL=http://localhost:8069
ODOO_DB=postgres
ODOO_USER=admin
ODOO_PASSWORD=admin
```

### 5.4 Test Odoo Connection
```bash
python odoo/setup_odoo.py --status
```

---

## 6. WhatsApp Session (Local Only)

### 6.1 WhatsApp Web Setup
```bash
# Create session directory
mkdir -p whatsapp_session

# Run WhatsApp watcher (will prompt for QR scan)
python watchers/whatsapp_watcher.py --auth
```

### 6.2 Scan QR Code
1. Terminal will show QR code
2. Open WhatsApp on phone
3. Go to: Settings → Linked Devices
4. Scan QR code
5. Session saved to `whatsapp_session/`

### 6.3 Configure in .env
```bash
# WhatsApp (Local Only - NEVER sync to cloud)
WHATSAPP_SESSION_PATH=./whatsapp_session
```

---

## Verification Checklist

### Test All Credentials

```bash
# Gmail
python watchers/gmail_watcher.py --status

# Twitter
python watchers/twitter_watcher.py --status

# Facebook
python watchers/facebook_watcher.py --status

# LinkedIn
python watchers/linkedin_watcher.py --status

# Odoo
python odoo/setup_odoo.py --status
```

### Expected Output
```
✅ Gmail: Connected
✅ Twitter: Connected
✅ Facebook: Connected
✅ LinkedIn: Connected
✅ Odoo: Connected
```

---

## Security Best Practices

### ✅ DO:
- Store credentials in `.env` only
- Keep `.env` in `.gitignore`
- Use strong passwords
- Rotate credentials monthly
- Use 2FA where available

### ❌ DON'T:
- Never commit `.env` to Git
- Never share credentials publicly
- Never store in plain text outside `.env`
- Never use same password everywhere

---

## Credential Storage

### Local Machine (.env)
```bash
# All credentials
cp .env.example .env
nano .env  # Fill in all values
```

### Cloud VM (.env)
```bash
# SSH into VM
ssh ubuntu@<vm-ip>

# Edit .env
cd /home/ubuntu/ai-employee
nano .env

# Secure permissions
chmod 600 .env
```

### Backup Credentials
```bash
# Encrypt and backup (optional)
tar -czf credentials_backup.tar.gz .env
openssl enc -aes-256-cbc -salt -in credentials_backup.tar.gz -out credentials_backup.enc
```

---

## Troubleshooting

### Gmail: "Invalid Credentials"
```bash
# Re-generate token
python watchers/gmail_watcher.py --auth --force
```

### Twitter: "Rate Limit Exceeded"
```bash
# Wait 15 minutes
# Twitter has strict rate limits
# Check: https://developer.twitter.com/en/portal/dashboard
```

### Facebook: "Token Expired"
```bash
# Generate new long-lived token
# Tokens expire after 60 days
# Set calendar reminder to refresh
```

### Odoo: "Connection Refused"
```bash
# Check if Odoo is running
docker-compose ps

# Start Odoo
docker-compose up -d odoo db
```

---

## Quick Reference

| Service | Documentation | Dashboard |
|---------|---------------|-----------|
| Gmail | https://developers.google.com/gmail/api | https://console.cloud.google.com |
| Twitter | https://developer.twitter.com/en/docs | https://developer.twitter.com/en/portal/dashboard |
| Facebook | https://developers.facebook.com/docs/graph-api | https://developers.facebook.com/apps |
| LinkedIn | https://learn.microsoft.com/en-us/linkedin/ | https://www.linkedin.com/developers/apps |
| Odoo | https://www.odoo.com/documentation | http://localhost:8069 |

---

## Next Steps

After configuring all credentials:

1. ✅ **Test each integration individually**
2. ✅ **Run full demo flow**
3. ✅ **Monitor for 24 hours**
4. ✅ **Set up credential rotation reminders**

---

**Credentials Setup Complete!** 🎉

*All API integrations ready for Platinum Tier*
