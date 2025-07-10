# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CKAN (Comprehensive Knowledge Archive Network) deployment customized for TACC (Texas Advanced Computing Center). CKAN is an open-source data management platform running on Python 3.9 with version 2.9.

## Development Commands

### Environment Setup
```bash
# Development environment
cp .env.secrets.example .env.dev.secrets  # Edit with your values
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d

# Production environment
cp .env.secrets.example .env.prod.secrets  # Edit with your values
docker compose build
docker compose up -d
```

### Development Workflow
- **Local development**: Edit files in `src/ckanext-*` directories - changes auto-reload
- **Access**: Development runs on port 5000, production on HTTPS port 8443
- **Database management**: Use scripts in `scripts/database/` for backup/restore
- **User management**: `docker compose exec ckan ckan sysadmin add username`

### Testing
```bash
# Run extension tests
docker compose -f docker-compose.dev.yml exec ckan-dev pytest --ckan-ini=test.ini --cov=ckanext.extension_name --disable-warnings

# Initialize test database first
docker compose -f docker-compose.dev.yml exec ckan-dev ckan -c test.ini db init
```

### Extension Development
```bash
# Generate new extension
docker compose -f docker-compose.dev.yml exec ckan-dev ckan generate extension --output-dir /srv/app/src_extensions

# Fix ownership after creation
docker compose -f docker-compose.dev.yml exec ckan-dev chown --reference /srv/app/src_extensions/ -R /srv/app/src_extensions/ckanext-newext/
```

## Architecture

### Core Components
- **CKAN Core**: Main application container with custom extensions
- **PostgreSQL**: Primary database + separate datastore database
- **Apache Solr 9**: Search engine with spatial search capabilities
- **Redis**: Caching and session management
- **DataPusher**: Automatic data processing service
- **NGINX**: Reverse proxy with SSL termination

### Custom Extensions
1. **ckanext-tacc_theme**: TACC branding and UI customization
2. **ckanext-dso_scheming**: Custom dataset schemas using ckanext-scheming framework
3. **ckanext-tapisfilestore**: Handles `tapis://` protocol URLs for distributed file storage

### Configuration Management
- **Development**: Uses `.env.dev.config` + `.env.dev.secrets`
- **Production**: Uses `.env.prod.config` + `.env.prod.secrets`
- **Security**: Never commit `.env.*secrets` files (auto-ignored by git)

### Authentication
- Uses OAuth2 integration with Tapis platform
- JWT token-based API authentication
- Scripts for OAuth management in `scripts/tapis-oauth/`

### Key Plugin Architecture
Active CKAN plugins: `envvars`, `image_view`, `text_view`, `recline_view`, `datastore`, `datapusher`, `spatial_metadata`, `spatial_query`, `geoview`, `oauth2`, `tacc_theme`, `dso_scheming`, `tapisfilestore`, `showcase`, `pages`, `scheming`, `pdfview`

### Database Schema
- Main CKAN database for metadata and configuration
- Separate datastore database for tabular data
- PostGIS enabled for spatial data support

## Important File Locations

### Extension Source Code
- `src/ckanext-tacc_theme/`: Theme customization and templates
- `src/ckanext-dso_scheming/`: Dataset schema definitions in YAML
- `src/ckanext-tapisfilestore/`: Tapis file system integration

### Configuration Files
- Schema definitions: `ckan_dataset.yaml`, `mint_dataset.yaml`, `subside_dataset.yaml`
- Docker configs: `docker-compose.yml` (prod), `docker-compose.dev.yml` (dev)
- Environment templates: `.env.secrets.example`

### Scripts
- `scripts/database/`: Database backup and restore utilities
- `scripts/tapis-oauth/`: OAuth2 token management tools

## Development Notes

### Extension Testing
Each extension has its own `test.ini` configuration and follows pytest patterns with CKAN-specific fixtures.

### Theme Development
Edit files in `src/ckanext-tacc_theme/ckanext/tacc_theme/templates/` and `public/` for UI changes. Changes are live-reloaded in development mode.

### Schema Management
Dataset schemas are defined in YAML files and managed through the dso_scheming extension, supporting temporal/spatial fields and MINT standard variables.

### File Storage
Supports both local file storage (mounted volumes) and distributed storage via Tapis file system with `tapis://` URLs.