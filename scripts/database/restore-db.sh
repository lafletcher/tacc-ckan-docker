#!/bin/bash
# Database restore script for CKAN Docker setup
# Usage: ./restore-db.sh path/to/ckan_backup.dump [path/to/datastore_backup.dump]

set -e

# Check if backup file is provided
if [ -z "$1" ]; then
  echo "Error: No backup file specified"
  echo "Usage: ./restore-db.sh path/to/ckan_backup.dump [path/to/datastore_backup.dump]"
  exit 1
fi

CKAN_BACKUP_FILE="$1"
DATASTORE_BACKUP_FILE="$2"

# Validate backup file exists
if [ ! -f "$CKAN_BACKUP_FILE" ]; then
  echo "Error: Backup file does not exist: $CKAN_BACKUP_FILE"
  exit 1
fi

# If datastore backup file is provided, validate it exists
if [ ! -z "$DATASTORE_BACKUP_FILE" ] && [ ! -f "$DATASTORE_BACKUP_FILE" ]; then
  echo "Error: Datastore backup file does not exist: $DATASTORE_BACKUP_FILE"
  exit 1
fi

# Load environment variables
source ./.env
POSTGRES_USER=${POSTGRES_USER:-ckan}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-ckan}
CKAN_DB=${CKAN_DB:-ckan}
DATASTORE_DB=${DATASTORE_DB:-datastore}

echo "Starting database restore process..."

# Copy the backup file to the container
CKAN_FILENAME=$(basename "$CKAN_BACKUP_FILE")
echo "Copying $CKAN_FILENAME to container..."
docker compose cp "$CKAN_BACKUP_FILE" "db:/tmp/$CKAN_FILENAME"

# Stop CKAN services to prevent active connections during restore
echo "Stopping CKAN services..."
docker compose stop ckan datapusher

# Restore the main CKAN database
echo "Restoring main CKAN database..."
docker compose exec db bash -c "
  # Drop and recreate database
  dropdb -U $POSTGRES_USER --if-exists $CKAN_DB
  createdb -U $POSTGRES_USER -O $POSTGRES_USER $CKAN_DB -E utf-8

  # Restore from backup
  pg_restore -U $POSTGRES_USER -d $CKAN_DB -v '/tmp/$CKAN_FILENAME'
"

# Restore datastore if backup provided
if [ ! -z "$DATASTORE_BACKUP_FILE" ]; then
  DATASTORE_FILENAME=$(basename "$DATASTORE_BACKUP_FILE")
  echo "Copying $DATASTORE_FILENAME to container..."
  docker compose cp "$DATASTORE_BACKUP_FILE" "db:/tmp/$DATASTORE_FILENAME"

  echo "Restoring datastore database..."
  docker compose exec db bash -c "
    # Drop and recreate database
    dropdb -U $POSTGRES_USER --if-exists $DATASTORE_DB
    createdb -U $POSTGRES_USER -O $POSTGRES_USER $DATASTORE_DB -E utf-8

    # Restore from backup
    pg_restore -U $POSTGRES_USER -d $DATASTORE_DB -v '/tmp/$DATASTORE_FILENAME'

    # Clean up
    rm -f '/tmp/$DATASTORE_FILENAME'
  "
fi

# Clean up temp files
docker compose exec db rm -f "/tmp/$CKAN_FILENAME"

# Restart services
echo "Starting CKAN services..."
docker compose start ckan datapusher
docker compose restart nginx

echo "Database restore completed successfully!"
echo "You may want to rebuild the search index with:"
echo "  docker compose exec ckan ckan search-index rebuild"