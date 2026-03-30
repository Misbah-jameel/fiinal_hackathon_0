# Cloud VM Deployment Guide - Platinum Tier

**Status:** Ready to Deploy
**Target:** Oracle Cloud Free Tier (Recommended) / AWS EC2 / DigitalOcean

---

## Quick Overview

| Step | Task | Time | Status |
|------|------|------|--------|
| 1 | Create Oracle Cloud Account | 10 min | ⏳ Pending |
| 2 | Create VM Instance | 5 min | ⏳ Pending |
| 3 | SSH into VM | 2 min | ⏳ Pending |
| 4 | Run Setup Script | 10 min | ⏳ Pending |
| 5 | Configure .env | 5 min | ⏳ Pending |
| 6 | Start Services | 5 min | ⏳ Pending |
| **Total** | | **~37 minutes** | |

---

## Step 1: Create Oracle Cloud Account

### 1.1 Sign Up
1. Visit: https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill in registration form
4. Verify email and phone
5. Add credit card (for verification only - won't be charged)

### 1.2 What You Get (Free Tier)
- **Compute VMs:**
  - Up to 4 ARM Ampere A1 Compute instances
  - 24 GB RAM total
  - 200 GB block volume total
- **Always Free:** No time limit, no charges

---

## Step 2: Create VM Instance

### 2.1 Create Instance
1. Login to Oracle Cloud Console
2. Navigate to: **Compute → Instances**
3. Click **Create Instance**

### 2.2 Configuration
```
Placement:
  - Compartment: [Your compartment]
  - Availability Domain: Any

Image and Shape:
  - Image: Oracle Linux 8.x / Ubuntu 22.04
  - Shape: VM.Standard.A1.Flex (ARM)
  - OCPUs: 4
  - Memory: 24 GB

Networking:
  - Virtual Cloud Network: [Default]
  - Subnet: [Default]
  - Assign Public IPv4 Address: ✓ YES

SSH Keys:
  - Generate a key pair OR upload your public key
  - Download private key (.ssh/id_rsa)
```

### 2.3 Boot Volume
```
Size: 200 GB (maximum free tier)
```

### 2.4 Create
- Click **Create**
- Wait 2-3 minutes for VM to provision
- Note the **Public IP Address**

---

## Step 3: SSH into VM

### 3.1 Prepare SSH Key
```bash
# If you generated a new key, download it
# Save as: ~/.ssh/oracle_cloud_key

# Set correct permissions
chmod 400 ~/.ssh/oracle_cloud_key
```

### 3.2 Connect to VM
```bash
# For Oracle Linux:
ssh -i ~/.ssh/oracle_cloud_key opc@<YOUR_VM_IP>

# For Ubuntu:
ssh -i ~/.ssh/oracle_cloud_key ubuntu@<YOUR_VM_IP>
```

### 3.3 First Login
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Git (if not installed)
sudo apt install -y git
```

---

## Step 4: Run Setup Script

### 4.1 Clone Repository
```bash
# Clone your AI Employee repository
git clone https://github.com/YOUR_USERNAME/ai-employee.git
cd ai-employee
```

### 4.2 Run Setup Script
```bash
# Navigate to deployment directory
cd platinum/deploy

# Make script executable
chmod +x setup_cloud_vm.sh

# Set your Git remote URL (for vault sync)
export GIT_REMOTE="https://github.com/YOUR_USERNAME/ai-employee-vault.git"

# Run setup script
./setup_cloud_vm.sh
```

### 4.3 What the Script Does
- ✅ Installs Docker & Docker Compose
- ✅ Installs Python 3.11, Node.js 20
- ✅ Clones repository
- ✅ Sets up firewall (ports 80, 443, 22)
- ✅ Creates systemd service
- ✅ Sets up backup automation
- ✅ Configures health checks
- ✅ Sets up log rotation

---

## Step 5: Configure .env

### 5.1 Edit Environment File
```bash
cd /home/ubuntu/ai-employee
nano .env
```

### 5.2 Required Settings
```bash
# Git Vault Sync
GIT_REMOTE=https://github.com/YOUR_USERNAME/ai-employee-vault.git
VAULT_PATH=/home/ubuntu/AI_Employee_Vault
AGENT_ID=cloud_agent

# API Credentials (for monitoring/drafting)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
LINKEDIN_ACCESS_TOKEN=your_access_token

# Cloud Settings
LOG_LEVEL=INFO
SYNC_INTERVAL=60
GMAIL_CHECK_INTERVAL=120
SOCIAL_CHECK_INTERVAL=300

# Odoo
ODOO_DB_PASSWORD=odoo123
```

### 5.3 Save and Exit
```
# In nano:
Ctrl+O → Enter (save)
Ctrl+X (exit)
```

---

## Step 6: Start Services

### 6.1 Start Docker Compose
```bash
cd /home/ubuntu/ai-employee/platinum/deploy

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 6.2 Expected Output
```
NAME                     STATUS         PORTS
ai-employee-cloud        Up 10 seconds
ai-employee-odoo         Up 10 seconds  0.0.0.0:8069->8069/tcp
ai-employee-db           Up 10 seconds  5432/tcp
ai-employee-redis        Up 10 seconds  6379/tcp
```

### 6.3 View Logs
```bash
# Cloud Agent logs
docker-compose logs -f cloud-agent

# Odoo logs
docker-compose logs -f odoo

# All logs
docker-compose logs -f
```

---

## Verification Checklist

### ✅ VM Setup Complete
- [ ] SSH connection working
- [ ] System updated
- [ ] Git installed

### ✅ Docker Services Running
```bash
docker-compose ps
# All services should show "Up" status
```

### ✅ Vault Sync Configured
```bash
cd /home/ubuntu/AI_Employee_Vault
git status
# Should show "Your branch is up to date"
```

### ✅ Cloud Agent Running
```bash
docker-compose logs cloud-agent | tail -20
# Should show "Cloud Agent initialized successfully"
```

---

## Post-Deployment Tasks

### A. Configure Git Remote (Vault Sync)

```bash
# On your LOCAL machine (Windows):
cd D:\fiinal_hackathon_0\AI_Employee_Vault

# Add remote (GitHub/GitLab private repo)
git remote add origin https://github.com/YOUR_USERNAME/ai-employee-vault.git

# Push initial commit
git push -u origin master
```

```bash
# On CLOUD VM:
cd /home/ubuntu/AI_Employee_Vault

# Pull from remote
git pull origin master

# Verify files
ls -la
```

### B. Test Cloud → Local Sync

```bash
# On VM: Create a test file
cd /home/ubuntu/AI_Employee_Vault/Updates
echo "Test from Cloud" > test_cloud_$(date +%Y%m%d_%H%M%S).md

# Commit and push
git add .
git commit -m "Test from Cloud Agent"
git push origin master
```

```bash
# On LOCAL machine: Pull and verify
cd D:\fiinal_hackathon_0\AI_Employee_Vault
git pull origin master
ls Updates/
```

### C. Setup HTTPS (Optional)

```bash
# On VM: Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Enable HTTPS profile in firewall
sudo ufw allow 'Nginx Full'
```

---

## Monitoring & Maintenance

### Daily Checks
```bash
# Check service status
docker-compose ps

# View recent logs
docker-compose logs --tail=100 cloud-agent

# Check disk usage
df -h

# Check memory
free -h
```

### Weekly Tasks
```bash
# Restart services (if needed)
docker-compose restart

# Clean up old images
docker image prune -f

# Check for updates
cd /home/ubuntu/ai-employee
git pull origin master
docker-compose up -d
```

### Monthly Backups
```bash
# Run backup script
./odoo_backup.sh

# Verify backups
ls -lh /home/ubuntu/backups/odoo/
```

---

## Troubleshooting

### Issue: Docker Compose Fails
```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Try again
docker-compose up -d
```

### Issue: Git Sync Fails
```bash
# Check Git configuration
git remote -v
git status

# Test connection
git fetch origin

# Reset if needed
git reset --hard origin/master
```

### Issue: Cloud Agent Not Starting
```bash
# Check logs
docker-compose logs cloud-agent

# Restart service
docker-compose restart cloud-agent

# Check .env configuration
cat .env | grep GIT_REMOTE
```

### Issue: Can't SSH
```bash
# Check security list (Oracle Cloud Console)
# Ensure port 22 is open in ingress rules

# Check firewall
sudo ufw status

# Allow SSH if blocked
sudo ufw allow 22/tcp
```

---

## Cost Estimate

### Oracle Cloud Free Tier: $0/month

| Resource | Usage | Cost |
|----------|-------|------|
| Compute VM (4 OCPU, 24GB) | Always Free | $0 |
| Block Volume (200GB) | Always Free | $0 |
| Data Transfer | 10TB/month | $0 |
| **Total** | | **$0** |

---

## Next Steps After Deployment

1. ✅ **Verify Cloud Agent is running**
2. ✅ **Test Git sync between Cloud and Local**
3. ✅ **Configure API credentials**
4. ✅ **Test draft creation workflow**
5. ✅ **Monitor for 24 hours**

---

## Support Commands

### Cloud VM
```bash
# Start services
cd /home/ubuntu/ai-employee/platinum/deploy
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f cloud-agent

# Check status
docker-compose ps
```

### Local Machine
```bash
# Pull latest from Cloud
cd D:\fiinal_hackathon_0\AI_Employee_Vault
git pull origin master

# Push changes to Cloud
git push origin master
```

---

**Deployment Guide Complete!** 🎉

*Ready to deploy to Oracle Cloud Free Tier*
