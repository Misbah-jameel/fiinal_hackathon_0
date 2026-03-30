#!/bin/bash
# Odoo Backup Script
# Platinum Tier: Always-On Cloud Executive

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/backups/odoo}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-odoo}"
DB_CONTAINER="${DB_CONTAINER:-ai-employee-db}"
ODOO_DATA_CONTAINER="${ODOO_DATA_CONTAINER:-ai-employee-odoo}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create backup directory
mkdir -p $BACKUP_DIR

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

log_info "Starting Odoo backup..."
log_info "Backup directory: $BACKUP_DIR"

# Backup PostgreSQL database
log_info "Backing up PostgreSQL database..."
docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_$TIMESTAMP.sql

if [ $? -eq 0 ]; then
    log_info "Database backup successful: db_$TIMESTAMP.sql"
else
    log_warn "Database backup failed!"
fi

# Backup Odoo filestore
log_info "Backing up Odoo filestore..."
docker exec $ODOO_DATA_CONTAINER tar -czf /tmp/odoo_filestore_$TIMESTAMP.tar.gz /var/lib/odoo
docker cp $ODOO_DATA_CONTAINER:/tmp/odoo_filestore_$TIMESTAMP.tar.gz $BACKUP_DIR/
docker exec $ODOO_DATA_CONTAINER rm /tmp/odoo_filestore_$TIMESTAMP.tar.gz

if [ $? -eq 0 ]; then
    log_info "Filestore backup successful: odoo_filestore_$TIMESTAMP.tar.gz"
else
    log_warn "Filestore backup failed!"
fi

# Backup Docker volumes (optional, for complete backup)
log_info "Backing up Docker volumes..."
docker run --rm \
    -v $(docker volume ls -q -f name=ai-employee)://data:ro \
    -v $BACKUP_DIR:/backup \
    alpine tar -czf /backup/volumes_$TIMESTAMP.tar.gz /data

# Cleanup old backups
log_info "Cleaning up backups older than $RETENTION_DAYS days..."
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Show backup size
BACKUP_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
log_info "Total backup size: $BACKUP_SIZE"

# List recent backups
log_info "Recent backups:"
ls -lht $BACKUP_DIR | head -5

log_info "Backup completed successfully!"
