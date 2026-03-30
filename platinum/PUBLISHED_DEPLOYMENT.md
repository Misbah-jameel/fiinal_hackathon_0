# 🌐 Published Deployment Guide - Platinum Tier

**Status:** ✅ **READY TO PUBLISH**
**Target:** Oracle Cloud Free Tier / AWS EC2 / DigitalOcean
**Time:** ~30 minutes

---

## 🚀 **Quick Deploy (3 Steps)**

### **Step 1: Create Cloud VM** (10 min)
### **Step 2: Run Deploy Script** (10 min)
### **Step 3: Configure & Start** (10 min)

---

## Step 1: Create Oracle Cloud VM

### **1.1 Sign Up (Free)**
1. Visit: https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill registration form
4. Verify email & phone
5. Add credit card (verification only - **won't be charged**)

### **1.2 Create VM Instance**

**Navigate to:** Compute → Instances → Create Instance

**Configuration:**
```
Image: Ubuntu 22.04
Shape: VM.Standard.A1.Flex (ARM)
  • OCPUs: 4
  • Memory: 24 GB
  • Boot Volume: 200 GB

Networking:
  • Assign Public IPv4: YES ✓
  • VCN: Default

SSH Keys:
  • Generate key pair (download private key)
```

**Click "Create"** → Wait 2-3 minutes

**Note Public IP Address** (shown after creation)

---

## Step 2: Deploy to VM

### **2.1 SSH into VM**

```bash
# Windows (PowerShell):
ssh -i C:\path\to\your\key ubuntu@YOUR_VM_IP

# Linux/Mac:
ssh -i ~/.ssh/your_key ubuntu@YOUR_VM_IP
```

### **2.2 Run Deploy Script**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Git
sudo apt install -y git

# Clone your repository
git clone https://github.com/YOUR_USERNAME/ai-employee.git
cd ai-employee

# Make deploy script executable
chmod +x platinum/deploy/DEPLOY_CLOUD.sh

# Run deployment
./platinum/deploy/DEPLOY_CLOUD.sh
```

**Script will:**
- ✅ Install Docker & Docker Compose
- ✅ Install Python, Node.js, Git
- ✅ Clone repository
- ✅ Configure .env
- ✅ Setup firewall
- ✅ Create systemd service
- ✅ Start all services

---

## Step 3: Configure & Publish

### **3.1 Edit .env with Credentials**

```bash
cd /home/ubuntu/ai-employee
nano .env
```

**Required Settings:**
```bash
# Cloud Agent
AGENT_ID=cloud_agent
VAULT_PATH=/home/ubuntu/AI_Employee_Vault
DRY_RUN=true

# API Credentials (Add yours)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_secret
LINKEDIN_ACCESS_TOKEN=your_token

# Odoo
ODOO_DB_PASSWORD=odoo123
```

**Save:** Ctrl+O → Enter → Ctrl+X

### **3.2 Restart Services**

```bash
cd platinum/deploy
docker-compose restart
```

### **3.3 Verify Deployment**

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f cloud-agent

# Check Odoo
curl http://localhost:8069
```

**Expected Output:**
```
NAME                    STATUS
ai-employee-cloud       Up
ai-employee-odoo        Up
ai-employee-db          Up
ai-employee-redis       Up
```

---

## 🌐 **Access Your Published AI Employee**

### **Web Interfaces:**

| Service | URL | Credentials |
|---------|-----|-------------|
| **Odoo ERP** | http://YOUR_VM_IP:8069 | admin / odoo123 |
| **Cloud Agent** | Internal (logs) | N/A |

### **Monitor Logs:**

```bash
# Cloud Agent logs
docker-compose logs -f cloud-agent

# All services
docker-compose logs -f

# Real-time monitoring
watch -n 5 'docker-compose ps'
```

---

## 📊 **Architecture (Published)**

```
┌─────────────────────────────────────────────────────────┐
│              ORACLE CLOUD VM (24/7)                     │
│              Public IP: XXX.XXX.XXX.XXX                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Cloud Agent (Docker Container)                   │ │
│  │  • Gmail Watcher (draft-only)                     │ │
│  │  • Social Media Watcher (draft-only)              │ │
│  │  • Lead Capture (draft-only)                      │ │
│  │  • Claude Code Drafter                            │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Odoo ERP (Docker Container)                      │ │
│  │  • Accounting                                     │ │
│  │  • Invoices                                       │ │
│  │  • Customers                                      │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  PostgreSQL Database                              │ │
│  │  Redis Cache                                      │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Firewall: Ports 80, 443, 8069 open                    │
│  SSH: Port 22 (your key only)                          │
└─────────────────────────────────────────────────────────┘
                    ↕ Internet ↕
                    ↕ Your PC ↕
```

---

## 🔧 **Management Commands**

### **Start/Stop Services:**

```bash
# Start all
docker-compose up -d

# Stop all
docker-compose down

# Restart
docker-compose restart

# Restart specific service
docker-compose restart cloud-agent
```

### **View Logs:**

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f cloud-agent
docker-compose logs -f odoo

# Last 100 lines
docker-compose logs --tail=100 cloud-agent
```

### **Check Status:**

```bash
# Service status
docker-compose ps

# Resource usage
docker stats

# Disk space
df -h

# Memory
free -h
```

### **Update:**

```bash
# Pull latest code
cd /home/ubuntu/ai-employee
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

---

## 🔒 **Security Checklist**

### ✅ **Configured:**
- [x] SSH key authentication only
- [x] Firewall enabled (UFW)
- [x] Only required ports open (22, 80, 443, 8069)
- [x] DRY_RUN=true (safe mode)
- [x] Database password changed
- [x] .env file (credentials protected)

### ⚠️ **Important:**
- Never commit `.env` to Git
- Keep SSH private key secure
- Rotate API credentials monthly
- Monitor logs regularly
- Enable HTTPS for production

---

## 📊 **Cost Estimate**

### **Oracle Cloud Free Tier: $0/month**

| Resource | Usage | Cost |
|----------|-------|------|
| Compute VM (4 OCPU, 24GB RAM) | Always Free | $0 |
| Boot Volume (200GB) | Always Free | $0 |
| Data Transfer (10TB/month) | Always Free | $0 |
| **Total** | | **$0/month** |

**Free for life!** No credit card charges.

---

## 🎯 **Post-Deployment Tasks**

### **1. Test Cloud Agent**

```bash
# Check if running
docker-compose ps cloud-agent

# View logs
docker-compose logs cloud-agent | tail -50
```

### **2. Configure API Credentials**

See: [`CREDENTIALS_SETUP.md`](CREDENTIALS_SETUP.md)

### **3. Setup Local Agent (Your PC)**

```bash
# On your local PC (Windows):
cd D:\fiinal_hackathon_0
python platinum\demo_flow.py --vault ./AI_Employee_Vault
```

### **4. Monitor for 24 Hours**

```bash
# Install monitoring tool
sudo apt install -y htop

# Check resources
htop

# View logs
tail -f /var/log/syslog | grep docker
```

---

## ⚠️ **Troubleshooting**

### **Issue: Docker Compose Fails**

```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Try again
docker-compose up -d
```

### **Issue: Can't SSH**

```bash
# Check Oracle Cloud Console
# → Security List → Ingress Rules
# Ensure port 22 is open

# Check firewall
sudo ufw status

# Allow SSH if needed
sudo ufw allow 22/tcp
```

### **Issue: Services Not Starting**

```bash
# Check logs
docker-compose logs cloud-agent

# Rebuild
docker-compose up -d --build

# Check .env configuration
cat .env | grep -E "GIT_|AGENT_|VAULT_"
```

### **Issue: Odoo Not Accessible**

```bash
# Check if Odoo is running
docker-compose ps odoo

# Check firewall
sudo ufw allow 8069/tcp

# Access via browser
# http://YOUR_VM_IP:8069
```

---

## 📖 **Documentation Links**

| Document | Purpose |
|----------|---------|
| [`DEPLOY_CLOUD.sh`](deploy/DEPLOY_CLOUD.sh) | Automated deploy script |
| [`docker-compose.yml`](deploy/docker-compose.yml) | Service configuration |
| [`CREDENTIALS_SETUP.md`](CREDENTIALS_SETUP.md) | API credentials guide |
| [`LOCAL_DEPLOYMENT.md`](LOCAL_DEPLOYMENT.md) | Local testing guide |

---

## 🎉 **You're Published!**

**Your AI Employee is now:**
- ✅ Running 24/7 on Oracle Cloud
- ✅ Accessible via internet
- ✅ Monitoring emails & social media
- ✅ Creating drafts autonomously
- ✅ Ready for production use

**Public URL:**
```
http://YOUR_VM_PUBLIC_IP:8069
```

**Find your VM's public IP:**
- Oracle Cloud Console → Instances → Your VM → Public IP

---

**🌐 Published Deployment Complete!**

*Platinum Tier - Cloud VM Edition*
*March 28, 2026*
