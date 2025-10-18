# n8n Workflows and Configuration

This directory contains n8n workflow automation configurations and data.

## Structure

```
apps/n8n/
├── workflows/              # Exported workflow JSON files
│   └── data-export-workflow.json  # Main data export workflow to Google Sheets
├── database.sqlite         # n8n workflow database (contains all workflows and executions)
├── config                  # n8n configuration file
└── README.md              # This file
```

## Workflows

### data-export-workflow.json

**Purpose**: Automatically exports Directus database records to Google Sheets for reporting.

**Schedule**: Runs every hour at :35 minutes

**What it does**:
1. Queries `jegyzokonyv` and `intervencio` tables from PostgreSQL
2. Transforms data into different report formats (altemak, fotemak, sima, filter)
3. Exports to multiple Google Sheets tabs for different views

**Tables queried**:
- `jegyzokonyv` - Main records
- `intervencio` - Intervention records

**Google Sheets Target**: 
- Document ID: `1DNKX2j07xZLm_7VdaNCdKT4TnxCI-JlEwA5FzNgxSVQ`
- Multiple sheets: jegyzo_altemak, jegyzo_fotemak, jegyzo_sima, jegyzo_fotema-filter, intervencio_sima

## Importing Workflows

### Method 1: Import via n8n UI (Recommended)

1. Access n8n at http://localhost:5678 (local) or https://jegyzokonyv.kek-vonal.cc/n8n/ (production)
2. Click **Workflows** → **+** → **Import from file**
3. Select `workflows/data-export-workflow.json`
4. Reconfigure credentials (see below)

### Method 2: Restore from database.sqlite

If you have the full `database.sqlite` file, it contains all workflows and credentials:

1. Stop n8n container: `docker-compose stop n8n`
2. Copy the database: 
   ```bash
   docker cp apps/n8n/database.sqlite n8n:/home/node/.n8n/database.sqlite
   ```
3. Restart n8n: `docker-compose start n8n`

## Credentials Setup

After importing workflows, you need to configure these credentials in n8n:

### 1. PostgreSQL (Postgres account)

- **Type**: PostgreSQL
- **Name**: "Postgres account"
- **Host**: `192.168.1.100` (Docker network) or `database` (container name)
- **Port**: `5432`
- **Database**: `directus`
- **User**: From `.env` → `POSTGRES_USER`
- **Password**: From `.env` → `POSTGRES_PASSWORD`

### 2. Google Sheets OAuth2

- **Type**: Google Sheets OAuth2 API
- **Name**: "Google Sheets account"
- **Setup**: Follow n8n's Google Sheets OAuth2 setup guide
- **Permissions needed**: Read and write access to Google Sheets

## Local Development

To use n8n locally with the production database:

1. **Restore the SQLite database** (contains all workflows):
   ```bash
   # The database.sqlite file is already in apps/n8n/
   # It will be mounted automatically via docker-compose
   ```

2. **Start n8n**:
   ```bash
   docker-compose up -d n8n
   ```

3. **Access n8n**:
   - URL: http://localhost:5678
   - No authentication (disabled for local dev via docker-compose.override.yml)

4. **Update credentials**:
   - Go to **Settings** → **Credentials**
   - Update database connection to point to `database` or `192.168.1.100`
   - Add/update Google Sheets OAuth credentials

## Production Deployment

On production server:

1. **Restore n8n data**:
   ```bash
   # n8n data is in Docker volume, or restore from backup:
   docker run --rm -v kek-vonal-crm-new_n8n_data:/data -v /path/to/backup:/backup alpine sh -c "cd /data && tar xzf /backup/n8n_backup.tar.gz"
   ```

2. **Environment variables** (already in `.env`):
   ```bash
   N8N_HOST=jegyzokonyv.kek-vonal.cc
   N8N_PROTOCOL=https
   N8N_PATH=/n8n/
   N8N_BASIC_AUTH_ACTIVE=true
   N8N_BASIC_AUTH_USER=marcigdd@gmail.com
   N8N_BASIC_AUTH_PASSWORD=malacka
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

## Workflow Maintenance

### Exporting Workflows

To export workflows after making changes:

```bash
# Via UI
1. Go to Workflows
2. Click ⋯ menu → Export
3. Save to apps/n8n/workflows/

# Or export all workflows via API
curl -u email:password http://localhost:5678/rest/workflows \
  -o apps/n8n/workflows/all-workflows-backup.json
```

### Backing Up n8n Data

The complete n8n state is in the SQLite database:

```bash
# Local
cp apps/n8n/database.sqlite apps/n8n/database.sqlite.backup

# From Docker volume (production)
docker run --rm -v kek-vonal-crm-new_n8n_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/n8n_backup_$(date +%Y%m%d).tar.gz -C /data .
```

## Troubleshooting

### Workflow not running on schedule

1. Check if workflow is **active**: Toggle the switch in the workflow header
2. Check n8n logs: `docker-compose logs n8n`
3. Verify Schedule Trigger is set to: "Every hour at :35 minutes"

### Database connection errors

1. Verify PostgreSQL credentials in n8n match `.env` file
2. Check database is running: `docker-compose ps database`
3. Test connection from n8n container:
   ```bash
   docker exec -it n8n sh
   nc -zv database 5432
   ```

### Google Sheets permission errors

1. Reauthorize Google OAuth credentials
2. Verify the service account has access to the target spreadsheet
3. Check that spreadsheet ID hasn't changed

## Data Flow

```
PostgreSQL (Directus DB)
    ↓ (Every hour at :35)
Schedule Trigger
    ↓
Query jegyzokonyv + intervencio tables
    ↓
Transform data (4 different formats)
    ├─→ Altemak (subtopics) → Google Sheets
    ├─→ Fotemak (main topics) → Google Sheets
    ├─→ Sima (simple) → Google Sheets
    └─→ Fotema_Filter (filtered) → Google Sheets
```

## Notes

- **Credential IDs** in workflow files are just references, not actual secrets
- Actual credentials are stored in n8n's database and are encrypted
- When importing workflows, you'll need to reconfigure credentials
- The workflow runs hourly and processes records from the last 62 minutes (avoiding last 2 minutes for data consistency)

