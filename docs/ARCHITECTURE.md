# AI Employee — Architecture & Lessons Learned

**Tier:** Gold (v0.3)
**Updated:** 2026-03-09

---

## Overview

A Personal AI Employee built on Claude Code + Obsidian vault. The system runs 24/7, monitors multiple inputs (email, social media, filesystem), reasons about them, and takes actions — always with human-in-the-loop approval for sensitive operations.

---

## Architecture: Perception → Reasoning → Action

```
┌─────────────────────────────────────────────────────────────────┐
│                        PERCEPTION LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Gmail Watcher│  │ File Watcher │  │  LinkedIn Watcher      │ │
│  │ (120s poll)  │  │ (watchdog)   │  │  (Playwright)          │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬─────────────┘ │
│  ┌──────┴───────┐  ┌──────┴──────────────────────┴─────────────┐ │
│  │Twitter Watcher│  │        Facebook/Instagram Watcher          │ │
│  │ (tweepy 5min) │  │        (Graph API, 5min poll)              │ │
│  └──────┬───────┘  └──────────────────────┬──────────────────── ┘ │
│         │                                  │                        │
│         └──────────────┬───────────────────┘                       │
│                        ▼                                            │
│              /AI_Employee_Vault/Needs_Action/*.md                   │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        REASONING LAYER                            │
│                                                                   │
│   Claude Code (claude-sonnet-4-6)                                │
│   ├── reads Company_Handbook.md (rules of engagement)            │
│   ├── reads Needs_Action/*.md                                     │
│   ├── applies priority triage (P1-P4)                            │
│   ├── creates Plans/*.md                                          │
│   └── routes sensitive actions → Pending_Approval/               │
│                                                                   │
│   Ralph Wiggum Stop Hook                                          │
│   └── if Needs_Action not empty → keeps Claude iterating         │
│                                                                   │
│   Skills (Agent Skills in .claude/skills/):                      │
│   ├── reasoning-loop     ├── process-vault                       │
│   ├── hitl-approval      ├── send-email                          │
│   ├── linkedin-poster    ├── twitter-poster                      │
│   ├── facebook-poster    ├── ceo-briefing                        │
│   ├── gmail-watcher      └── schedule-task                       │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ACTION LAYER                              │
│                                                                   │
│   MCP Servers (Model Context Protocol):                           │
│   ├── email-server   → Gmail send/draft/search (Node.js)         │
│   ├── odoo-server    → Odoo JSON-RPC accounting (Node.js)        │
│   └── social-server  → Twitter/Facebook/Instagram posting        │
│                                                                   │
│   HITL Approval Gate:                                             │
│   Pending_Approval/ → human moves to Approved/ or Rejected/      │
│   → HITL skill executes approved, cancels rejected               │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
D:/fiinal_hackathon_0/
├── AI_Employee_Vault/          ← Obsidian vault (brain & GUI)
│   ├── Inbox/                  ← Drop new files here
│   ├── Needs_Action/           ← Watcher-created action files
│   ├── Plans/                  ← Claude-created plan files
│   ├── Pending_Approval/       ← Sensitive actions awaiting human
│   ├── Approved/               ← Human-approved actions
│   ├── Rejected/               ← Human-rejected actions
│   ├── Done/                   ← Completed items archive
│   ├── Logs/                   ← Audit logs (YYYY-MM-DD.md)
│   ├── Briefings/              ← Weekly CEO briefings
│   ├── Accounting/             ← Financial summaries
│   ├── Dashboard.md            ← Live status dashboard
│   └── Company_Handbook.md     ← Rules of engagement
│
├── watchers/                   ← Python watcher scripts
│   ├── base_watcher.py         ← Abstract base class
│   ├── filesystem_watcher.py   ← /Inbox monitor (Bronze)
│   ├── gmail_watcher.py        ← Gmail unread+important (Silver)
│   ├── linkedin_watcher.py     ← LinkedIn notifications (Silver)
│   ├── twitter_watcher.py      ← Twitter mentions + DMs (Gold)
│   └── facebook_watcher.py     ← Facebook + Instagram (Gold)
│
├── mcp/                        ← MCP servers
│   ├── email-server/           ← Gmail send/draft (Silver)
│   ├── odoo-server/            ← Odoo accounting (Gold)
│   └── social-server/          ← Social media posting (Gold)
│
├── hooks/                      ← Claude Code hooks
│   └── ralph_wiggum.py         ← Stop hook (Gold)
│
├── scheduler/                  ← Task Scheduler setup
│   ├── setup_scheduler.py      ← One-command setup
│   └── run_claude.ps1          ← PowerShell wrapper
│
├── .claude/
│   ├── settings.json           ← MCP server registrations + hooks
│   └── skills/                 ← Agent Skills
│       ├── reasoning-loop/
│       ├── process-vault/
│       ├── hitl-approval/
│       ├── send-email/
│       ├── linkedin-poster/
│       ├── twitter-poster/
│       ├── facebook-poster/
│       ├── ceo-briefing/
│       ├── gmail-watcher/
│       └── schedule-task/
│
├── docs/
│   └── ARCHITECTURE.md         ← This file
├── requirements.txt            ← Python dependencies
├── CLAUDE.md                   ← Claude Code project instructions
└── .env                        ← Secrets (never commit!)
```

---

## Tier Progression

| Feature | Bronze | Silver | Gold |
|---------|--------|--------|------|
| Obsidian vault | ✅ | ✅ | ✅ |
| Filesystem watcher | ✅ | ✅ | ✅ |
| Gmail watcher | | ✅ | ✅ |
| LinkedIn watcher + poster | | ✅ | ✅ |
| Email MCP server | | ✅ | ✅ |
| HITL approval workflow | | ✅ | ✅ |
| Reasoning loop skill | | ✅ | ✅ |
| Task Scheduler + PM2 | | ✅ | ✅ |
| Twitter/X watcher + poster | | | ✅ |
| Facebook/Instagram watcher + poster | | | ✅ |
| Odoo accounting MCP | | | ✅ |
| Social MCP server | | | ✅ |
| CEO Briefing skill | | | ✅ |
| Ralph Wiggum Stop Hook | | | ✅ |
| Error recovery + audit logs | | | ✅ |
| Architecture documentation | | | ✅ |

---

## Key Design Decisions

### 1. File-as-Message-Queue
All inter-component communication happens via Markdown files in the vault. No message broker, no database, no complex infrastructure. Files are:
- Human-readable in Obsidian
- Easy to audit
- Trivially backed up with git
- Survived even if Claude crashes

### 2. HITL by Default
Every external action (send email, post on social, make payment) requires a file in `/Pending_Approval/`. Human moves to `/Approved/` or `/Rejected/`. Claude never acts autonomously on external-facing actions.

### 3. Skills = Repeatable, Auditable Prompts
Each Agent Skill is a `.md` file with structured instructions. This means:
- Skills are version-controlled
- Skills are readable (non-technical owner can understand what Claude will do)
- Skills compose well (ceo-briefing skill calls odoo + social analytics)

### 4. Ralph Wiggum Loop
A Stop hook (`hooks/ralph_wiggum.py`) checks if `Needs_Action/` or `Pending_Approval/` still has items when Claude tries to stop. If yes, it returns exit code 1 and prints a message, causing Claude to keep iterating. This prevents Claude from "forgetting" to complete tasks.

### 5. MCP for External Actions
MCP servers provide a clean interface between Claude's reasoning and real-world effects. Each server:
- Has defined tools (not arbitrary shell access)
- Logs all calls
- Respects `DRY_RUN=true` by default
- Can be independently tested

---

## Setup Guide

### First Time Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node.js MCP server deps
cd mcp/email-server && npm install && cd ../..
cd mcp/odoo-server && npm install && cd ../..
cd mcp/social-server && npm install && cd ../..

# 3. Authenticate Gmail
python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --auth

# 4. Configure social credentials
python watchers/twitter_watcher.py --vault ./AI_Employee_Vault --auth
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --auth

# 5. Set up Odoo (optional but recommended for Gold)
# See: https://www.odoo.com/documentation/17.0/administration/install.html

# 6. Start all watchers and schedulers
python scheduler/setup_scheduler.py

# 7. Check status
python scheduler/setup_scheduler.py --status
```

### Environment Variables (.env)

```env
# Gmail
GMAIL_CREDENTIALS=./credentials.json
GMAIL_TOKEN=./token.json

# LinkedIn (already configured)
LINKEDIN_ACCESS_TOKEN=your_token
LINKEDIN_PERSON_URN=urn:li:person:xxx

# Twitter/X
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_BEARER_TOKEN=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=

# Facebook / Instagram
FACEBOOK_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_USER_ID=

# Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USER=admin
ODOO_PASSWORD=admin

# Email MCP
DRY_RUN=true   # set to false to send real emails/posts
```

---

## Lessons Learned

1. **Start with the Handbook** — defining rules before building tools prevents chaotic agent behavior.
2. **Files over databases** — Obsidian vault as the single source of truth is genius for human oversight.
3. **HITL is not a limitation, it's the product** — owners trust the system *because* it asks for approval.
4. **Ralph Wiggum solves "lazy agent"** — without it, Claude stops too early on multi-step tasks.
5. **MCP DRY_RUN by default** — accidentally posting real content during testing is a nightmare; DRY_RUN saves you.
6. **Skills > prompts** — structured skill files with explicit steps produce far more consistent behavior than ad-hoc prompting.
7. **Log everything** — the audit trail in `/Logs/` is invaluable for debugging and owner trust.

---

*AI Employee v0.3 (Gold Tier) — Built for Hackathon 0*
