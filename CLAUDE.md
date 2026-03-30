# AI Employee — Claude Code Context (Gold Tier)

## Project Overview

This is a **Personal AI Employee** built for Hackathon 0. The system uses Claude Code as the reasoning engine and an Obsidian vault (`AI_Employee_Vault/`) as the local knowledge base and task management dashboard.

## Vault Location

```
D:/fiinal_hackathon_0/AI_Employee_Vault/
```

When working with vault files, always use this absolute path or paths relative to the project root.

## Vault Structure

```
AI_Employee_Vault/
├── Inbox/              ← Drop new files here (watcher monitors this)
├── Needs_Action/       ← Watcher creates .md action files here
├── Plans/              ← Claude creates Plan files here
├── Pending_Approval/   ← Sensitive actions waiting for human approval
├── Approved/           ← Human moved files here to approve
├── Rejected/           ← Human moved files here to reject
├── Done/               ← Completed items moved here
├── Logs/               ← Audit logs (YYYY-MM-DD.md format)
├── Briefings/          ← Weekly CEO Briefings
├── Accounting/         ← Financial summaries (Odoo integration)
├── Dashboard.md        ← Live status dashboard (always update this)
└── Company_Handbook.md ← Rules of engagement (read before every task)
```

## Core Rules

1. **Always read `Company_Handbook.md` first** before taking any action.
2. **Never delete files** without explicit human approval.
3. **Never send messages, emails, or payments** without creating an approval file in `/Pending_Approval/` first.
4. **Always update `Dashboard.md`** after processing items.
5. **Always log actions** to `/Logs/YYYY-MM-DD.md`.
6. **HITL rule:** Check `/Approved/` and `/Rejected/` before executing any external action.
7. **Error rule:** Log all errors to `/Logs/errors.md` and surface on Dashboard.

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| Process Vault | `/process-vault` | Scan `/Needs_Action`, create Plans, update Dashboard, move to `/Done` |
| Reasoning Loop | `/reasoning-loop` | Full reasoning brain — triage inbox, apply Handbook, route approvals |
| HITL Approval | `/hitl-approval` | Check `/Pending_Approval`, execute approved, cancel rejected |
| Send Email | `/send-email` | Draft email → create approval file → send after human approval |
| LinkedIn Poster | `/linkedin-poster` | Draft LinkedIn post → approval → publish via LinkedIn API |
| Twitter Poster | `/twitter-poster` | Draft tweet → approval → publish via Twitter API |
| Facebook Poster | `/facebook-poster` | Draft Facebook/Instagram post → approval → publish |
| CEO Briefing | `/ceo-briefing` | Weekly business audit — finance, tasks, social, alerts |
| Gmail Watcher | `/gmail-watcher` | Run/manage Gmail monitoring daemon |
| Schedule Task | `/schedule-task` | Set up Windows Task Scheduler / PM2 recurring jobs |

## Watcher Scripts

Located in `watchers/`:

| Script | Purpose | Run Command |
|--------|---------|-------------|
| `filesystem_watcher.py` | Monitors `/Inbox` for new files | `python watchers/filesystem_watcher.py --vault ./AI_Employee_Vault` |
| `gmail_watcher.py` | Monitors Gmail (unread + important) | `python watchers/gmail_watcher.py --vault ./AI_Employee_Vault` |
| `linkedin_watcher.py` | Monitors LinkedIn notifications | `python watchers/linkedin_watcher.py --vault ./AI_Employee_Vault --watch` |
| `twitter_watcher.py` | Monitors Twitter mentions + DMs | `python watchers/twitter_watcher.py --vault ./AI_Employee_Vault --watch` |
| `facebook_watcher.py` | Monitors Facebook + Instagram | `python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --watch` |

### First-time auth:
```bash
python watchers/gmail_watcher.py --vault ./AI_Employee_Vault --auth
python watchers/twitter_watcher.py --vault ./AI_Employee_Vault --auth
python watchers/facebook_watcher.py --vault ./AI_Employee_Vault --auth
```

### Start all watchers via PM2 (recommended):
```bash
python scheduler/setup_scheduler.py
```

## MCP Servers

| Server | Location | Tools |
|--------|----------|-------|
| `email` | `mcp/email-server/index.js` | `email_send`, `email_draft`, `email_search`, `email_get` |
| `odoo` | `mcp/odoo-server/index.js` | `odoo_get_invoices`, `odoo_create_invoice`, `odoo_get_balance`, `odoo_get_revenue`, `odoo_list_payments`, `odoo_get_customers` |
| `social` | `mcp/social-server/index.js` | `social_post_tweet`, `social_reply_tweet`, `social_post_facebook`, `social_post_instagram`, `social_post_all`, `social_get_analytics` |

### MCP setup:
```bash
cd mcp/email-server && npm install && cd ../..
cd mcp/odoo-server && npm install && cd ../..
cd mcp/social-server && npm install && cd ../..
```

All MCP servers registered in `.claude/settings.json` and auto-start with Claude Code.
`DRY_RUN=true` by default — set to `false` in `.env` to send real messages/posts.

## Ralph Wiggum Hook

A Stop hook (`hooks/ralph_wiggum.py`) runs when Claude tries to stop. If `/Needs_Action/` or `/Pending_Approval/` still have items, it exits with code 1 to keep Claude working.

## File Naming Conventions

| Type            | Pattern                              |
|-----------------|--------------------------------------|
| Action files    | `FILE_<name>_<timestamp>.md`         |
| Email actions   | `EMAIL_<id>_<timestamp>.md`          |
| LinkedIn posts  | `LINKEDIN_<topic>_<YYYY-MM-DD>.md`   |
| Twitter posts   | `TWITTER_<type>_<id>_<timestamp>.md` |
| Facebook posts  | `FACEBOOK_<type>_<id>_<timestamp>.md`|
| Instagram posts | `INSTAGRAM_<type>_<id>_<timestamp>.md`|
| Plan files      | `PLAN_<item>_<YYYY-MM-DD>.md`        |
| Approval files  | `APPROVAL_<action>_<YYYY-MM-DD>.md`  |
| Log files       | `YYYY-MM-DD.md`                      |
| Briefings       | `<YYYY-MM-DD>_Monday_Briefing.md`    |

## Priority Levels

| Priority | SLA         |
|----------|-------------|
| P1       | 1 hour      |
| P2       | 24 hours    |
| P3       | 48 hours    |
| P4       | Weekly      |

## Scheduling (Gold Tier)

Automated tasks run via Windows Task Scheduler + PM2:

| Job | Trigger | Skill |
|-----|---------|-------|
| Reasoning Loop | Every 30 min | `/reasoning-loop` |
| HITL Approval | Every 5 min | `/hitl-approval` |
| LinkedIn Post | Tue & Thu 7AM | `/linkedin-poster` |
| Twitter Post | Tue & Thu 8AM | `/twitter-poster` |
| CEO Briefing | Monday 7AM | `/ceo-briefing` |

Check scheduler status: `python scheduler/setup_scheduler.py --status`

## Current Tier

**Gold** — Autonomous Employee.
- 5 Watcher scripts (Filesystem + Gmail + LinkedIn + Twitter + Facebook/Instagram)
- 3 MCP servers (Email + Odoo Accounting + Social Media)
- Human-in-the-loop approval workflow
- LinkedIn, Twitter, Facebook, Instagram posting
- Odoo Community accounting integration
- CEO Weekly Business Briefing
- Ralph Wiggum Stop Hook (autonomous multi-step completion)
- Automated scheduling via Windows Task Scheduler + PM2
- Full reasoning loop with Plan.md creation
- Comprehensive audit logging + error recovery
- Architecture documentation
- All AI functionality as Agent Skills

## Architecture Reference

See `docs/ARCHITECTURE.md` for full system design, setup guide, and lessons learned.
