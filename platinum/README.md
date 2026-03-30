# Platinum Tier: Always-On Cloud + Local Executive

> **Hackathon 0: Building Autonomous FTEs in 2026**
> Tier: Platinum (Production-Ready AI Employee)

**🎯 Status:** ✅ **IMPLEMENTED** - Full Cloud + Local architecture with Git-based vault sync

---

## What This Is

The Platinum Tier extends the Gold Tier with:

- **Cloud Agent**: Runs 24/7 on a cloud VM (Oracle/AWS/DigitalOcean)
- **Local Agent**: Runs on your personal machine with credentials
- **Work-Zone Specialization**: Cloud drafts, Local executes
- **Git-Based Vault Sync**: Secure synchronization between Cloud and Local
- **Human-in-the-Loop**: All sensitive actions require Local approval
- **Production Deployment**: Docker, HTTPS, backups, monitoring

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD VM (24/7)                              │
│              Oracle Cloud / AWS EC2 / DigitalOcean              │
├─────────────────────────────────────────────────────────────────┤
│  Cloud Agent (Docker Container)                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Watchers (Draft-Only):                                   │   │
│  │ • Gmail Watcher → Email triage + draft replies           │   │
│  │ • Social Media Watcher → Monitor + draft posts           │   │
│  │ • Lead Capture Watcher → Identify high-value leads       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Cloud Drafter:                                           │   │
│  │ • Uses Claude Code to generate drafts                    │   │
│  │ • Creates approval files in /Pending_Approval/           │   │
│  │ • Syncs to Local via Git push                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Vault Sync: Git Push/Pull                                      │
│  Odoo: Self-hosted on Cloud VM (Community Edition)              │
└─────────────────────────────────────────────────────────────────┘
                              ↕
                    Git Vault Sync (Encrypted)
                    (Secrets NEVER sync)
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE (Your PC)                      │
├─────────────────────────────────────────────────────────────────┤
│  Local Agent (Desktop Application)                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Approval Workflow:                                       │   │
│  │ • Monitor /Pending_Approval/                             │   │
│  │ • Desktop notifications                                  │   │
│  │ • User approval/rejection                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Execution (MCP Access):                                  │   │
│  │ • Gmail MCP (send emails)                                │   │
│  │ • Social MCP (post to Twitter/FB/IG)                     │   │
│  │ • Odoo MCP (payments, invoices)                          │   │
│  │ • WhatsApp (local session)                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Vault: Obsidian (Local First)                                  │
│  Secrets: .env, Tokens, WhatsApp Session (NEVER sync)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Work-Zone Specialization

| Zone | Owns | Can Execute | Requires Approval |
|------|------|-------------|-------------------|
| **Cloud** | Email triage, Social monitoring, Lead capture | Draft creation | ALL send/post/pay actions |
| **Local** | WhatsApp, Payments, Final actions | Send/Post/Pay | Human approval |

### Security Rules

- **Secrets NEVER sync**: `.env`, tokens, WhatsApp sessions stay on Local
- **Git ignore**: `.secrets/`, `*.env`, `credentials.json`, `token.json`
- **Vault sync**: Only markdown files and state files
- **Claim-by-move**: First agent to move file owns it

---

## Quick Start

### Option A: Run Demo (Recommended for First Time)

```bash
cd D:\fiinal_hackathon_0

# Run Platinum demo (simulates full workflow)
python platinum/demo_flow.py --vault ./AI_Employee_Vault --speed 1.0
```

This demonstrates the complete flow without actual API calls.

### Option B: Deploy Cloud Agent

```bash
# 1. Setup Cloud VM (Oracle Cloud Free Tier)
# Follow: platinum/deploy/setup_cloud_vm.sh

# 2. Configure environment
export GIT_REMOTE="https://github.com/yourusername/ai-employee-vault.git"
cd platinum/deploy
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f cloud-agent
```

### Option C: Run Local Agent

```bash
# 1. Configure environment
export GIT_REMOTE="https://github.com/yourusername/ai-employee-vault.git"

# 2. Initialize Local Agent
python -m platinum.local_agent.main \
    --git-remote $GIT_REMOTE \
    --vault-path ./AI_Employee_Vault \
    --init-only

# 3. Start Local Agent
python -m platinum.local_agent.main \
    --git-remote $GIT_REMOTE \
    --vault-path ./AI_Employee_Vault
```

---

## Directory Structure

```
platinum/
├── README.md                       # This file
├── demo_flow.py                    # End-to-end demo
│
├── cloud_agent/                    # Cloud Agent (24/7 VM)
│   ├── __init__.py
│   ├── config.py                   # Cloud configuration
│   ├── watcher.py                  # Gmail, Social, Lead watchers
│   ├── drafter.py                  # Draft generation (Claude Code)
│   ├── sync_client.py              # Git sync client
│   └── main.py                     # Cloud Agent entry point
│
├── local_agent/                    # Local Agent (Your PC)
│   ├── __init__.py
│   ├── config.py                   # Local configuration
│   ├── approver.py                 # Human approval workflow
│   ├── executor.py                 # MCP execution
│   ├── notifier.py                 # Desktop notifications
│   ├── sync_client.py              # Git sync client
│   └── main.py                     # Local Agent entry point
│
├── sync/                           # Shared Sync Utilities
│   ├── __init__.py
│   ├── vault_sync.py               # Core Git sync
│   ├── conflict_resolver.py        # Conflict resolution
│   └── encryption.py               # Optional encryption
│
└── deploy/                         # Deployment Scripts
    ├── Dockerfile.cloud            # Cloud Agent Docker
    ├── docker-compose.yml          # Cloud services
    ├── setup_cloud_vm.sh           # VM setup script
    ├── nginx.conf                  # HTTPS configuration
    ├── odoo_backup.sh              # Odoo backup script
    └── requirements-platinum.txt   # Additional dependencies
```

---

## Platinum Demo Flow

The demo (`demo_flow.py`) simulates the complete Platinum workflow:

### Step-by-Step Flow

1. **Email Arrives** → Cloud Gmail Watcher detects
2. **Cloud Creates Draft** → Cloud Drafter generates reply
3. **Cloud Creates Approval** → Approval file in `/Pending_Approval/`
4. **Cloud Syncs** → Git push to remote
5. **Local Notifies** → Desktop notification to user
6. **User Approves** → Move file to `/Approved/`
7. **Local Executes** → Email MCP sends email
8. **Move to Done** → File moved to `/Done/`
9. **Local Syncs** → Git push completion to Cloud

### Running the Demo

```bash
# Normal speed
python platinum/demo_flow.py --vault ./AI_Employee_Vault

# Fast demo (0.5x wait time)
python platinum/demo_flow.py --vault ./AI_Employee_Vault --speed 0.5

# Slow demo (2x wait time)
python platinum/demo_flow.py --vault ./AI_Employee_Vault --speed 2.0
```

---

## Cloud Agent Features

### Watchers (Draft-Only)

| Watcher | Monitors | Creates | Interval |
|---------|----------|---------|----------|
| GmailCloudWatcher | Unread important emails | Draft replies | 2 min |
| SocialMediaCloudWatcher | Twitter, FB, IG, LinkedIn | Draft responses | 5 min |
| LeadCaptureWatcher | All channels for leads | Prioritized leads | 5 min |

### Cloud Drafter

- Uses Claude Code to generate drafts
- Applies Company Handbook rules
- Creates approval files automatically
- Draft expiry after 24 hours

### Cloud Sync Client

- Git-based vault synchronization
- Claim-by-move rule enforcement
- Conflict detection
- Secrets exclusion (never sync)

---

## Local Agent Features

### Approver

- Monitors `/Pending_Approval/`
- Desktop notifications (Windows/macOS/Linux)
- Sound notifications
- Email notifications (optional)
- Auto-approve for safe actions (configurable)

### Executor

- Executes approved actions via MCP
- Rate limiting enforcement
- Payment amount limits
- Comprehensive audit logging

### Notifier

- Cross-platform desktop notifications
- Priority-based alerts
- Notification history
- Sound alerts

### Local Sync Client

- Git pull from Cloud
- Merge Cloud updates into Dashboard.md
- Process Cloud signals
- Push approvals/completions to Cloud

---

## Deployment

### Cloud VM Setup (Oracle Cloud Free Tier)

```bash
# 1. Create VM
# - Shape: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM - Free)
# - Image: Ubuntu 22.04

# 2. Run setup script
export GIT_REMOTE="https://github.com/yourusername/ai-employee.git"
curl -O https://raw.githubusercontent.com/yourusername/ai-employee/main/platinum/deploy/setup_cloud_vm.sh
chmod +x setup_cloud_vm.sh
./setup_cloud_vm.sh

# 3. Configure .env
nano ai-employee/.env

# 4. Start services
cd ai-employee/platinum/deploy
docker-compose up -d

# 5. Check status
docker-compose ps
docker-compose logs -f cloud-agent
```

### Local Setup (Your PC)

```bash
# 1. Install dependencies
pip install -r platinum/deploy/requirements-platinum.txt

# 2. Configure Git remote
export GIT_REMOTE="https://github.com/yourusername/ai-employee-vault.git"

# 3. Initialize vault
python -m platinum.local_agent.main \
    --git-remote $GIT_REMOTE \
    --vault-path ./AI_Employee_Vault \
    --init-only

# 4. Start Local Agent
python -m platinum.local_agent.main \
    --git-remote $GIT_REMOTE \
    --vault-path ./AI_Employee_Vault
```

---

## Configuration

### Cloud Agent (.env)

```bash
# Cloud Configuration
CLOUD_PROVIDER=oracle
VM_REGION=us-ashburn-1
GIT_REMOTE=https://github.com/yourusername/ai-employee-vault.git
VAULT_PATH=/home/ubuntu/AI_Employee_Vault
AGENT_ID=cloud_agent

# Sync Settings
SYNC_INTERVAL=60
GMAIL_CHECK_INTERVAL=120
SOCIAL_CHECK_INTERVAL=300

# API Credentials (for monitoring only)
GMAIL_CLIENT_ID=xxx
GMAIL_CLIENT_SECRET=xxx
TWITTER_API_KEY=xxx
FACEBOOK_ACCESS_TOKEN=xxx
```

### Local Agent (.env)

```bash
# Local Configuration
GIT_REMOTE=https://github.com/yourusername/ai-employee-vault.git
VAULT_PATH=./AI_Employee_Vault
AGENT_ID=local_agent

# Security
DRY_RUN=true
REQUIRE_APPROVAL_PAYMENTS=true
REQUIRE_APPROVAL_NEW_CONTACTS=true
MAX_PAYMENT_AMOUNT=1000.0

# Notifications
DESKTOP_NOTIFICATIONS=true
NOTIFICATION_SOUND=true
EMAIL_NOTIFICATIONS=false

# API Credentials (NEVER sync to Cloud)
GMAIL_CREDENTIALS=./.secrets/credentials.json
WHATSAPP_SESSION_PATH=./whatsapp_session
```

---

## Security

### Secrets Management

| Secret | Stored | Synced |
|--------|--------|--------|
| Gmail credentials | Local `.secrets/` | ❌ Never |
| WhatsApp session | Local `whatsapp_session/` | ❌ Never |
| Banking tokens | Local `.secrets/` | ❌ Never |
| Social media tokens | Local `.secrets/` | ❌ Never |
| Git credentials | Cloud + Local | ✅ Encrypted |

### .gitignore Rules

```gitignore
# Secrets - NEVER SYNC
.env
*.env
credentials.json
token.json
tokens.json
.secrets/
whatsapp_session/
session/
*.session

# Logs (sync only summaries)
Logs/*.jsonl
Audit/json/*.jsonl
```

---

## Monitoring

### Health Check

```bash
# Cloud Agent health
docker-compose exec cloud-agent python -m platinum.cloud_agent.main --status

# Local Agent health
python -m platinum.local_agent.main --git-remote $GIT_REMOTE --status

# Vault sync status
cd AI_Employee_Vault
git status
```

### Logs

```bash
# Cloud Agent logs
docker-compose logs -f cloud-agent

# Local Agent logs
tail -f AI_Employee_Vault/Logs/*.md

# Audit logs
cat AI_Employee_Vault/Audit/json/*.jsonl | jq
```

### Backups

```bash
# Odoo backup (Cloud VM)
./platinum/deploy/odoo_backup.sh

# Vault backup (Git)
cd AI_Employee_Vault
git push origin main
```

---

## Troubleshooting

### Cloud Agent Not Syncing

```bash
# Check Git configuration
docker-compose exec cloud-agent git status
docker-compose exec cloud-agent git remote -v

# Check sync logs
docker-compose logs cloud-agent | grep sync
```

### Local Agent Not Receiving Updates

```bash
# Manual pull
cd AI_Employee_Vault
git pull origin main

# Check for conflicts
git status

# Reset if needed
git reset --hard origin/main
```

### Approval Notifications Not Working

```bash
# Check notification settings
cat .env | grep NOTIFICATION

# Test notifications
python -m platinum.local_agent.notifier --test

# Check approver status
python -m platinum.local_agent.main --git-remote $GIT_REMOTE --status
```

---

## Platinum Tier Checklist

### Core Requirements

- [x] **Cloud Agent 24/7**
  - [x] Docker deployment
  - [x] VM setup script
  - [x] Health monitoring
  - [x] Auto-restart

- [x] **Work-Zone Specialization**
  - [x] Cloud: Draft-only actions
  - [x] Local: Execution with credentials
  - [x] Clear separation of duties

- [x] **Vault Sync**
  - [x] Git-based synchronization
  - [x] Claim-by-move rule
  - [x] Conflict resolution
  - [x] Secrets exclusion

- [x] **Security**
  - [x] Secrets never sync
  - [x] .gitignore configured
  - [x] Encryption support (optional)

- [x] **Odoo on Cloud**
  - [x] Docker Compose setup
  - [x] Backup script
  - [x] HTTPS support (nginx)

- [x] **Demo Flow**
  - [x] End-to-end simulation
  - [x] Step-by-step logging
  - [x] Complete workflow demo

---

## Comparison: Gold vs Platinum

| Feature | Gold | Platinum |
|---------|------|----------|
| **Deployment** | Local only | Cloud + Local |
| **Availability** | When running | 24/7 |
| **Credentials** | Local | Local only (never sync) |
| **Watchers** | Full execution | Draft-only (Cloud) |
| **Execution** | Direct | Local Agent (Cloud drafts) |
| **Sync** | N/A | Git-based vault |
| **Odoo** | Local | Cloud VM |
| **Complexity** | Medium | High |
| **Use Case** | Personal automation | Production business |

---

## Next Steps

### Phase 1: Git Sync (Current)

- ✅ Cloud Agent implementation
- ✅ Local Agent implementation
- ✅ Git-based vault sync
- ✅ Demo flow

### Phase 2: A2A Upgrade (Optional)

- [ ] Replace some file handoffs with A2A messages
- [ ] Keep vault as audit record
- [ ] Real-time notifications

### Phase 3: Production Hardening

- [ ] Enhanced monitoring (Prometheus)
- [ ] Alerting (PagerDuty/Slack)
- [ ] Load balancing
- [ ] Multi-region deployment

---

## Resources

### Documentation
- 📖 [Main README](../README.md)
- 📖 [Gold Tier Checklist](../GOLD_TIER_CHECKLIST.md)
- 📖 [Hackathon Document](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)

### External Links
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [Docker Documentation](https://docs.docker.com/)
- [Git Documentation](https://git-scm.com/docs)

### Support Commands
```bash
# Run demo
python platinum/demo_flow.py --vault ./AI_Employee_Vault

# Cloud Agent status
docker-compose ps
docker-compose logs -f cloud-agent

# Local Agent status
python -m platinum.local_agent.main --git-remote $GIT_REMOTE --status
```

---

*Platinum Tier: Production-Ready AI Employee*
*Hackathon 0: Building Autonomous FTEs in 2026*
