# Facebook Token Setup — Quick Guide

**Your App ID:** `1383922417086696`  
**Status:** Ready to generate tokens

---

## 🚀 Quick Setup (Automated)

Run the token generator script:

```bash
python watchers/generate_facebook_token.py
```

This will:
1. Open Facebook OAuth dialog in your browser
2. Guide you through permissions
3. Automatically exchange for long-lived tokens
4. Update your `.env` file
5. Test the connection

---

## 📋 Manual Setup (Step-by-Step)

### Step 1: Get User Access Token

1. **Go to Graph API Explorer:**
   https://developers.facebook.com/tools/explorer/?client_id=1383922417086696

2. **Select your app:** `1383922417086696`

3. **Click "Get Token" → "Get User Token"**

4. **Select these permissions:**
   - ✅ `pages_manage_posts`
   - ✅ `pages_read_engagement`
   - ✅ `pages_read_user_content`
   - ✅ `pages_manage_metadata`
   - ✅ `instagram_basic`
   - ✅ `instagram_manage_comments`
   - ✅ `instagram_manage_insights`

5. **Click "Generate Access Token"**

6. **Log in to Facebook and approve**

7. **Copy the access token** (starts with `EAAc...`)

---

### Step 2: Get Page Access Token

1. **In Graph API Explorer, run:**
   ```
   GET /me/accounts?access_token=YOUR_USER_TOKEN
   ```

2. **Copy your Page's access token** from the response

3. **Copy your Page ID** from the response

---

### Step 3: Get Instagram User ID

1. **In Graph API Explorer, run:**
   ```
   GET /YOUR_PAGE_ID?fields=instagram_business_account&access_token=YOUR_PAGE_TOKEN
   ```

2. **Copy the Instagram User ID** from the response

---

### Step 4: Update .env File

Open `.env` and add:

```bash
# Facebook & Instagram
FACEBOOK_APP_ID=1383922417086696
FACEBOOK_APP_SECRET=22d4377e9ea0963e8eba3123dc3f4647
FACEBOOK_ACCESS_TOKEN=EAAc...your_page_token_here
FACEBOOK_PAGE_ID=123456789012345
INSTAGRAM_ACCESS_TOKEN=EAAc...same_as_facebook_token
INSTAGRAM_USER_ID=17841400000000000
```

---

## ✅ Test Your Configuration

```bash
# Test connection
python watchers/test_facebook.py

# Run full integration test
python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault

# Start monitoring
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch
```

---

## 🔗 Useful Links

- **Graph API Explorer:** https://developers.facebook.com/tools/explorer/?client_id=1383922417086696
- **Your App Dashboard:** https://developers.facebook.com/apps/1383922417086696/
- **Access Token Debugger:** https://developers.facebook.com/tools/debug/access_token/

---

## ⚠️ Important Notes

1. **Token Expiry:**
   - Short-lived tokens: ~1 hour
   - Long-lived tokens: ~60 days
   - Page tokens: Don't expire (if from long-lived user token)

2. **Token Refresh:**
   Run the generator script again before tokens expire:
   ```bash
   python watchers/generate_facebook_token.py
   ```

3. **Instagram Requirements:**
   - Must be Instagram Business Account
   - Must be connected to Facebook Page
   - Go to: Facebook Page → Settings → Instagram → Connect

---

## 🆘 Troubleshooting

### "Invalid App ID"
- Make sure your App is in **Live** mode (not Development)
- Go to: App Dashboard → Settings → Basic → App Mode → Live

### "Permissions Denied"
- Make sure you granted all required permissions
- Some permissions need App Review by Facebook

### "No Instagram Account Found"
- Convert Instagram to Business Account
- Connect it to your Facebook Page
- Run: `GET /{page-id}?fields=instagram_business_account`

### "Token Expired"
- Run the token generator script again
- Tokens expire after ~60 days

---

## 📞 Need Help?

```bash
# Run automated setup
python watchers/generate_facebook_token.py

# Test connection
python watchers/test_facebook.py

# Check status
python watchers/facebook_watcher.py --status
```

---

**Last Updated:** March 17, 2026  
**App ID:** 1383922417086696  
**Status:** ✅ Ready for Configuration
