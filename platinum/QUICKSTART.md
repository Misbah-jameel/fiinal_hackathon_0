# Platinum Tier Quick Start Guide

> **Status:** ✅ **COMPLETE & TESTED**
> **Demo:** Successfully ran end-to-end workflow

---

## What Was Built

Complete Platinum Tier implementation with:

- **Cloud Agent** (24/7 VM) - Draft creation only
- **Local Agent** (Your PC) - Approval + Execution
- **Git Vault Sync** - Secure synchronization
- **Demo Flow** - End-to-end testing

---

## Quick Commands

### 1. Run Demo (Test Installation)

```bash
cd D:\fiinal_hackathon_0

# Run Platinum demo (simulates full workflow)
python platinum\demo_flow.py --vault ./AI_Employee_Vault
```

**Expected Output:**
```
============================================================
PLATINUM TIER DEMO - End-to-End Workflow
============================================================
...
DEMO COMPLETE! ✅
```

### 2. Verify Files Created

```bash
# Check demo files
dir AI_Employee_Vault\Platinum_Demo
dir AI_Employee_Vault\Signals
dir AI_Employee_Vault\Done
```

### 3. Test Cloud Agent Module

```bash
# Test Cloud Agent imports
python -c "from platinum.cloud_agent import config, watcher, drafter, sync_client; print('✅ Cloud Agent modules OK')"

# Test Local Agent imports
python -c "from platinum.local_agent import config, approver, executor, notifier, sync_client; print('✅ Local Agent modules OK')"

# Test Sync modules
python -c "from platinum.sync import vault_sync, conflict_resolver, encryption; print('✅ Sync modules OK')"
```

---

## Deployment Options

### Option A: Test Locally (Development)

Run both Cloud and Local agents on your machine for testing:

```bash
# Terminal 1: Cloud Agent (simulated)
python platinum\cloud_agent\main.py --git-remote "https://github.com/test/test.git" --demo --vault-path ./AI_Employee_Vault

# Terminal 2: Local Agent
python platinum\local_agent\main.py --git-remote "https://github.com/test/test.git" --demo --vault-path ./AI_Employee_Vault
```

### Option B: Deploy to Cloud VM (Production)

#### Step 1: Create Cloud VM

**Oracle Cloud Free Tier:**
1. Go to https://www.oracle.com/cloud/free/
2. Create account
3. Create VM:
   - Image: Ubuntu 22.04
   - Shape: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM - Free)
   - Region: Closest to you

#### Step 2: Setup VM

```bash
# SSH into VM
ssh ubuntu@<vm-ip>

# Run setup script
curl -O https://raw.githubusercontent.com/yourusername/ai-employee/main/platinum/deploy/setup_cloud_vm.sh
chmod +x setup_cloud_vm.sh

# Set your Git remote
export GIT_REMOTE="https://github.com/yourusername/ai-employee-vault.git"
./setup_cloud_vm.sh
```

#### Step 3: Configure & Start

```bash
# Edit .env with credentials
cd ai-employee
nano .env

# Start services
cd platinum/deploy
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f cloud-agent
```

### Option C: Local Agent Only (Hybrid)

Run Local Agent on your PC, sync with Git repo:

```bash
# 1. Create Git repo for vault
# GitHub/GitLab/Bitbucket - private repo recommended

# 2. Initialize Local Agent
export GIT_REMOTE="https://github.com/yourusername/ai-employee-vault.git"
python platinum\local_agent\main.py --git-remote $GIT_REMOTE --init-only --vault-path ./AI_Employee_Vault

# 3. Start Local Agent
python platinum\local_agent\main.py --git-remote $GIT_REMOTE --vault-path ./AI_Employee_Vault
```

---

## Configuration

### Cloud Agent (.env on VM)

```bash
# Required
GIT_REMOTE=https://github.com/yourusername/ai-employee-vault.git
VAULT_PATH=/home/ubuntu/AI_Employee_Vault
AGENT_ID=cloud_agent

# Optional
LOG_LEVEL=INFO
SYNC_INTERVAL=60
GMAIL_CHECK_INTERVAL=120
SOCIAL_CHECK_INTERVAL=300

# API Credentials (for monitoring/drafting only)
GMAIL_CLIENT_ID=xxx
GMAIL_CLIENT_SECRET=xxx
TWITTER_API_KEY=xxx
FACEBOOK_ACCESS_TOKEN=xxx
```

### Local Agent (.env on your PC)

```bash
# Required
GIT_REMOTE=https://github.com/yourusername/ai-employee-vault.git
VAULT_PATH=./AI_Employee_Vault
AGENT_ID=local_agent

# Security (IMPORTANT)
DRY_RUN=true
REQUIRE_APPROVAL_PAYMENTS=true
REQUIRE_APPROVAL_NEW_CONTACTS=true

# Notifications
DESKTOP_NOTIFICATIONS=true
NOTIFICATION_SOUND=true

# NEVER SYNC THESE
# Keep these only on Local:
GMAIL_CREDENTIALS=./.secrets/credentials.json
WHATSAPP_SESSION_PATH=./whatsapp_session
```

---

## Architecture Recap

```
┌─────────────────────────────────────────┐
│         CLOUD VM (24/7)                 │
│  ┌──────────────────────────────────┐   │
│  │ Cloud Agent                      │   │
│  │ • Gmail Watcher (draft only)     │   │
│  │ • Social Watcher (draft only)    │   │
│  │ • Lead Capture (draft only)      │   │
│  │ • Cloud Drafter (Claude Code)    │   │
│  └──────────────────────────────────┘   │
│           ↕ Git Sync ↕                  │
└─────────────────────────────────────────┘
                   ↕
         (Secrets NEVER sync)
                   ↕
┌─────────────────────────────────────────┐
│      LOCAL PC (Your Machine)            │
│  ┌──────────────────────────────────┐   │
│  │ Local Agent                      │   │
│  │ • Approver (HITL workflow)       │   │
│  │ • Executor (MCP access)          │   │
│  │ • Notifier (Desktop alerts)      │   │
│  │ • Sync Client (Git pull/push)    │   │
│  └──────────────────────────────────┘   │
│                                         │
│  Secrets: .env, tokens, WhatsApp        │
└─────────────────────────────────────────┘
```

---

## Security Checklist

- [ ] `.env` file in `.gitignore`
- [ ] Credentials only in Local Agent
- [ ] WhatsApp session local only
- [ ] Banking tokens local only
- [ ] Git remote is private repository
- [ ] DRY_RUN=true for testing
- [ ] Approval required for payments
- [ ] Rate limits configured

---

## Troubleshooting

### Demo Fails

```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip install -r requirements.txt

# Run with verbose logging
python platinum\demo_flow.py --vault ./AI_Employee_Vault --speed 1.0
```

### Import Errors

```bash
# Install Platinum dependencies
pip install -r platinum\deploy\requirements-platinum.txt

# Or install individually
pip install cryptography GitPython psutil
```

### Git Sync Issues

```bash
# Check Git configuration
cd AI_Employee_Vault
git status
git remote -v

# Test manual pull
git pull origin main

# Reset if needed
git reset --hard origin/main
```

---

## Next Steps

### Immediate (Test & Validate)

1. ✅ Run demo flow
2. ✅ Test module imports
3. ✅ Configure Git remote
4. ✅ Test Local Agent

### Short Term (Deploy Cloud)

1. Create Oracle Cloud VM
2. Run setup script
3. Configure .env
4. Start Cloud Agent
5. Verify sync

### Long Term (Production)

1. Configure all API credentials
2. Set up monitoring
3. Enable HTTPS
4. Configure backups
5. Set up alerting

---

## Resources

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Full Platinum documentation |
| [demo_flow.py](demo_flow.py) | End-to-end demo script |
| [../README.md](../README.md) | Main project README |
| [../GOLD_TIER_CHECKLIST.md](../GOLD_TIER_CHECKLIST.md) | Gold Tier reference |

---

## Support Commands

```bash
# Run demo
python platinum\demo_flow.py --vault ./AI_Employee_Vault

# Test Cloud Agent
python -c "from platinum.cloud_agent.main import CloudAgent; print('OK')"

# Test Local Agent
python -c "from platinum.local_agent.main import LocalAgent; print('OK')"

# Check vault structure
tree AI_Employee_Vault /F

# View demo logs
type AI_Employee_Vault\Platinum_Demo\*.log
```

---

**Platinum Tier: Production-Ready AI Employee** ✅

*Built for Hackathon 0: Building Autonomous FTEs in 2026*
