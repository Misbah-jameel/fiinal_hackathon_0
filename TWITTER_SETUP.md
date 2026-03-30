# Twitter/X Gold Tier Setup Guide

## Overview
Twitter/X integration allows your AI Employee to:
- ✅ Monitor mentions (@username)
- ✅ Read Direct Messages (DMs)
- ✅ Post tweets (with approval)
- ✅ Create action files for engagement opportunities

## Prerequisites
- Twitter Developer Account (https://developer.twitter.com/)
- Twitter App with Read + Write permissions
- Python 3.8+

## Credentials Setup

### 1. Get Your Twitter Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Select your project/app
3. Go to **Keys and Tokens** section
4. Generate/copy these credentials:
   - API Key (Consumer Key)
   - API Secret (Consumer Secret)
   - Access Token
   - Access Token Secret
   - Bearer Token

### 2. Add to .env File

Your `.env` file should have:

```env
# ------------------------------------------------------------------
# Twitter/X  (Gold Tier)
# ------------------------------------------------------------------
TWITTER_CONSUMER_KEY=your_consumer_key_here
TWITTER_CONSUMER_SECRET=your_consumer_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Testing Twitter Integration

### Test Connection

```bash
python watchers/twitter_poster.py --vault ./AI_Employee_Vault --test
```

Expected output:
```
✓ Twitter connection successful!
```

### Run Twitter Watcher (Single Check)

```bash
python watchers/twitter_watcher.py --vault ./AI_Employee_Vault --once
```

### Run Twitter Watcher (Continuous)

```bash
python watchers/twitter_watcher.py --vault ./AI_Employee_Vault --watch
```

### Post a Tweet

1. Create tweet file in `/Approved/` directory
2. Run:

```bash
python watchers/twitter_poster.py --vault ./AI_Employee_Vault --post ./AI_Employee_Vault/Approved/TWITTER_tweet_2026-03-26.md
```

## File Structure

```
AI_Employee_Vault/
├── Needs_Action/          # Twitter mentions/DMs create action files here
│   └── TWITTER_MENTION_12345_20260326.md
├── Approved/              # Approved tweets ready to post
│   └── TWITTER_tweet_2026-03-26.md
├── Done/                  # Posted tweets moved here
│   └── TWITTER_tweet_2026-03-26.md
└── Logs/
    ├── twitter_processed.json    # Track processed tweets/DMs
    └── YYYY-MM-DD.md             # Daily activity logs
```

## Action File Format

When Twitter watcher detects mentions or DMs, it creates files like:

```markdown
---
type: twitter_mention
tweet_id: 1234567890
from: @username
received: 2026-03-26T10:30:00
priority: P3
status: pending
---

# Twitter Mention — Action Required

**Type:** Mention
**ID:** 1234567890
**From:** @username
**Time:** 2026-03-26T10:30:00

## Content

> Hey @YourCompany, love your product!

## Suggested Actions

1. Review tweet/DM content
2. Draft reply if needed → place in /Pending_Approval
3. If spam/irrelevant → mark as done
```

## Posting Tweets

Approved tweet format:

```markdown
---
type: twitter_post
created: 2026-03-26
priority: P2
status: approved
---

# Twitter Post

**Content:** (280 characters max)

---

Excited to announce our new AI Employee Gold Tier! 🚀

Autonomous social media management powered by Claude + Twitter API.

#AI #Automation #GoldTier

---

## Approval

- Approved by: Human Manager
- Date: 2026-03-26
- Notes: Ready to post
```

## PM2 Setup (Production)

To run Twitter watcher as a background service:

```bash
# Install PM2 globally
npm install -g pm2

# Start Twitter watcher
pm2 start watchers/twitter_watcher.py --name twitter-watcher --interpreter python3 -- --vault ./AI_Employee_Vault --watch

# Save PM2 configuration
pm2 save

# View logs
pm2 logs twitter-watcher
```

## Troubleshooting

### "Twitter client not initialized"
- Check that all 5 credentials are in `.env`
- Verify credentials are correct (no extra spaces)
- Test with `--test` flag

### "tweepy not installed"
```bash
pip install tweepy
```

### "Rate limit exceeded"
- Twitter API has rate limits
- Watcher automatically waits when limits are hit
- Consider upgrading to Elevated access for higher limits

### DMs not being fetched
- DM access requires Elevated API access
- Apply at https://developer.twitter.com/en/portal/products

## API Limits

| Access Level | Tweets/Day | DMs/Day |
|--------------|-----------|---------|
| Free         | 50        | N/A     |
| Basic ($100) | 10,000    | 1,000   |
| Pro ($5,000) | 1M        | 10,000  |

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` to git
- Keep `twitter_processed.json` out of version control
- Rotate credentials every 90 days
- Use DRY_RUN=true for testing

## Next Steps

1. ✅ Test Twitter connection
2. ✅ Run watcher in watch mode
3. ✅ Create first test tweet
4. ✅ Monitor Needs_Action queue
5. ✅ Set up PM2 for production

---

**Status:** ✅ Gold Tier Complete
**Last Updated:** 2026-03-26
