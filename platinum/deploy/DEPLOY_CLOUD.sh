# ===========================================
# Oracle Cloud VM - AI Employee Deployment
# ===========================================
# Run this on Oracle Cloud VM (Ubuntu 22.04)
# ===========================================

#!/bin/bash
set -e

echo "========================================="
echo "AI Employee - Cloud VM Deployment"
echo "Platinum Tier - Published"
echo "========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PROJECT_DIR="/home/ubuntu/ai-employee"
VAULT_DIR="/home/ubuntu/AI_Employee_Vault"

# ===========================================
# Step 1: Update System
# ===========================================
log_info "Step 1: Updating system..."
sudo apt update && sudo apt upgrade -y

# ===========================================
# Step 2: Install Docker
# ===========================================
log_info "Step 2: Installing Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# ===========================================
# Step 3: Install Docker Compose
# ===========================================
log_info "Step 3: Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# ===========================================
# Step 4: Install Git & Python
# ===========================================
log_info "Step 4: Installing dependencies..."
sudo apt install -y git python3.11 python3-pip nodejs npm

# ===========================================
# Step 5: Clone Repository
# ===========================================
log_info "Step 5: Cloning repository..."

# Ask for repository URL
echo ""
echo "Enter your GitHub repository URL:"
echo "Example: https://github.com/yourusername/ai-employee.git"
read -p "> " REPO_URL

if [ -d "$PROJECT_DIR" ]; then
    log_warn "Directory exists, pulling latest..."
    cd $PROJECT_DIR
    git pull
else
    if [ -z "$REPO_URL" ]; then
        log_error "No repository URL provided"
        exit 1
    fi
    git clone $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
fi

# ===========================================
# Step 6: Configure Environment
# ===========================================
log_info "Step 6: Configuring environment..."
cd $PROJECT_DIR

# Create .env from example
if [ -f ".env.example" ]; then
    cp .env.example .env
fi

# Create vault directory
mkdir -p $VAULT_DIR

# ===========================================
# Step 7: Configure .env
# ===========================================
log_info "Step 7: Editing .env..."

cat > .env << 'EOF'
# ===========================================
# AI Employee - Cloud VM Configuration
# ===========================================

# Cloud Agent Settings
AGENT_ID=cloud_agent
VAULT_PATH=/home/ubuntu/AI_Employee_Vault
LOCAL_ONLY=false

# Security (IMPORTANT!)
DRY_RUN=true
REQUIRE_APPROVAL_PAYMENTS=true
REQUIRE_APPROVAL_NEW_CONTACTS=true

# Sync Settings
SYNC_INTERVAL=60
GMAIL_CHECK_INTERVAL=120
SOCIAL_CHECK_INTERVAL=300

# API Credentials (Add your credentials below)
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
TWITTER_API_KEY=
TWITTER_API_SECRET=
FACEBOOK_ACCESS_TOKEN=
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_ACCESS_TOKEN=

# Odoo ERP
ODOO_URL=http://odoo:8069
ODOO_DB=postgres
ODOO_USER=admin
ODOO_PASSWORD=odoo123

# Docker Settings
DOCKER_NETWORK=ai-employee-network
ODOO_DB_PASSWORD=odoo123
EOF

log_warn "IMPORTANT: Edit .env with your API credentials!"
echo "nano .env"

# ===========================================
# Step 8: Setup Firewall
# ===========================================
log_info "Step 8: Configuring firewall..."
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8069/tcp  # Odoo
sudo ufw --force enable

# ===========================================
# Step 9: Create Systemd Service
# ===========================================
log_info "Step 9: Creating systemd service..."

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

# ===========================================
# Step 10: Start Services
# ===========================================
log_info "Step 10: Starting services..."

cd $PROJECT_DIR/platinum/deploy
docker-compose up -d

# ===========================================
# Step 11: Verify Deployment
# ===========================================
log_info "Step 11: Verifying deployment..."

sleep 10

echo ""
echo "========================================="
echo "Deployment Status"
echo "========================================="
docker-compose ps

echo ""
echo "========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "Services:"
echo "  • Cloud Agent: Running"
echo "  • Odoo ERP: http://$(curl -s http://169.254.169.254/opc/v1/instance/publicIp 2>/dev/null || echo 'YOUR_VM_IP'):8069"
echo "  • PostgreSQL: Running"
echo "  • Redis: Running"
echo ""
echo "Next Steps:"
echo "  1. Edit .env with API credentials"
echo "  2. Restart: docker-compose restart"
echo "  3. View logs: docker-compose logs -f"
echo ""
echo "Management Commands:"
echo "  • Status: docker-compose ps"
echo "  • Logs: docker-compose logs -f"
echo "  • Restart: docker-compose restart"
echo "  • Stop: docker-compose down"
echo ""
