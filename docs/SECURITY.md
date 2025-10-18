# Security Guidelines

## Critical: Never Commit These

**NEVER commit to git**:
- `.env` file (contains all passwords and secrets)
- SSH credentials (host, port, user, password)
- Database passwords
- API keys or tokens
- SSL private keys
- Backup passwords

## Where Credentials Are Stored

All sensitive credentials are in `.env` (which is gitignored):

```bash
# .env contains:
SSH_HOST=...
SSH_PORT=...
SSH_USER=...
SSH_BACKUP_PASSWORD=...
POSTGRES_PASSWORD=...
DIRECTUS_KEY=...
DIRECTUS_SECRET=...
ADMIN_PASSWORD=...
N8N_BASIC_AUTH_PASSWORD=...
# etc.
```

## Using Credentials Safely

### In Scripts
Reference env variables:
```bash
# Good
ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}

# Bad - never hardcode!
ssh -p <exposed-port> user@<exposed-ip>
```

### In Documentation
Use placeholders:
```bash
# Good
ssh -p <port-from-env> <user-from-env>@<host-from-env>

# Bad - exposes real credentials
ssh -p <port> <user>@<host>
```

## Access Control

### Production Server SSH
- **Never** expose SSH host/port in public repos
- Use SSH keys instead of passwords when possible
- Change default SSH port from 22
- Use fail2ban or similar for brute-force protection
- Regularly review SSH logs: `sudo tail -f /var/log/auth.log`

### Directus Admin
- Use strong passwords (20+ characters)
- Enable 2FA if available in future versions
- Review user access regularly
- Rotate passwords quarterly

### n8n Access
- Keep basic auth enabled in production
- Use strong password
- Restrict access by IP if possible (via nginx)
- Review workflow executions for suspicious activity

## Database Security

- PostgreSQL is bound to Docker network only (192.168.1.100)
- Not exposed to public internet
- Use strong passwords
- Regular backups with encryption in transit (to GCS)

## SSL/TLS

- Certificates managed by Let's Encrypt
- Auto-renewal via certbot
- Monitor expiry: `sudo certbot certificates`
- Nginx configured for strong TLS ciphers

## Backups

### Database Backups
- Local backups: encrypted at rest on server
- GCS backups: encrypted by Google Cloud
- Access controlled via service account
- Review bucket permissions regularly

### Sensitive Data in Backups
- Database dumps contain all application data
- Store backups securely
- Never share backup files via insecure channels
- When downloading locally, delete after use

## Docker Security

- Use official images only
- Regularly update images: `docker-compose pull`
- Scan for vulnerabilities: `docker scan <image>`
- Don't run containers as root (already configured)
- Review docker logs for suspicious activity

## Network Security

### Firewall Rules
Ensure only these ports are open:
- `80` - HTTP (redirects to HTTPS)
- `443` - HTTPS
- `SSH_PORT` - SSH (non-standard port from .env)

Check with:
```bash
sudo ufw status
```

### Nginx Configuration
- Rate limiting enabled
- Request size limits
- No directory listing
- Security headers configured

## Incident Response

### If Credentials Are Compromised

1. **Immediately** rotate all affected credentials
2. Review access logs for unauthorized access
3. Check database for suspicious modifications
4. Restore from clean backup if needed
5. Update all .env files everywhere
6. Update passwords in n8n credentials
7. Document the incident

### If Repository Is Exposed

1. **Never** try to remove secrets from git history
2. Rotate ALL credentials immediately
3. Consider the repository permanently compromised
4. Create new repository if needed
5. Update all deployment configurations

## Regular Security Tasks

### Weekly
- [ ] Review nginx access logs for suspicious activity
- [ ] Check fail2ban logs (if configured)

### Monthly
- [ ] Review user accounts and access levels
- [ ] Check for failed login attempts
- [ ] Scan Docker images for vulnerabilities
- [ ] Review firewall rules

### Quarterly
- [ ] Rotate database passwords
- [ ] Rotate Directus admin password
- [ ] Rotate n8n basic auth password
- [ ] Review and update security policies

### Annually
- [ ] Full security audit
- [ ] Rotate ALL credentials
- [ ] Review and update access controls
- [ ] Test incident response procedures

## Best Practices

1. **Principle of Least Privilege**: Only grant access that's needed
2. **Defense in Depth**: Multiple layers of security
3. **Regular Updates**: Keep all software current
4. **Monitor Everything**: Logs, metrics, alerts
5. **Test Backups**: Regular restore tests
6. **Document Everything**: Security procedures and incidents
7. **Assume Breach**: Plan for worst-case scenarios

## Security Checklist for New Team Members

Before giving someone access:
- [ ] Provide `.env` file via secure channel (password manager, encrypted)
- [ ] Create individual user accounts (don't share passwords)
- [ ] Document what they have access to
- [ ] Review security guidelines with them
- [ ] Set up 2FA where possible
- [ ] Revoke access when they leave

## Contact

**Security issues**: Report via encrypted channel (not public)  
**Production access**: Keep credentials in team password manager  
**Emergency**: Follow disaster recovery procedures first

## See Also

- [MAINTENANCE.md](MAINTENANCE.md) - Regular maintenance including security tasks
- [DISASTER-RECOVERY.md](DISASTER-RECOVERY.md) - Recovery procedures
- [DEPLOYMENT.md](DEPLOYMENT.md) - Secure deployment practices

