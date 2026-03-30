# Facebook Integration — Gold Tier Documentation

**AI Employee Hackathon 0**

This document provides comprehensive documentation for the Facebook & Instagram integration in your AI Employee system.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Setup Guide](#setup-guide)
5. [Available Skills](#available-skills)
6. [MCP Tools](#mcp-tools)
7. [Watcher Configuration](#watcher-configuration)
8. [Workflows](#workflows)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Overview

The Facebook integration enables your AI Employee to:

- **Monitor** Facebook Page comments, posts, and Messenger messages
- **Monitor** Instagram Business comments and mentions
- **Post** updates to Facebook Page (with human approval)
- **Post** images to Instagram (with human approval)
- **Retrieve** analytics and insights
- **Manage** posts (delete, edit via approval workflow)

All actions follow the **Human-in-the-Loop (HITL)** pattern — nothing posts without your approval.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 EXTERNAL PLATFORMS                          │
├────────────────────────┬────────────────────────────────────┤
│   Facebook Page        │   Instagram Business               │
│   - Comments           │   - Comments                       │
│   - Messages (Messenger)│  - Mentions                       │
│   - Posts              │   - Media                          │
│   - Insights           │                                    │
└───────────┬────────────┴──────────────┬─────────────────────┘
            │                           │
            ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│              FACEBOOK WATCHER (Python)                      │
│  - Polls Graph API every 5 minutes                          │
│  - Creates action files in /Needs_Action                    │
│  - Tracks processed items (deduplication)                   │
│  - Error handling with circuit breaker                      │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│              OBSIDIAN VAULT (Local Memory)                  │
│  /Needs_Action/    ← New social interactions                │
│  /Plans/           ← Claude-generated response plans        │
│  /Pending_Approval/ ← Draft replies awaiting approval       │
│  /Approved/        ← Ready to execute                       │
│  /Done/            ← Completed actions                      │
│  /Logs/            ← Activity logs                          │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│           CLAUDE CODE (Reasoning Engine)                    │
│  - Reads action files                                       │
│  - Creates response plans                                   │
│  - Routes to approval workflow                              │
│  - Uses MCP tools for posting                               │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│           MCP SOCIAL SERVER (Node.js)                       │
│  Tools:                                                     │
│  - social_post_facebook                                     │
│  - social_post_instagram                                    │
│  - social_get_facebook_comments                             │
│  - social_get_facebook_insights                             │
│  - social_delete_facebook_post                              │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│              FACEBOOK GRAPH API                             │
│  - Posts content                                            │
│  - Retrieves data                                           │
│  - Manages media                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Facebook Watcher

**File:** `watchers/facebook_watcher.py`

Monitors Facebook Page for:
- New comments on posts
- New Messenger messages
- Post engagement

**Features:**
- Automatic deduplication (tracks processed IDs)
- Error handling with retry logic (3 retries, exponential backoff)
- Circuit breaker pattern (stops after 3 consecutive errors)
- Rate limit handling (respects 429 responses)
- Configurable check interval (default: 5 minutes)

**Usage:**
```bash
# Check once
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault

# Continuous monitoring
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch

# Check status
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --status
```

### 2. Instagram Watcher

Monitors Instagram Business Account for:
- New comments on media
- Tagged mentions
- Media engagement

**Note:** Uses the same Facebook Watcher with `platform="both"` (default).

### 3. MCP Social Server

**File:** `mcp/social-server/index.js`

Provides tools for:
- Posting to Facebook
- Posting to Instagram
- Retrieving comments
- Getting insights
- Deleting posts

All operations respect `DRY_RUN` mode (default: true).

### 4. Human-in-the-Loop Approval

All sensitive actions require approval:

1. Claude creates approval file in `/Pending_Approval/`
2. Human reviews and moves to `/Approved/`
3. HITL skill executes the action via MCP
4. Action logged to `/Logs/` and `/Audit/`

---

## Setup Guide

### Quick Start

1. **Configure credentials** in `.env`:
   ```bash
   FACEBOOK_ACCESS_TOKEN=your_token_here
   FACEBOOK_PAGE_ID=your_page_id_here
   INSTAGRAM_ACCESS_TOKEN=your_token_here
   INSTAGRAM_USER_ID=your_user_id_here
   ```

2. **Test connection**:
   ```bash
   python watchers/test_facebook.py
   ```

3. **Run integration test**:
   ```bash
   python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault
   ```

4. **Start watcher**:
   ```bash
   python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch
   ```

### Detailed Setup

See [`docs/FACEBOOK_SETUP_GUIDE.md`](./FACEBOOK_SETUP_GUIDE.md) for complete OAuth setup instructions.

---

## Available Skills

### Core Skills

| Skill | Description | Command |
|-------|-------------|---------|
| `/facebook-watcher` | Start Facebook/Instagram monitoring | `python watchers/facebook_watcher.py --vault $VAULT --watch` |
| `/facebook-status` | Check watcher health | `python watchers/facebook_watcher.py --vault $VAULT --status` |
| `/facebook-poster` | Generate and post Facebook update | `claude /social_post_facebook` |
| `/instagram-poster` | Generate and post Instagram update | `claude /social_post_instagram` |
| `/social-post-all` | Cross-post to all platforms | `claude /social_post_all` |

### Analytics Skills

| Skill | Description | Command |
|-------|-------------|---------|
| `/social-get-analytics` | Get social media analytics | `claude /social_get_analytics` |
| `/facebook-get-comments` | Get comments on Facebook post | `claude /social_get_facebook_comments` |
| `/facebook-get-insights` | Get Facebook Page insights | `claude /social_get_facebook_insights` |

### Management Skills

| Skill | Description | Command |
|-------|-------------|---------|
| `/facebook-delete-post` | Delete Facebook post (requires approval) | `claude /social_delete_facebook_post` |

---

## MCP Tools

### Posting Tools

#### `social_post_facebook`

Post update to Facebook Page.

**Parameters:**
- `message` (string, required): Post content

**Example:**
```bash
claude /social_post_facebook --message "Exciting news! Our AI Employee just hit 1000 followers!"
```

**Approval Flow:**
1. Creates `/Pending_Approval/APPROVAL_FACEBOOK_POST_YYYY-MM-DD_timestamp.md`
2. Human moves to `/Approved/`
3. HITL executes post via MCP
4. Logs action and moves to `/Done/`

#### `social_post_instagram`

Post image to Instagram Business account.

**Parameters:**
- `caption` (string, required): Post caption
- `image_url` (string, required): Public image URL

**Example:**
```bash
claude /social_post_instagram --caption "Behind the scenes at our office!" --image_url "https://example.com/image.jpg"
```

#### `social_post_all`

Cross-post to Twitter, Facebook, and Instagram.

**Parameters:**
- `content` (string, required): Main post content
- `image_url` (string, optional): Image URL (required for Instagram)
- `platforms` (array, optional): Specific platforms to post to

**Example:**
```bash
claude /social_post_all --content "Big announcement coming soon!" --platforms '["facebook", "twitter"]'
```

### Analytics Tools

#### `social_get_facebook_comments`

Get comments for a Facebook post.

**Parameters:**
- `post_id` (string, required): Facebook post ID
- `limit` (number, optional): Max comments (default: 10)

**Example:**
```bash
claude /social_get_facebook_comments --post_id "123456789_987654321"
```

#### `social_get_facebook_insights`

Get Facebook Page insights.

**Parameters:**
- `metrics` (array, optional): Metrics to retrieve

**Available Metrics:**
- `page_fan_count`: Total page likes
- `page_posts_engagement`: Engagement on posts
- `page_impressions`: Post impressions
- `page_reach`: Unique users who saw content

**Example:**
```bash
claude /social_get_facebook_insights --metrics '["page_fan_count", "page_posts_engagement"]'
```

### Management Tools

#### `social_delete_facebook_post`

Delete a Facebook post (requires approval).

**Parameters:**
- `post_id` (string, required): Post ID to delete

**Example:**
```bash
claude /social_delete_facebook_post --post_id "123456789_987654321"
```

---

## Watcher Configuration

### Environment Variables

```bash
# Facebook
FACEBOOK_ACCESS_TOKEN=EAAc...
FACEBOOK_PAGE_ID=123456789012345

# Instagram
INSTAGRAM_ACCESS_TOKEN=EAAc...
INSTAGRAM_USER_ID=17841400000000000

# Safety
DRY_RUN=true  # Set to false for real actions
```

### Watcher Settings

Edit `watchers/facebook_watcher.py`:

```python
# Check interval (default: 5 minutes)
check_interval = 300

# Max retries before circuit breaker
MAX_RETRIES = 3

# Request timeout
REQUEST_TIMEOUT = 30
```

### PM2 Setup (Production)

For 24/7 monitoring:

```bash
# Install PM2
npm install -g pm2

# Start Facebook watcher
pm2 start watchers/facebook_watcher.py --name facebook-watcher -- --vault ./AI_Employee_Vault --watch

# Save PM2 config
pm2 save

# Auto-start on boot
pm2 startup
```

---

## Workflows

### Workflow 1: Respond to Facebook Comment

```
1. Facebook Watcher detects new comment
   ↓
2. Creates action file in /Needs_Action/
   ↓
3. Reasoning Loop processes file
   ↓
4. Claude drafts reply → /Pending_Approval/
   ↓
5. Human reviews and approves
   ↓
6. HITL executes via MCP
   ↓
7. Logs action → /Done/
```

### Workflow 2: Post Business Update

```
1. Claude generates post content (scheduled or triggered)
   ↓
2. Creates approval file in /Pending_Approval/
   ↓
3. Human reviews content
   ↓
4. Moves to /Approved/
   ↓
5. HITL posts via MCP Social Server
   ↓
6. Logs post ID and timestamp → /Logs/
```

### Workflow 3: Weekly Analytics Report

```
1. CEO Briefing skill runs (scheduled Monday 7 AM)
   ↓
2. Calls /social_get_facebook_insights
   ↓
3. Retrieves metrics from Odoo + Social
   ↓
4. Generates briefing with analytics
   ↓
5. Saves to /Briefings/
```

---

## Troubleshooting

### Common Issues

#### "Authentication failed"

**Cause:** Invalid or expired access token

**Solution:**
```bash
# Regenerate token
python watchers/facebook_watcher.py --auth

# Test connection
python watchers/test_facebook.py
```

#### "Circuit breaker triggered"

**Cause:** Too many consecutive API errors

**Solution:**
```bash
# Check status
python watchers/facebook_watcher.py --status

# Reset circuit breaker (edit processed.json)
# Delete: AI_Employee_Vault/Logs/facebook_processed.json
```

#### "Rate limit exceeded"

**Cause:** Too many API calls

**Solution:**
- Watcher automatically backs off on 429 responses
- Wait 1 hour for limit reset
- Reduce check frequency if needed

#### "Insights not available"

**Cause:** Page needs more activity or app review

**Solution:**
- This is normal for new pages
- Insights require page activity
- Some metrics need Facebook app review

### Debug Mode

Enable verbose logging:

```python
# In facebook_watcher.py
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
```

### Test Suite

Run comprehensive integration tests:

```bash
python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault --full
```

Results saved to: `AI_Employee_Vault/Logs/facebook_test_results.json`

---

## API Reference

### Facebook Graph API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/{page-id}` | GET | Get page info |
| `/{page-id}/feed` | GET | Get page posts |
| `/{page-id}/comments` | GET | Get page comments |
| `/{page-id}/conversations` | GET | Get Messenger messages |
| `/{page-id}/feed` | POST | Create post |
| `/{page-id}/insights` | GET | Get page insights |
| `/{post-id}` | DELETE | Delete post |
| `/{post-id}/comments` | GET | Get post comments |

### Instagram Graph API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/{ig-user-id}` | GET | Get account info |
| `/{ig-user-id}/media` | GET | Get user's media |
| `/{ig-user-id}/media` | POST | Create media container |
| `/{ig-user-id}/media_publish` | POST | Publish media |
| `/{media-id}/comments` | GET | Get media comments |
| `/{ig-user-id}/tags` | GET | Get tagged mentions |

### Required Permissions

**Facebook:**
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_read_user_content`
- `pages_manage_metadata`

**Instagram:**
- `instagram_basic`
- `instagram_manage_comments`
- `instagram_manage_insights`

---

## Security Notes

1. **Never commit tokens** to version control
2. **Use DRY_RUN=true** until ready for production
3. **All posts require approval** (Human-in-the-Loop)
4. **Rotate tokens every 60 days**
5. **Monitor API usage** in Facebook Developer Dashboard
6. **Use HTTPS** for all API calls

---

## Resources

- [Facebook Graph API Docs](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API Docs](https://developers.facebook.com/docs/instagram-api)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [Setup Guide](./FACEBOOK_SETUP_GUIDE.md)
- [Test Script](../watchers/test_facebook_integration.py)

---

**Gold Tier Status:** ✅ Complete

All Facebook integration features implemented and tested.
