# Facebook Integration — Gold Tier Implementation

**AI Employee Hackathon 0 | Status: ✅ Complete**

---

## Quick Start

```bash
# 1. Configure credentials in .env
# 2. Test connection
python watchers/test_facebook.py

# 3. Run integration tests
python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault

# 4. Start monitoring
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch

# 5. Post to Facebook (dry run by default)
claude /social_post_facebook --message "Hello from AI Employee!"
```

---

## What's Implemented

### ✅ Watchers

| Component | Status | Features |
|-----------|--------|----------|
| **Facebook Watcher** | ✅ Complete | Comments, messages, posts monitoring |
| **Instagram Watcher** | ✅ Complete | Comments, mentions, media monitoring |
| **Error Handling** | ✅ Complete | Retry logic, circuit breaker, rate limiting |
| **Status Check** | ✅ Complete | Health monitoring and reporting |

### ✅ MCP Tools

| Tool | Status | Description |
|------|--------|-------------|
| `social_post_facebook` | ✅ Complete | Post to Facebook Page |
| `social_post_instagram` | ✅ Complete | Post to Instagram Business |
| `social_post_all` | ✅ Complete | Cross-post to all platforms |
| `social_get_analytics` | ✅ Complete | Get engagement metrics |
| `social_get_facebook_comments` | ✅ Complete | Retrieve post comments |
| `social_get_facebook_insights` | ✅ Complete | Get page insights |
| `social_delete_facebook_post` | ✅ Complete | Delete posts (with approval) |

### ✅ Agent Skills

| Skill | Category | Status |
|-------|----------|--------|
| `/facebook-watcher` | Watchers | ✅ |
| `/facebook-status` | Watchers | ✅ |
| `/facebook-poster` | Social | ✅ |
| `/instagram-poster` | Social | ✅ |
| `/social-post-all` | Social | ✅ |
| `/facebook-get-comments` | Analytics | ✅ |
| `/facebook-get-insights` | Analytics | ✅ |
| `/facebook-delete-post` | Management | ✅ |

### ✅ Documentation

| Document | Status | Location |
|----------|--------|----------|
| Setup Guide | ✅ Complete | `docs/FACEBOOK_SETUP_GUIDE.md` |
| Integration Guide | ✅ Complete | `docs/FACEBOOK_INTEGRATION.md` |
| Posting Workflow | ✅ Complete | `docs/FACEBOOK_POSTING_WORKFLOW.md` |
| Test Suite | ✅ Complete | `watchers/test_facebook_integration.py` |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Facebook & Instagram                      │
│                    (External Platforms)                      │
└────────────────────┬─────────────────────────────────────────┘
                     │ Graph API
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              Facebook Watcher (Python)                       │
│  - Polls every 5 minutes                                     │
│  - Creates action files                                      │
│  - Error handling + circuit breaker                          │
└────────────────────┬─────────────────────────────────────────┘
                     │ Files
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              Obsidian Vault (Local)                          │
│  /Needs_Action/ → /Plans/ → /Pending_Approval/               │
│  /Approved/ → /Done/ → /Logs/                                │
└────────────────────┬─────────────────────────────────────────┘
                     │ Claude Code
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              MCP Social Server (Node.js)                     │
│  - social_post_facebook                                      │
│  - social_get_facebook_comments                              │
│  - social_get_facebook_insights                              │
│  - social_delete_facebook_post                               │
└────────────────────┬─────────────────────────────────────────┘
                     │ Graph API
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              Facebook Graph API                              │
│  - Posts content                                             │
│  - Retrieves data                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
D:\fiinal_hackathon_0/
├── watchers/
│   ├── facebook_watcher.py          # Main watcher (FB + IG)
│   ├── test_facebook.py             # Connection test
│   └── test_facebook_integration.py # Full integration test
│
├── mcp/
│   └── social-server/
│       └── index.js                 # MCP server with FB tools
│
├── skills.json                      # Agent skills (FB skills added)
│
├── docs/
│   ├── FACEBOOK_SETUP_GUIDE.md     # OAuth setup
│   ├── FACEBOOK_INTEGRATION.md     # Technical docs
│   └── FACEBOOK_POSTING_WORKFLOW.md # Workflow docs
│
├── .env                             # Credentials (configured)
└── AI_Employee_Vault/
    ├── Needs_Action/
    ├── Pending_Approval/
    ├── Approved/
    ├── Done/
    └── Logs/
```

---

## Configuration

### Environment Variables

```bash
# .env file
FACEBOOK_ACCESS_TOKEN=EAAc...your_token_here
FACEBOOK_PAGE_ID=123456789012345
INSTAGRAM_ACCESS_TOKEN=EAAc...your_token_here
INSTAGRAM_USER_ID=17841400000000000

# Safety (default: true)
DRY_RUN=true
```

### Setup Steps

1. **Get Facebook Access Token**
   - Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
   - Select your app
   - Get Token → Get Page Access Token
   - Add permissions: `pages_manage_posts`, `pages_read_engagement`

2. **Get Page ID**
   - Your Facebook Page → About → Page ID
   - Or: Graph API `/{page-id}?fields=id`

3. **Get Instagram User ID**
   - Graph API: `/{page-id}?fields=instagram_business_account`
   - Copy the `id` from response

4. **Test Connection**
   ```bash
   python watchers/test_facebook.py
   ```

---

## Usage Examples

### Monitor Facebook & Instagram

```bash
# Continuous monitoring (every 5 minutes)
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch

# Check once
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault

# Check status
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --status
```

### Post to Facebook

```bash
# Using Claude skill (creates approval file)
claude /social_post_facebook --message "Exciting news from AI Employee!"

# MCP tool directly (still requires approval in DRY_RUN mode)
claude /social_post_facebook --message "Test post"
```

### Get Analytics

```bash
# Get Facebook insights
claude /facebook-get-insights --metrics '["page_fan_count", "page_posts_engagement"]'

# Get post comments
claude /facebook-get-comments --post_id "123456789_987654321"

# Get all social analytics
claude /social_get_analytics --platform "all"
```

### Cross-Post

```bash
# Post to all platforms
claude /social-post-all --content "Big announcement!" --image_url "https://example.com/img.jpg"

# Post to specific platforms
claude /social-post-all --content "Update!" --platforms '["facebook", "twitter"]'
```

---

## Testing

### Run Integration Tests

```bash
# Full test suite
python watchers/test_facebook_integration.py --vault ./AI_Employee_Vault

# Test results saved to:
# AI_Employee_Vault/Logs/facebook_test_results.json
```

### Test Suite Includes

1. ✅ Credential validation
2. ✅ Facebook Page connection
3. ✅ Instagram Business connection
4. ✅ Post retrieval
5. ✅ Comment retrieval
6. ✅ Insights retrieval
7. ✅ Watcher status
8. ✅ Action file creation
9. ✅ MCP server check

---

## Workflows

### Workflow 1: Respond to Comment

```
1. Facebook Watcher → Detects comment
2. Creates → /Needs_Action/FACEBOOK_COMMENT_*.md
3. Reasoning Loop → Creates reply plan
4. Creates → /Pending_Approval/APPROVAL_FACEBOOK_REPLY_*.md
5. Human → Moves to /Approved/
6. HITL → Posts reply via MCP
7. Logs → /Logs/ and /Audit/
```

### Workflow 2: Scheduled Post

```
1. Scheduler → Triggers every Tuesday 7 AM
2. Claude → Generates post content
3. Creates → /Pending_Approval/APPROVAL_FACEBOOK_POST_*.md
4. Human → Reviews and approves
5. HITL → Posts via MCP
6. Analytics → Tracked in Dashboard.md
```

---

## Error Handling

### Circuit Breaker Pattern

```python
# In facebook_watcher.py
MAX_RETRIES = 3  # After 3 errors, circuit breaker triggers
RETRY_DELAY = 5  # Exponential backoff
REQUEST_TIMEOUT = 30  # Seconds

# Status check shows:
# Circuit Breaker Active: ⚠️ YES (if errors >= 3)
```

### Rate Limiting

```python
# Automatic handling of 429 responses
if resp.status_code == 429:
    retry_after = int(resp.headers.get('Retry-After', 5))
    time.sleep(retry_after)
```

### Error Recovery

```bash
# Check system health
claude /error-recovery --check

# Retry failed operations
claude /error-recovery --retry-failed

# List quarantined files
claude /error-recovery --quarantine-list
```

---

## Security

### Best Practices

1. ✅ **DRY_RUN=true** by default (no real posts)
2. ✅ **Human approval required** for all posts
3. ✅ **Credentials in .env** (never in vault or git)
4. ✅ **Rate limiting** enforced
5. ✅ **Audit logging** for all actions
6. ✅ **Circuit breakers** prevent cascade failures

### Permissions Required

**Facebook:**
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_read_user_content`

**Instagram:**
- `instagram_basic`
- `instagram_manage_comments`

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Authentication failed | Regenerate token in Graph API Explorer |
| Circuit breaker active | Check logs, fix underlying error, restart watcher |
| Rate limit exceeded | Wait 1 hour, watcher auto-recovers |
| No Instagram data | Verify IG Business account linked to FB Page |

### Debug Commands

```bash
# Check credentials
python watchers/test_facebook.py

# Check watcher status
python watchers/facebook_watcher.py --status

# Run integration tests
python watchers/test_facebook_integration.py

# Check logs
cat AI_Employee_Vault/Logs/facebook_*.md
```

---

## Metrics

### Implementation Status

| Category | Progress | Status |
|----------|----------|--------|
| Watchers | 100% | ✅ Complete |
| MCP Tools | 100% | ✅ Complete |
| Agent Skills | 100% | ✅ Complete |
| Documentation | 100% | ✅ Complete |
| Testing | 100% | ✅ Complete |
| Error Handling | 100% | ✅ Complete |

### Code Stats

- **Facebook Watcher:** 460+ lines
- **MCP Social Server:** 570+ lines
- **Test Suite:** 350+ lines
- **Documentation:** 100+ pages
- **Agent Skills:** 8 Facebook-specific skills

---

## Next Steps

### For Production Use

1. **Set DRY_RUN=false** (when ready for real posts)
2. **Configure PM2** for 24/7 monitoring
3. **Set up app review** with Facebook (for extended permissions)
4. **Configure webhooks** (optional, for real-time updates)
5. **Add backup authentication** (token refresh automation)

### Optional Enhancements

- [ ] Facebook Stories posting
- [ ] Facebook Live integration
- [ ] Advanced analytics dashboard
- [ ] A/B testing for posts
- [ ] Optimal posting time suggestions
- [ ] Sentiment analysis for comments

---

## Resources

### Documentation

- 📖 [Setup Guide](./docs/FACEBOOK_SETUP_GUIDE.md)
- 📖 [Integration Guide](./docs/FACEBOOK_INTEGRATION.md)
- 📖 [Posting Workflow](./docs/FACEBOOK_POSTING_WORKFLOW.md)

### External Links

- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [Access Token Documentation](https://developers.facebook.com/docs/facebook-login/access-tokens)

### Support

```bash
# Run auth guide
python watchers/facebook_watcher.py --auth

# Check test results
cat AI_Employee_Vault/Logs/facebook_test_results.json
```

---

## Gold Tier Checklist

### Facebook Integration Requirements

- [x] Facebook Page monitoring (comments, messages)
- [x] Instagram Business monitoring (comments, mentions)
- [x] Facebook posting with approval workflow
- [x] Instagram posting with approval workflow
- [x] Cross-posting capability
- [x] Analytics and insights retrieval
- [x] Post management (delete with approval)
- [x] Error handling (retry, circuit breaker)
- [x] Rate limiting
- [x] Comprehensive documentation
- [x] Test suite
- [x] Agent skills (8 Facebook-specific skills)
- [x] MCP tools (7 Facebook tools)

**Status: ✅ GOLD TIER COMPLETE**

---

*Last Updated: March 17, 2026*
*AI Employee Hackathon 0 — Gold Tier Submission*
