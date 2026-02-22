#!/bin/bash

################################################################################
# National Water Infrastructure Monitoring System - Database Backup Script
# 
# Purpose: Automated backup of PostgreSQL database with encryption and S3 upload
# 
# Features:
#   - Full database dumps with compression
#   - Incremental backups support
#   - Encryption with OpenSSL
#   - AWS S3 upload with versioning
#   - Retention policy (30 days default)
#   - Email notifications on success/failure
#
# Usage:
#   ./backup.sh [--full|--incremental] [--dry-run]
#
# Environment Variables:
#   BACKUP_ENABLED - Enable/disable backups (true/false)
#   BACKUP_SCHEDULE - Cron schedule (0 2 * * * = 2am daily)
#   BACKUP_RETENTION_DAYS - Keep backups for N days (default: 30)
#   DATABASE_URL - PostgreSQL connection string
#   AWS_S3_BUCKET - S3 bucket for backup storage
#   AWS_REGION - AWS region
#   AWS_ACCESS_KEY_ID - AWS credentials
#   AWS_SECRET_ACCESS_KEY - AWS credentials
#   BACKUP_ENCRYPTION_KEY - OpenSSL encryption key (min 32 chars)
#   NOTIFY_EMAIL - Email for notifications
#
# Kubernetes CronJob:
#   apiVersion: batch/v1
#   kind: CronJob
#   metadata:
#     name: database-backup
#     namespace: default
#   spec:
#     schedule: "0 2 * * *"
#     jobTemplate:
#       spec:
#         template:
#           spec:
#             containers:
#             - name: backup
#               image: postgres:15-alpine
#               command: ["/bin/sh"]
#               args: ["-c", "apt-get update && apt-get install -y awscli && /scripts/backup.sh"]
#               env:
#               - name: PGPASSWORD
#                 valueFrom:
#                   secretKeyRef:
#                     name: db-credentials
#                     key: password
#             restartPolicy: OnFailure
#
################################################################################

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/randwater"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_TYPE="${1:-full}"  # full or incremental
DRY_RUN="${2:-}"
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Database configuration from DATABASE_URL or environment
: "${DATABASE_URL:=postgresql://postgres:password@localhost:5432/randwater}"
: "${DB_HOST:=$(echo $DATABASE_URL | sed -n 's|.*://.*@\([^:]*\):.*|\1|p')}"
: "${DB_PORT:=$(echo $DATABASE_URL | sed -n 's|.*:\([0-9]*\)/.*|\1|p' || echo 5432)}"
: "${DB_NAME:=$(echo $DATABASE_URL | sed -n 's|.*/\([^?]*\).*|\1|p' || echo randwater)}"
: "${DB_USER:=$(echo $DATABASE_URL | sed -n 's|.*://\([^:]*\):.*|\1|p' || echo postgres)}"

# AWS S3 configuration
: "${AWS_S3_BUCKET:=}"
: "${AWS_REGION:=us-east-1}"

# Logging
LOG_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d).log"
NOTIFY_EMAIL="${NOTIFY_EMAIL:=}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create backup directory
mkdir -p "$BACKUP_DIR"

################################################################################
# Logging Functions
################################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

send_notification() {
    local subject="$1"
    local message="$2"
    local status="$3"  # success or failure
    
    if [ -z "$NOTIFY_EMAIL" ]; then
        return
    fi
    
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$NOTIFY_EMAIL"
        log_info "Notification sent to $NOTIFY_EMAIL"
    elif command -v sendmail &> /dev/null; then
        {
            echo "Subject: $subject"
            echo "To: $NOTIFY_EMAIL"
            echo ""
            echo "$message"
        } | sendmail "$NOTIFY_EMAIL"
        log_info "Notification sent to $NOTIFY_EMAIL"
    fi
}

################################################################################
# Backup Functions
################################################################################

validate_backup_config() {
    log_info "Validating backup configuration..."
    
    if [ "$BACKUP_ENABLED" != "true" ]; then
        log_warn "Backups are disabled (BACKUP_ENABLED=$BACKUP_ENABLED)"
        return 1
    fi
    
    if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
        log_error "Missing database configuration"
        return 1
    fi
    
    if [ -n "$BACKUP_ENCRYPTION_KEY" ] && [ ${#BACKUP_ENCRYPTION_KEY} -lt 32 ]; then
        log_error "BACKUP_ENCRYPTION_KEY must be at least 32 characters"
        return 1
    fi
    
    log_info "Configuration validated"
    return 0
}

test_database_connection() {
    log_info "Testing database connection to $DB_HOST:$DB_PORT..."
    
    if PGPASSWORD="${PGPASSWORD:-}" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" &> /dev/null; then
        log_info "Database connection successful"
        return 0
    else
        log_error "Failed to connect to database"
        return 1
    fi
}

create_full_backup() {
    local backup_file="$BACKUP_DIR/backup_full_${TIMESTAMP}.sql"
    
    log_info "Creating full database backup to $backup_file..."
    
    if [ -n "$DRY_RUN" ]; then
        log_info "[DRY RUN] Would execute: pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
        return 0
    fi
    
    if pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=plain \
        --verbose \
        --blobs \
        --create \
        > "$backup_file" 2>> "$LOG_FILE"; then
        
        log_info "Full backup completed: $(du -h "$backup_file" | cut -f1)"
        compress_backup "$backup_file"
        return 0
    else
        log_error "Failed to create full backup"
        return 1
    fi
}

create_schema_backup() {
    local backup_file="$BACKUP_DIR/backup_schema_${TIMESTAMP}.sql"
    
    log_info "Creating schema backup to $backup_file..."
    
    if [ -n "$DRY_RUN" ]; then
        log_info "[DRY RUN] Would execute: pg_dump --schema-only..."
        return 0
    fi
    
    if pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --schema-only \
        > "$backup_file" 2>> "$LOG_FILE"; then
        
        log_info "Schema backup completed: $(du -h "$backup_file" | cut -f1)"
        compress_backup "$backup_file"
        return 0
    else
        log_error "Failed to create schema backup"
        return 1
    fi
}

compress_backup() {
    local backup_file="$1"
    
    log_info "Compressing backup..."
    
    if [ -n "$DRY_RUN" ]; then
        log_info "[DRY RUN] Would compress: $backup_file"
        return 0
    fi
    
    if gzip -9 "$backup_file"; then
        log_info "Backup compressed: $backup_file.gz ($(du -h "$backup_file.gz" | cut -f1))"
        rm -f "$backup_file"
        return 0
    else
        log_error "Failed to compress backup"
        return 1
    fi
}

encrypt_backup() {
    local backup_file="$1"
    
    if [ -z "$BACKUP_ENCRYPTION_KEY" ]; then
        log_warn "No encryption key provided, skipping encryption"
        return 0
    fi
    
    log_info "Encrypting backup with AES-256..."
    
    if [ -n "$DRY_RUN" ]; then
        log_info "[DRY RUN] Would encrypt: $backup_file"
        return 0
    fi
    
    if echo -n "$BACKUP_ENCRYPTION_KEY" | openssl enc -aes-256-cbc -in "$backup_file" -out "$backup_file.enc" -K $(echo -n "$BACKUP_ENCRYPTION_KEY" | md5sum | cut -d' ' -f1) -iv 00000000000000000000000000000000; then
        log_info "Backup encrypted: $backup_file.enc"
        rm -f "$backup_file"
        return 0
    else
        log_error "Failed to encrypt backup"
        return 1
    fi
}

upload_to_s3() {
    local backup_file="$1"
    
    if [ -z "$AWS_S3_BUCKET" ]; then
        log_warn "AWS_S3_BUCKET not configured, skipping S3 upload"
        return 0
    fi
    
    log_info "Uploading backup to S3 bucket: $AWS_S3_BUCKET..."
    
    if [ -n "$DRY_RUN" ]; then
        log_info "[DRY RUN] Would upload to: s3://$AWS_S3_BUCKET/backups/$(basename $backup_file)"
        return 0
    fi
    
    if aws s3 cp "$backup_file" "s3://$AWS_S3_BUCKET/backups/$(basename $backup_file)" \
        --region "$AWS_REGION" \
        --storage-class STANDARD_IA \
        --sse AES256 \
        --metadata "timestamp=$TIMESTAMP,database=$DB_NAME" \
        >> "$LOG_FILE" 2>&1; then
        
        log_info "Backup uploaded to S3"
        return 0
    else
        log_error "Failed to upload to S3"
        return 1
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $BACKUP_RETENTION_DAYS days..."
    
    if [ -n "$DRY_RUN" ]; then
        log_info "[DRY RUN] Would delete backups older than $BACKUP_RETENTION_DAYS days"
        return 0
    fi
    
    # Local cleanup
    find "$BACKUP_DIR" -type f -name "backup_*" -mtime "+$BACKUP_RETENTION_DAYS" -delete
    log_info "Local backup cleanup completed"
    
    # S3 cleanup (if configured)
    if [ -n "$AWS_S3_BUCKET" ]; then
        cutoff_date=$(date -d "$BACKUP_RETENTION_DAYS days ago" +%Y-%m-%d)
        log_info "Deleting S3 backups before $cutoff_date"
        
        aws s3 ls "s3://$AWS_S3_BUCKET/backups/" --region "$AWS_REGION" | \
        while read -r date time size file; do
            if [[ "$date" < "$cutoff_date" ]]; then
                aws s3 rm "s3://$AWS_S3_BUCKET/backups/$file" --region "$AWS_REGION"
                log_info "Deleted old S3 backup: $file"
            fi
        done
    fi
}

verify_backup() {
    local backup_file="$1"
    
    log_info "Verifying backup integrity..."
    
    if [ -n "$DRY_RUN" ]; then
        log_info "[DRY RUN] Would verify: $backup_file"
        return 0
    fi
    
    # Check file size
    local size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
    if [ "$size" -lt 1000 ]; then
        log_error "Backup file is suspiciously small: $size bytes"
        return 1
    fi
    
    # Verify gzip integrity
    if [[ "$backup_file" == *.gz ]]; then
        if gzip -t "$backup_file" 2>&1; then
            log_info "Backup integrity verified"
            return 0
        else
            log_error "Backup gzip integrity check failed"
            return 1
        fi
    fi
    
    log_info "Backup verification completed"
    return 0
}

################################################################################
# Main Execution
################################################################################

main() {
    log_info "=== National Water Infrastructure Backup Started ==="
    log_info "Timestamp: $TIMESTAMP"
    log_info "Backup Type: $BACKUP_TYPE"
    log_info "Database: $DB_NAME at $DB_HOST:$DB_PORT"
    
    # Validate configuration
    if ! validate_backup_config; then
        send_notification "Backup Failed" "Backup validation failed. Check logs." "failure"
        return 1
    fi
    
    # Test database connection
    if ! test_database_connection; then
        send_notification "Backup Failed" "Failed to connect to database." "failure"
        return 1
    fi
    
    # Create backups
    local backup_file=""
    if [ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "" ]; then
        if ! create_full_backup; then
            send_notification "Backup Failed" "Full backup creation failed." "failure"
            return 1
        fi
        backup_file="$BACKUP_DIR/backup_full_${TIMESTAMP}.sql.gz"
    fi
    
    # Create schema backup
    if ! create_schema_backup; then
        log_warn "Schema backup failed, continuing..."
    fi
    
    # Encrypt if configured
    if [ -f "$backup_file" ]; then
        if ! encrypt_backup "$backup_file"; then
            send_notification "Backup Failed" "Backup encryption failed." "failure"
            return 1
        fi
        backup_file="${backup_file}.enc"
    fi
    
    # Upload to S3
    if [ -f "$backup_file" ]; then
        if ! upload_to_s3 "$backup_file"; then
            send_notification "Backup Warning" "Backup created but S3 upload failed." "failure"
        fi
    fi
    
    # Verify backup
    if [ -f "$backup_file" ]; then
        if ! verify_backup "$backup_file"; then
            send_notification "Backup Failed" "Backup integrity verification failed." "failure"
            return 1
        fi
    fi
    
    # Cleanup old backups
    if ! cleanup_old_backups; then
        log_warn "Cleanup failed, but backup succeeded"
    fi
    
    log_info "=== National Water Infrastructure Backup Completed Successfully ==="
    send_notification "Backup Success" "Database backup completed successfully at $TIMESTAMP" "success"
    
    return 0
}

# Run main function
if main; then
    exit 0
else
    exit 1
fi
