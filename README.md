# Personal AI Employee — Gold Tier

> **Hackathon 0: Building Autonomous FTEs in 2026**
> Tier: Gold (Autonomous Employee)

**🎯 Facebook Integration: ✅ COMPLETE** - Full Facebook & Instagram integration with posting, monitoring, analytics, and approval workflows.

---

## What This Is

A local-first, Claude Code-powered **Autonomous AI Employee** that works 24/7 by:

- **Monitoring 6+ channels**: Gmail, LinkedIn, Twitter/X, Facebook, Instagram, and local file system
- **Creating structured action files** in `/Needs_Action/` automatically
- **Running autonomous reasoning loops** with the Ralph Wiggum pattern for multi-step task completion
- **Integrating with Odoo ERP** for accounting, invoices, and financial reporting
- **Generating Weekly CEO Briefings** with revenue reports, bottlenecks, and proactive suggestions
- **Cross-posting to social media** (Twitter, Facebook, Instagram) with human approval
- **Comprehensive audit logging** for compliance and debugging
- **Error recovery & graceful degradation** for production resilience
- All AI functionality exposed as Claude Code **Agent Skills**

---

## 🆕 Gold Tier Features

### Facebook Integration (NEW!)

✅ **Complete Facebook & Instagram Integration**

- **Facebook Watcher**: Monitors Page comments, posts, and Messenger messages
- **Instagram Watcher**: Monitors Business account comments and mentions
- **Facebook Posting**: Post updates with human approval workflow
- **Instagram Posting**: Post images with captions (approval required)
- **Analytics**: Get Facebook Insights and engagement metrics
- **Comment Management**: Retrieve and respond to comments
- **Error Handling**: Circuit breaker, retry logic, rate limiting
- **Documentation**: Complete setup guide, integration docs, and workflow docs

**Quick Start:**
```bash
# Test connection
python watchers/test_facebook.py

# Start monitoring
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch

# Post to Facebook (dry run by default)
claude /social_post_facebook --message "Hello from AI Employee!"

# Get insights
claude /facebook-get-insights
```

**Documentation:**
- 📖 [Facebook Setup Guide](docs/FACEBOOK_SETUP_GUIDE.md)
- 📖 [Facebook Integration](docs/FACEBOOK_INTEGRATION.md)
- 📖 [Posting Workflow](docs/FACEBOOK_POSTING_WORKFLOW.md)
- 📖 [Gold Tier README](FACEBOOK_GOLD_TIER_README.md)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                             │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│  Gmail   │ LinkedIn │ Twitter  │ Facebook │ Instagram│  Files  │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬────┘
     │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER (Watchers)                  │
│  gmail_watcher.py  linkedin_watcher.py  twitter_watcher.py      │
│  filesystem_watcher.py  facebook_watcher.py  instagram_watcher  │
└─────────────────────────────────────────────────────────────────┘
     │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Local Memory)                │
│  /Needs_Action/  /Plans/  /Pending_Approval/  /Approved/       │
│  /Done/  /Logs/  /Audit/  /Briefings/  Dashboard.md             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REASONING LAYER (Claude Code)                │
│  /reasoning-loop  /hitl-approval  /ceo-briefing  /odoo-*        │
│  Ralph Wiggum Stop Hook (keeps Claude iterating until done)     │
└─────────────────────────────────────────────────────────────────┘
                                 │
              ┌──────────────────┴───────────────────┐
              ▼                                      ▼
┌────────────────────────────┐    ┌────────────────────────────────┐
│    HUMAN-IN-THE-LOOP       │    │         ACTION LAYER           │
│  Review & Approve Files    │    │    MCP SERVERS                 │
│  /Pending_Approval/        │    │  - Email (Gmail)               │
│  → /Approved/ → Execute    │    │  - Odoo (Accounting)           │
│  → /Rejected/ → Cancel     │    │  - Social (Twitter/FB/IG)      │
└────────────────────────────┘    └────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   EXTERNAL ACTIONS     │
                    │  Send • Post • Pay     │
                    └────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SUPPORT SYSTEMS                              │
│  error_recovery.py  - Retry logic, quarantine, circuit breakers │
│  audit_logger.py  - Structured JSON + MD audit trails           │
│  watchdog.py  - Process health monitoring & auto-restart        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Tool        | Version    | Purpose                        |
|-------------|------------|--------------------------------|
| Python      | 3.13+      | Watcher scripts & skills       |
| Node.js     | v18+ LTS   | MCP servers                    |
| Claude Code | Latest     | Reasoning engine               |
| Obsidian    | v1.10.6+   | Vault GUI (optional viewer)    |
| PM2         | Latest     | Keep watchers alive 24/7       |
| Odoo        | 19+ CE     | Accounting & ERP (local/cloud) |

---

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt
playwright install chromium

# MCP server dependencies
cd mcp/email-server && npm install && cd ../..
cd mcp/odoo-server && npm install && cd ../..
cd mcp/social-server && npm install && cd ../..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. OAuth Setup (One-Time)

```bash
# Gmail
python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --auth

# LinkedIn
python watchers/linkedin_watcher.py --auth

# Twitter/X
python watchers/twitter_watcher.py --auth

# Facebook/Instagram
python watchers/facebook_watcher.py --auth
```

### 4. Odoo Setup (Gold Tier)

```bash
# Start Odoo (Docker)
docker compose up -d

# Initialize database with demo data
python odoo/setup_odoo.py --seed

# Verify connection
python odoo/setup_odoo.py --status
```

### 5. Start All Services

```bash
# Start watchers + scheduler (one command)
python scheduler/setup_scheduler.py

# Verify status
python scheduler/setup_scheduler.py --status
```

### 6. Run Claude Code

```bash
claude
```

---

## Available Skills (Gold Tier)

| Skill | What It Does |
|-------|-------------|
| `/reasoning-loop` | Scan `/Needs_Action`, create Plans, apply Handbook rules, route to approval |
| `/hitl-approval` | Execute approved actions via MCP, log, move to `/Done` |
| `/ceo-briefing` | Generate Monday Morning CEO Briefing with Odoo revenue data |
| `/odoo-get-invoices` | List/filter invoices from Odoo |
| `/odoo-create-invoice` | Create draft invoice in Odoo (requires approval to post) |
| `/odoo-get-balance` | Get accounting balance (receivables/payables) |
| `/odoo-get-revenue` | Revenue report for date range |
| `/odoo-get-customers` | List customers from Odoo |
| `/send-email` | Draft → approval → send via Email MCP |
| `/linkedin-poster` | Generate post → approval → publish via LinkedIn API |
| `/twitter-poster` | Generate tweet → approval → publish via Twitter API |
| `/facebook-poster` | Generate Facebook post → approval → publish via Graph API |
| `/instagram-poster` | Generate Instagram post → approval → publish |
| `/social-post-all` | Cross-post to Twitter, Facebook, Instagram |
| `/facebook-get-comments` | Get comments on a Facebook post |
| `/facebook-get-insights` | Get Facebook Page analytics and insights |
| `/facebook-delete-post` | Delete Facebook post (requires approval) |
| `/social-get-analytics` | Get engagement analytics for social media accounts |
| `/error-recovery` | Check system health, retry failed ops, manage quarantine |
| `/audit-report` | Generate compliance reports from audit logs |
| `/gmail-watcher` | Start/check/diagnose Gmail monitoring |
| `/facebook-watcher` | Start/check Facebook and Instagram monitoring |
| `/facebook-status` | Check Facebook/Instagram watcher health |
| `/schedule-task` | Manage Windows Task Scheduler / PM2 jobs |

---

## Watcher Scripts

| Script | Monitors | Interval | Gold Tier |
|--------|---------|---------|-----------|
| `filesystem_watcher.py` | `/Inbox` folder | Instant (watchdog) | ✅ |
| `gmail_watcher.py` | Gmail (unread + important) | 2 min | ✅ |
| `linkedin_watcher.py` | LinkedIn notifications | 5 min | ✅ |
| `twitter_watcher.py` | Twitter mentions & DMs | 5 min | ✅ Gold |
| `facebook_watcher.py` | Facebook Page + Instagram | 5 min | ✅ Gold |

**Facebook Watcher Features:**
- Monitors Facebook Page comments, posts, and Messenger messages
- Monitors Instagram Business comments and mentions
- Error handling with retry logic (3 retries, exponential backoff)
- Circuit breaker pattern (stops after 3 consecutive errors)
- Rate limit handling (respects 429 responses)
- Status checking (`--status` flag)
- Comprehensive test suite

---

## MCP Servers

| Server | Tools | Gold Tier |
|--------|-------|-----------|
| **email** | `email_send`, `email_draft`, `email_search`, `email_get` | ✅ |
| **odoo** | `odoo_get_invoices`, `odoo_create_invoice`, `odoo_get_balance`, `odoo_get_revenue`, `odoo_list_payments`, `odoo_get_customers` | ✅ Gold |
| **social** | `social_post_tweet`, `social_reply_tweet`, `social_post_facebook`, `social_post_instagram`, `social_post_all`, `social_get_analytics`, `social_get_facebook_comments`, `social_get_facebook_insights`, `social_delete_facebook_post` | ✅ Gold |

**Social MCP Server - New Facebook Tools:**
- `social_post_facebook` - Post updates to Facebook Page
- `social_post_instagram` - Post images to Instagram Business
- `social_get_facebook_comments` - Retrieve comments on posts
- `social_get_facebook_insights` - Get Page analytics and insights
- `social_delete_facebook_post` - Delete posts (with approval)

---

## Scheduled Tasks

| Job | Trigger | Skill |
|-----|---------|-------|
| Reasoning Loop | Every 30 min | `/reasoning-loop` |
| HITL Approval | Every 5 min | `/hitl-approval` |
| CEO Briefing | Monday 7AM | `/ceo-briefing` |
| LinkedIn Post | Tue & Thu 7AM | `/linkedin-poster` |
| Twitter Post | Tue & Thu 8AM | `/twitter-poster` |
| Social Cross-Post | Fri 9AM | `/social-post-all` |
| Audit Report | Sunday 6PM | `/audit-report` |

---

## Vault Structure (Gold Tier)

```
AI_Employee_Vault/
├── Inbox/                  ← Drop files here
├── Needs_Action/           ← Auto-generated action files
├── In_Progress/            ← Claimed items (claim-by-move rule)
├── Plans/                  ← Claude-generated plans
├── Pending_Approval/       ← Awaiting human review
├── Approved/               ← Ready to execute
├── Rejected/               ← Cancelled items
├── Done/                   ← Completed items
├── Logs/                   ← Daily markdown logs
├── Audit/
│   └── json/               ← Structured JSONL audit logs
├── Briefings/              ← CEO briefings
├── Quarantine/             ← Corrupted/problematic files
├── Dashboard.md            ← Live status view
├── Company_Handbook.md     ← AI rules of engagement
├── Business_Goals.md       ← Revenue targets & projects
└── .degradation_status.json ← Graceful degradation state
```

---

## Gold Tier Features

### 1. Odoo Accounting Integration

```bash
# Get invoice list
claude /odoo-get-invoices --state posted --limit 10

# Create draft invoice (requires approval)
claude /odoo-create-invoice --customer "Acme Corp" --amount 500 --description "Consulting"

# Get revenue report
claude /odoo-get-revenue --date-from 2026-03-01 --date-to 2026-03-31

# Get balance sheet
claude /odoo-get-balance
```

### 2. CEO Briefing (Monday Morning)

Generates comprehensive briefing with:
- Revenue vs. target
- Outstanding invoices
- Task completion metrics
- Bottleneck analysis
- Proactive suggestions
- Subscription audit

```bash
# Generate briefing
claude /ceo-briefing --period 7

# Preview before saving
python skills/ceo_briefing.py --vault ./AI_Employee_Vault --preview
```

### 3. Ralph Wiggum Loop

Autonomous multi-step task completion:

```bash
# The Stop hook keeps Claude iterating until:
# - /Needs_Action is empty
# - /Pending_Approval is empty
# - OR max iterations reached (default: 10)

# Configure in .claude/settings.json hooks
```

### 4. Error Recovery

```bash
# Check system health
claude /error-recovery --check

# List quarantined files
claude /error-recovery --quarantine-list

# Retry failed operations
claude /error-recovery --retry-failed
```

Features:
- Exponential backoff retry logic
- Circuit breaker pattern
- Graceful degradation
- File quarantine for corrupted data

### 5. Audit Logging

```bash
# Today's summary
claude /audit-report --status

# Search logs
claude /audit-report --search "email_send"

# Weekly compliance report
claude /audit-report --report week

# Cleanup old logs
claude /audit-report --cleanup --retention-days 90
```

---

## Security Notes

- **`DRY_RUN=true`** by default — no real actions until set to `false`
- **All sensitive actions require human approval** (file moved to `/Pending_Approval/`)
- **Credentials in `.env` only** — never committed to git, never in vault
- **Rate limiting**: max 10 emails/hour, max 20 social posts/day
- **All actions logged** to `/Audit/json/` (JSONL) and `/Logs/` (MD)
- **Circuit breakers** prevent cascade failures

---

## Error Handling

| Error Type | Recovery Strategy |
|------------|-------------------|
| Network timeout | Exponential backoff (3 retries) |
| API rate limit | Backoff + circuit breaker |
| Auth failure | Alert human, pause operations |
| Corrupted file | Quarantine + alert |
| Process crash | Watchdog auto-restart |

---

## Tier Declaration

**Gold Tier — Autonomous Employee** complete:

- [x] All Silver requirements
- [x] **6 Watchers**: Filesystem + Gmail + LinkedIn + Twitter + Facebook + Instagram
- [x] **Odoo Integration**: Full accounting MCP server (invoices, revenue, balance)
- [x] **Social Media**: Cross-post to Twitter, Facebook, Instagram
- [x] **CEO Briefing**: Weekly business + accounting audit
- [x] **Ralph Wiggum Loop**: Autonomous multi-step completion
- [x] **Error Recovery**: Retry logic, circuit breakers, quarantine
- [x] **Audit Logging**: Structured JSONL + compliance reports
- [x] **All AI functionality as Agent Skills** (16+ skills)

---

## Troubleshooting

### Odoo Connection Failed

```bash
# Check if Odoo is running
docker compose ps

# Verify credentials
python odoo/setup_odoo.py --status

# Check MCP server
node mcp/odoo-server/index.js
```

### Watcher Not Picking Up Items

```bash
# Check PM2 status
pm2 status

# Restart specific watcher
pm2 restart gmail-watcher

# Check logs
pm2 logs gmail-watcher
```

### Ralph Wiggum Stuck in Loop

```bash
# Check iteration count
cat AI_Employee_Vault/.ralph_iteration

# Reset manually
rm AI_Employee_Vault/.ralph_iteration

# Check what's blocking
python hooks/ralph_wiggum.py --status
```

### Audit Logs Growing Too Large

```bash
# Cleanup logs older than 30 days
python skills/audit_logger.py --cleanup --retention-days 30
```

---

## Hackathon Submission

- **Tier:** Gold
- **Watchers:** 6 (Filesystem + Gmail + LinkedIn + Twitter + Facebook + Instagram)
- **MCP Servers:** Email + Odoo + Social (3 servers)
- **Key Features:**
  - Odoo accounting integration
  - CEO Briefing with revenue reports
  - Ralph Wiggum autonomous loop
  - Error recovery & circuit breakers
  - Comprehensive audit logging
- **Security:** `.env` credentials, `DRY_RUN=true` default, HITL for all sensitive actions
- **Documentation:** This README + architecture diagrams + inline code docs

---

*Built with Claude Code for Hackathon 0 — Personal AI Employee (Gold Tier)*
