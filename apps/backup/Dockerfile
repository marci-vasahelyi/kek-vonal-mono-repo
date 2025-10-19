FROM google/cloud-sdk:alpine

# Install PostgreSQL client and cron
RUN apk add --no-cache \
  postgresql-client \
  dcron \
  bash \
  tzdata

# Set timezone to match server
ENV TZ=GMT+1

# Create backup directory
RUN mkdir -p /backups /app

# Copy backup scripts
COPY backup.sh /app/backup.sh
COPY entrypoint.sh /app/entrypoint.sh
COPY crontab /etc/cron.d/backup-cron

# Make scripts executable
RUN chmod +x /app/backup.sh /app/entrypoint.sh

# Set proper permissions for cron
RUN chmod 0644 /etc/cron.d/backup-cron && \
  crontab /etc/cron.d/backup-cron

# Create log file
RUN touch /var/log/backup.log && chmod 666 /var/log/backup.log

WORKDIR /app

# Run entrypoint to start cron
CMD ["/app/entrypoint.sh"]

