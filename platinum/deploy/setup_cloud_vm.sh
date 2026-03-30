#!/bin/bash
# Cloud VM Setup Script
# Platinum Tier: Always-On Cloud Executive
# Target: Oracle Cloud Free Tier / AWS EC2 / DigitalOcean

set -e

echo "========================================="
echo "AI Employee - Cloud VM Setup"
echo "Platinum Tier"
echo "========================================="

# Configuration
GIT_REMOTE="${GIT_REMOTE:-}"
VAULT_PATH="${VAULT_PATH:-/home/ubuntu/AI_Employee_Vault}"
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/ai-employee}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please do not run as root"
    exit 1
fi

# Step 1: Update system
log_info "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Docker
log_info "Step 2: Installing Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Step 3: Install Docker Compose
log_info "Step 3: Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Step 4: Install Git
log_info "Step 4: Installing Git..."
sudo apt install -y git

# Step 5: Install Python
log_info "Step 5: Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip

# Step 6: Install Node.js
log_info "Step 6: Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Step 7: Clone repository
log_info "Step 7: Cloning repository..."
if [ -d "$PROJECT_DIR" ]; then
    log_warn "Project directory exists, pulling latest..."
    cd $PROJECT_DIR
    git pull
else
    if [ -z "$GIT_REMOTE" ]; then
        log_error "GIT_REMOTE not set. Please export GIT_REMOTE=<your-repo-url>"
        exit 1
    fi
    git clone $GIT_REMOTE $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Step 8: Setup environment
log_info "Step 8: Setting up environment..."
cd $PROJECT_DIR

if [ -f ".env.example" ]; then
    cp .env.example .env
    log_warn "Please edit .env with your credentials"
fi

# Create vault directory
mkdir -p $VAULT_PATH

# Step 9: Setup SSL (optional)
log_info "Step 9: Setting up SSL (optional)..."
if [ "${ENABLE_SSL:-false}" = "true" ]; then
    sudo apt install -y certbot python3-certbot-nginx
    
    if [ -n "${DOMAIN_NAME:-}" ]; then
        sudo certbot --nginx -d $DOMAIN_NAME
    else
        log_warn "DOMAIN_NAME not set, skipping SSL setup"
    fi
fi

# Step 10: Setup firewall
log_info "Step 10: Configuring firewall..."
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Step 11: Setup monitoring
log_info "Step 11: Installing monitoring tools..."
sudo apt install -y htop iotop

# Step 12: Setup log rotation
log_info "Step 12: Configuring log rotation..."
sudo tee /etc/logrotate.d/ai-employee > /dev/null <<EOF
/var/log/ai-employee/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
}
EOF

# Step 13: Create systemd service
log_info "Step 13: Creating systemd service..."
sudo tee /etc/systemd/system/ai-employee-cloud.service > /dev/null <<EOF
[Unit]
Description=AI Employee Cloud Agent
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR/platinum/deploy
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ai-employee-cloud

# Step 14: Setup backup script
log_info "Step 14: Creating backup script..."
mkdir -p /home/ubuntu/backups

cat > /home/ubuntu/backups/backup-odoo.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups/odoo"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup Odoo database
docker exec ai-employee-db pg_dump -U odoo postgres > $BACKUP_DIR/db_$DATE.sql

# Backup Odoo data
tar -czf $BACKUP_DIR/odoo_data_$DATE.tar.gz /var/lib/odoo

# Keep only last 7 backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backups/backup-odoo.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backups/backup-odoo.sh") | crontab -

# Step 15: Setup health check script
log_info "Step 15: Creating health check script..."
cat > /home/ubuntu/health-check.sh <<'EOF'
#!/bin/bash
# Health check for AI Employee Cloud

# Check Docker containers
if ! docker ps | grep -q ai-employee-cloud; then
    echo "Cloud Agent container is down, restarting..."
    cd /home/ubuntu/ai-employee/platinum/deploy
    docker-compose restart cloud-agent
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "WARNING: Disk usage above 90%"
    # Send alert (implement your alerting mechanism)
fi

# Check memory
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2*100.0)}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "WARNING: Memory usage above 90%"
fi
EOF

chmod +x /home/ubuntu/health-check.sh

# Add health check to crontab (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/health-check.sh") | crontab -

# Final steps
echo ""
log_info "========================================="
log_info "Setup Complete!"
log_info "========================================="
echo ""
log_info "Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   cd $PROJECT_DIR && nano .env"
echo ""
echo "2. Configure Git remote for vault sync:"
echo "   export GIT_REMOTE=<your-git-repo-url>"
echo ""
echo "3. Start the Cloud Agent:"
echo "   sudo systemctl start ai-employee-cloud"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status ai-employee-cloud"
echo "   docker-compose ps"
echo ""
echo "5. View logs:"
echo "   docker-compose logs -f cloud-agent"
echo ""
log_warn "IMPORTANT: Configure your .env file before starting!"
echo ""

# Print summary
log_info "Installation Summary:"
echo "- Docker: $(docker --version)"
echo "- Docker Compose: $(docker-compose --version)"
echo "- Python: $(python3 --version)"
echo "- Node.js: $(node --version)"
echo "- Git: $(git --version)"
echo ""
log_info "Vault path: $VAULT_PATH"
log_info "Project directory: $PROJECT_DIR"
log_info "Backup directory: /home/ubuntu/backups"
