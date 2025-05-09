#!/bin/bash
# Database backup script for CKAN Docker setup
# Usage: ./backup-db.sh [output_directory]

set -e

# Set default output directory if not provided
OUTPUT_DIR=${1:-./backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="ckan_db_backup_${TIMESTAMP}.dump"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Starting database backup process..."
echo "Using container name from docker-compose: ckan-docker-db-1"

# Get the PostgreSQL connection details from the environment
source ./.env.prod.secrets
source ./.env.prod.config
POSTGRES_USER=${POSTGRES_USER:-ckan}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-ckan}
CKAN_DB=${CKAN_DB:-ckan}
DATASTORE_DB=${DATASTORE_DB:-datastore}

# Perform database dump using docker compose exec
echo "Backing up main CKAN database..."
docker compose exec db pg_dump -U ${POSTGRES_USER} -F c -b -v -f "/tmp/${BACKUP_FILENAME}" ${CKAN_DB}

# Copy the dump file from the container to the host
echo "Copying backup file from container to host..."
docker compose cp "db:/tmp/${BACKUP_FILENAME}" "${OUTPUT_DIR}/${BACKUP_FILENAME}"

# If CKAN is using datastore, also backup that database
if grep -q "CKAN__PLUGINS.*datastore" .env; then
  DATASTORE_BACKUP_FILENAME="ckan_datastore_backup_${TIMESTAMP}.dump"
  echo "Backing up datastore database..."
  docker compose exec db pg_dump -U ${POSTGRES_USER} -F c -b -v -f "/tmp/${DATASTORE_BACKUP_FILENAME}" ${DATASTORE_DB}
  docker compose cp "db:/tmp/${DATASTORE_BACKUP_FILENAME}" "${OUTPUT_DIR}/${DATASTORE_BACKUP_FILENAME}"
fi

# Cleanup temp files in container
docker compose exec db rm -f "/tmp/${BACKUP_FILENAME}"
if grep -q "CKAN__PLUGINS.*datastore" .env; then
  docker compose exec db rm -f "/tmp/${DATASTORE_BACKUP_FILENAME}"
fi

# Backup PostgreSQL roles/users
echo "Backing up PostgreSQL roles/users..."
ROLES_BACKUP_FILENAME="postgres_roles_${TIMESTAMP}.sql"

# Export all roles with permissions
docker compose exec db pg_dumpall -U ${POSTGRES_USER} --roles-only > "${OUTPUT_DIR}/${ROLES_BACKUP_FILENAME}"

echo "Backup completed successfully!"
echo "Backup files saved to: ${OUTPUT_DIR}"
echo "  - ${OUTPUT_DIR}/${BACKUP_FILENAME}"
if grep -q "CKAN__PLUGINS.*datastore" .env; then
  echo "  - ${OUTPUT_DIR}/${DATASTORE_BACKUP_FILENAME}"
fi
echo "  - ${OUTPUT_DIR}/${ROLES_BACKUP_FILENAME}"

# Print restore instructions
echo ""
echo "To restore this backup, use:"
echo "  docker compose exec db pg_restore -U ${POSTGRES_USER} -d ${CKAN_DB} -c -v /path/to/${BACKUP_FILENAME}"
if grep -q "CKAN__PLUGINS.*datastore" .env; then
  echo "  docker compose exec db pg_restore -U ${POSTGRES_USER} -d ${DATASTORE_DB} -c -v /path/to/${DATASTORE_BACKUP_FILENAME}"
fi