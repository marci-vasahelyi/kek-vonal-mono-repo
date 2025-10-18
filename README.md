# KEK-VONAL Infrastructure Monorepo

Complete infrastructure setup for the KEK-VONAL project, including Directus CMS, n8n automation, PostgreSQL database, and all necessary configurations.

## 🏗️ Architecture

This monorepo contains everything needed to run and restore the KEK-VONAL infrastructure:

- **Directus CMS** - Headless CMS for content management
- **n8n** - Workflow automation tool
- **PostgreSQL + PostGIS** - Database with geographic extensions
- **Redis** - Caching layer
- **Nginx** - Reverse proxy with SSL termination
- **Automated Backups** - Daily database backups to Google Cloud Storage

## 📁 Repository Structure

```
kek-vonal-mono-repo/
├── apps/
│   ├── directus/
│   │   ├── extensions/        # Custom Directus extensions
│   │   │   ├── endpoints/     # API endpoints
│   │   │   └── operations/    # Custom operations
│   │   └── uploads/           # User uploaded files
│   └── n8n/
│       ├── workflows/         # Exported n8n workflows
│       └── README.md          # n8n documentation
├── infrastructure/
│   ├── nginx/
│   │   ├── sites-available/   # Nginx site configurations
│   │   └── nginx.conf         # Main nginx config
│   ├── ssl/                   # SSL certificates (not in git)
│   └── docker/                # Docker-related configs
├── scripts/
│   ├── backup/                # Database backup scripts
│   ├── restore/               # Database restore scripts
│   └── deployment/            # Deployment and setup scripts
├── docs/                      # Additional documentation
├── backups/                   # Local database backups (not in git)
├── data/                      # Database data (not in git)
├── docker-compose.yml         # Main application stack
├── .env                       # Environment variables (not in git)
└── .env.example               # Environment template
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Access to the server (if deploying remotely)
- `.env` file configured (copy from `.env.example`)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd kek-vonal-mono-repo
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

4. **Access the applications:**
   - Directus: http://localhost:8055
   - n8n: http://localhost:5678

5. **Import n8n workflows** (optional):
   - See [apps/n8n/README.md](apps/n8n/README.md) for workflow setup

### Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## 🔧 Configuration

### Environment Variables

All configuration is managed through a single `.env` file. Key variables include:

- **Server Configuration**: Domain, SSL, networking
- **Database**: PostgreSQL credentials and connection
- **Directus**: Admin credentials, email settings, API keys
- **n8n**: Authentication and webhook configuration
- **Backups**: Google Cloud Storage settings

See `.env.example` for all available options.

### Nginx Configuration

Nginx is configured as a reverse proxy with SSL termination:
- Directus is served at the root domain
- n8n is accessible at `/n8n/`
- SSL certificates managed by Let's Encrypt

Configuration file: `infrastructure/nginx/sites-available/jegyzokonyv.kek-vonal.cc`

## 📦 Applications

### Directus

Content management system for managing all application data.

**Local**: http://localhost:8055  
**Production**: https://jegyzokonyv.kek-vonal.cc

- Default admin credentials in `.env` file
- Custom extensions in `apps/directus/extensions/`
- Uploaded files in `apps/directus/uploads/`

### n8n

Workflow automation tool for data exports and integrations.

**Local**: http://localhost:5678 (no auth required)  
**Production**: https://jegyzokonyv.kek-vonal.cc/n8n/ (basic auth required)

- Workflows exported in `apps/n8n/workflows/`
- Main workflow: hourly data export to Google Sheets
- See [apps/n8n/README.md](apps/n8n/README.md) for detailed documentation

### Dashboard

Interactive data visualization dashboard for mental health contact analytics.

**Local**: http://localhost:8501 (Streamlit)  
**Production**: Not yet deployed

- Real-time PostgreSQL data visualization
- Monthly trends, demographics, channels, topics
- Built with Streamlit + Plotly
- See [apps/dashboard/README.md](apps/dashboard/README.md) for usage

## 💾 Backups and Restore

### Creating a Backup

```bash
./scripts/backup/db-backup.sh
```

This will:
- Create a timestamped SQL dump
- Compress it with gzip
- Upload to Google Cloud Storage (if configured)
- Keep local backups for 7 days

### Restoring from Backup

```bash
./scripts/restore/db-restore.sh backups/directus_backup_YYYYMMDD.sql.gz
```

This will:
- Stop the Directus container
- Drop and recreate the database
- Restore from the backup file
- Restart all containers

**⚠️ Warning:** This will completely replace your current database!

## 🔄 Deployment

### Update Deployment

To update the running application:

```bash
./scripts/deployment/deploy.sh
```

This script:
- Pulls latest Docker images
- Restarts containers with zero-downtime
- Verifies all services are running

### Fresh Server Setup

To set up a completely new server:

```bash
sudo ./scripts/deployment/setup-server.sh
```

Then:
1. Copy the entire monorepo to `/home/kek-vonal-crm/`
2. Copy your `.env` file
3. Copy nginx configuration
4. Request SSL certificate with Certbot
5. Start the application

See [docs/DISASTER-RECOVERY.md](docs/DISASTER-RECOVERY.md) for complete recovery procedures.

## 🌐 Server Information

- **Domain**: `jegyzokonyv.kek-vonal.cc`
- **SSH Access**: See `.env` file for credentials (never commit to git!)
  ```bash
  # Get from .env file
  ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}
  ```

## 📊 Monitoring

### Check Service Status

```bash
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f directus
docker-compose logs -f n8n
docker-compose logs -f database
```

### Check Backup Logs

```bash
cat backups/backup.log
```

## 🛠️ Maintenance

### Update Docker Images

```bash
docker-compose pull
docker-compose up -d
```

### Restart Services

```bash
docker-compose restart
```

### Stop All Services

```bash
docker-compose down
```

### Clean Up Old Backups

Backups older than 7 days are automatically removed. To change retention:

```bash
# Edit .env
BACKUP_RETENTION_DAYS=14
```

## 🔐 Security Notes

- ⚠️ **NEVER commit `.env` file to git** - it contains sensitive credentials
- SSL certificates are managed by Let's Encrypt
- Nginx handles SSL termination
- Database is only accessible from Docker network
- Regular backups are encrypted in Google Cloud Storage

## 📝 Additional Documentation

- [MAINTENANCE.md](docs/MAINTENANCE.md) - Regular maintenance checklist
- [SECURITY.md](docs/SECURITY.md) - Security guidelines and best practices
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Detailed deployment guide
- [DISASTER-RECOVERY.md](docs/DISASTER-RECOVERY.md) - Complete recovery procedures
- [NGINX-SETUP.md](docs/NGINX-SETUP.md) - Nginx and SSL configuration
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🆘 Troubleshooting

### Containers won't start
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f
```

### Database connection issues
Check if database container is running:
```bash
docker ps | grep database
docker-compose logs database
```

### Nginx configuration errors
Test nginx configuration:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

## 📞 Support

For issues or questions, contact: marcigdd@gmail.com

## 📄 License

Internal project - All rights reserved.

---

**Last Updated**: October 2025
**Maintained by**: Marci
