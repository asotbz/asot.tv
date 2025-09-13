# Video Jockey C# - Single Container Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the C# version of Video Jockey as a single, self-contained Docker container optimized for self-hosting scenarios.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Deployment Options](#deployment-options)
3. [Configuration](#configuration)
4. [Production Deployment](#production-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Docker 20.10+ or Podman 4.0+
- 1GB free RAM
- 10GB free disk space
- Linux, Windows, or macOS

### 1-Minute Deployment

```bash
# Pull and run the container (no API keys needed!)
docker run -d \
  --name videojockey \
  -p 8080:8080 \
  -v videojockey_data:/data \
  -v videojockey_media:/media \
  ghcr.io/yourusername/videojockey:latest

# Access the application
# First run: http://localhost:8080/setup (complete setup wizard)
# After setup: http://localhost:8080
```

### Docker Compose Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  videojockey:
    image: ghcr.io/yourusername/videojockey:latest
    container_name: videojockey
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data     # SQLite database and application data
      - ./media:/media   # Video storage
    # No environment variables needed - all config stored in database!
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
```

Deploy (no .env file needed):

```bash
docker-compose up -d
```

---

## Deployment Options

### Option 1: Docker (Recommended)

#### Building from Source

```bash
# Clone repository
git clone https://github.com/yourusername/videojockey-csharp.git
cd videojockey-csharp

# Build Docker image
docker build -t videojockey:latest .

# Run container (no environment variables!)
docker run -d \
  --name videojockey \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  -v $(pwd)/media:/media \
  videojockey:latest

# On first run, navigate to http://localhost:8080/setup
```

#### Using Pre-built Image

```bash
# Pull latest image
docker pull ghcr.io/yourusername/videojockey:latest

# Run with persistent data
docker run -d \
  --name videojockey \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  -v $(pwd)/media:/media \
  ghcr.io/yourusername/videojockey:latest
```

### Option 2: Standalone Executable

#### Linux Deployment

```bash
# Download release
wget https://github.com/yourusername/videojockey/releases/latest/download/videojockey-linux-x64.tar.gz
tar -xzf videojockey-linux-x64.tar.gz

# Make executable
chmod +x VideoJockey

# Create directories
mkdir -p data media config

# Run application
./VideoJockey --urls=http://0.0.0.0:8080
```

#### Windows Deployment

```powershell
# Download release
Invoke-WebRequest -Uri "https://github.com/yourusername/videojockey/releases/latest/download/videojockey-win-x64.zip" -OutFile "videojockey.zip"
Expand-Archive -Path "videojockey.zip" -DestinationPath "."

# Create directories
New-Item -ItemType Directory -Path "data", "media", "config"

# Run application
.\VideoJockey.exe --urls=http://0.0.0.0:8080
```

#### macOS Deployment

```bash
# Download release
curl -L https://github.com/yourusername/videojockey/releases/latest/download/videojockey-osx-x64.tar.gz -o videojockey.tar.gz
tar -xzf videojockey.tar.gz

# Make executable
chmod +x VideoJockey

# Create directories
mkdir -p data media config

# Run application
./VideoJockey --urls=http://0.0.0.0:8080
```

### Option 3: Systemd Service (Linux)

Create `/etc/systemd/system/videojockey.service`:

```ini
[Unit]
Description=Video Jockey Music Video Management
After=network.target

[Service]
Type=simple
User=videojockey
Group=videojockey
WorkingDirectory=/opt/videojockey
ExecStart=/opt/videojockey/VideoJockey
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=videojockey
Environment="ASPNETCORE_ENVIRONMENT=Production"
Environment="ASPNETCORE_URLS=http://0.0.0.0:8080"

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/videojockey/data /opt/videojockey/media

[Install]
WantedBy=multi-user.target
```

Install and start:

```bash
# Create user
sudo useradd -r -s /bin/false videojockey

# Create directories
sudo mkdir -p /opt/videojockey/{data,media,config}
sudo chown -R videojockey:videojockey /opt/videojockey

# Copy application
sudo cp -r ./publish/* /opt/videojockey/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable videojockey
sudo systemctl start videojockey

# Check status
sudo systemctl status videojockey
```

### Option 4: Windows Service

```powershell
# Install as Windows Service
sc.exe create VideoJockey binPath="C:\VideoJockey\VideoJockey.exe" start=auto

# Configure service
sc.exe config VideoJockey DisplayName="Video Jockey" 
sc.exe description VideoJockey "Music Video Management System"

# Start service
sc.exe start VideoJockey
```

### Option 5: Kubernetes Deployment

Create `videojockey-k8s.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: videojockey
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: videojockey-data
  namespace: videojockey
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: videojockey-media
  namespace: videojockey
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: videojockey-config
  namespace: videojockey
data:
  appsettings.Production.json: |
    {
      "Storage": {
        "MediaPath": "/media",
        "DataPath": "/data"
      }
    }
---
apiVersion: v1
kind: Secret
metadata:
  name: videojockey-secrets
  namespace: videojockey
type: Opaque
stringData:
  imvdb-api-key: "your-imvdb-api-key"
  youtube-api-key: "your-youtube-api-key"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: videojockey
  namespace: videojockey
spec:
  replicas: 1
  selector:
    matchLabels:
      app: videojockey
  template:
    metadata:
      labels:
        app: videojockey
    spec:
      containers:
      - name: videojockey
        image: ghcr.io/yourusername/videojockey:latest
        ports:
        - containerPort: 8080
        env:
        - name: ASPNETCORE_ENVIRONMENT
          value: "Production"
        - name: ApiKeys__ImvdbApiKey
          valueFrom:
            secretKeyRef:
              name: videojockey-secrets
              key: imvdb-api-key
        - name: ApiKeys__YouTubeApiKey
          valueFrom:
            secretKeyRef:
              name: videojockey-secrets
              key: youtube-api-key
        volumeMounts:
        - name: data
          mountPath: /data
        - name: media
          mountPath: /media
        - name: config
          mountPath: /app/appsettings.Production.json
          subPath: appsettings.Production.json
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: videojockey-data
      - name: media
        persistentVolumeClaim:
          claimName: videojockey-media
      - name: config
        configMap:
          name: videojockey-config
---
apiVersion: v1
kind: Service
metadata:
  name: videojockey
  namespace: videojockey
spec:
  selector:
    app: videojockey
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

Deploy:

```bash
kubectl apply -f videojockey-k8s.yaml
kubectl get pods -n videojockey
kubectl get svc -n videojockey
```

---

## Configuration

### Database-Driven Configuration

Video Jockey stores all configuration in the SQLite database. On first run, you'll be prompted to complete a setup wizard at `/setup` that will:

1. Create an admin account
2. Configure storage paths
3. Optionally set API keys (can be added later)
4. Initialize the system

After initial setup, all configuration can be managed through the Settings page in the web UI (admin only).

### First-Run Setup

When you first access Video Jockey, you'll see the setup wizard:

```bash
# 1. Start the container
docker run -d \
  --name videojockey \
  -p 8080:8080 \
  -v videojockey_data:/data \
  -v videojockey_media:/media \
  ghcr.io/yourusername/videojockey:latest

# 2. Open browser to http://localhost:8080
# 3. Complete the setup wizard:
#    - Enter admin email and password
#    - Configure storage paths (or use defaults)
#    - Optionally add API keys
#    - Click "Complete Setup"

# 4. System is ready to use!
```

### Configuration Management

All settings are managed through the web UI after initial setup:

- **Settings Page** (`/settings` - admin only):
  - API Keys (IMVDb, YouTube) - encrypted in database
  - Storage configuration
  - Download preferences
  - Security settings
  - User management
  - System features

### Minimal appsettings.json

Only needed for overriding default behaviors:

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Data Source=/data/videojockey.db"
  },
  "DataProtection": {
    "KeysPath": "/data/keys"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

---

## Production Deployment

### Reverse Proxy Setup

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name videojockey.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name videojockey.example.com;

    ssl_certificate /etc/ssl/certs/videojockey.crt;
    ssl_certificate_key /etc/ssl/private/videojockey.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache_bypass $http_upgrade;
        
        # WebSocket support for SignalR
        proxy_read_timeout 86400;
    }

    # Static files
    location /media {
        alias /var/videojockey/media;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
```

#### Traefik Configuration

```yaml
# docker-compose with Traefik
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=admin@example.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt

  videojockey:
    image: ghcr.io/yourusername/videojockey:latest
    container_name: videojockey
    restart: unless-stopped
    volumes:
      - ./data:/data
      - ./media:/media
    # Configuration stored in database - no environment variables needed
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.videojockey.rule=Host(`videojockey.example.com`)"
      - "traefik.http.routers.videojockey.entrypoints=websecure"
      - "traefik.http.routers.videojockey.tls.certresolver=myresolver"
      - "traefik.http.services.videojockey.loadbalancer.server.port=8080"
```

### SSL/TLS Setup

#### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d videojockey.example.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### Self-Signed Certificate

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout videojockey.key \
  -out videojockey.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=videojockey.local"

# Configure in appsettings
{
  "Kestrel": {
    "Endpoints": {
      "Https": {
        "Url": "https://+:8443",
        "Certificate": {
          "Path": "/config/videojockey.crt",
          "KeyPath": "/config/videojockey.key"
        }
      }
    }
  }
}
```

### Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# backup-videojockey.sh

BACKUP_DIR="/backups/videojockey"
DATA_DIR="/var/videojockey/data"
MEDIA_DIR="/var/videojockey/media"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec videojockey sqlite3 /data/videojockey.db ".backup /data/backup.db"
docker cp videojockey:/data/backup.db "$BACKUP_DIR/db_$DATE.db"

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C /var/videojockey config/

# Optional: Backup media (large!)
# tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" -C /var/videojockey media/

# Keep only last 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

#### Cron Schedule

```bash
# Add to crontab
0 2 * * * /usr/local/bin/backup-videojockey.sh >> /var/log/videojockey-backup.log 2>&1
```

### Monitoring Setup

#### Health Check Endpoint

The application provides a health check endpoint at `/health`:

```json
{
  "status": "Healthy",
  "totalDuration": "00:00:00.0123456",
  "entries": {
    "database": {
      "status": "Healthy",
      "duration": "00:00:00.0012345"
    },
    "storage": {
      "status": "Healthy",
      "duration": "00:00:00.0001234",
      "data": {
        "freeSpaceGB": 450.2,
        "usedSpaceGB": 49.8
      }
    }
  }
}
```

#### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'videojockey'
    static_configs:
      - targets: ['videojockey:8080']
    metrics_path: '/metrics'
```

#### Grafana Dashboard

Import the Video Jockey dashboard with ID: `VJ-001` or create custom:

```json
{
  "dashboard": {
    "title": "Video Jockey Monitoring",
    "panels": [
      {
        "title": "Active Downloads",
        "targets": [
          {
            "expr": "videojockey_downloads_active"
          }
        ]
      },
      {
        "title": "Queue Size",
        "targets": [
          {
            "expr": "videojockey_queue_size"
          }
        ]
      },
      {
        "title": "Storage Usage",
        "targets": [
          {
            "expr": "videojockey_storage_used_bytes / 1073741824"
          }
        ]
      }
    ]
  }
}
```

---

## Monitoring & Maintenance

### Log Management

#### View Logs

```bash
# Docker logs
docker logs -f videojockey

# Last 100 lines
docker logs --tail 100 videojockey

# Since timestamp
docker logs --since 2024-01-01T00:00:00 videojockey
```

#### Log Rotation

```json
// appsettings.json
{
  "Serilog": {
    "WriteTo": [
      {
        "Name": "File",
        "Args": {
          "path": "/data/logs/videojockey-.log",
          "rollingInterval": "Day",
          "retainedFileCountLimit": 7,
          "fileSizeLimitBytes": 10485760,
          "rollOnFileSizeLimit": true
        }
      }
    ]
  }
}
```

### Performance Tuning

#### Memory Optimization

```bash
# Limit container memory
docker run -d \
  --name videojockey \
  --memory="512m" \
  --memory-swap="1g" \
  --cpus="1.0" \
  videojockey:latest
```

#### Application Settings

```json
{
  "Performance": {
    "MaxConcurrentRequests": 100,
    "RequestQueueLimit": 1000,
    "EnableResponseCompression": true,
    "EnableResponseCaching": true,
    "CacheDurationSeconds": 300
  }
}
```

### Update Process

#### Docker Update

```bash
# Pull new image
docker pull ghcr.io/yourusername/videojockey:latest

# Stop current container
docker stop videojockey

# Backup data
docker run --rm -v videojockey_data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# Remove old container
docker rm videojockey

# Start new container
docker run -d \
  --name videojockey \
  -p 8080:8080 \
  -v videojockey_data:/data \
  -v videojockey_media:/media \
  ghcr.io/yourusername/videojockey:latest
```

#### Zero-Downtime Update

```bash
# Using Docker Compose
docker-compose pull
docker-compose up -d --no-deps --build videojockey
```

---

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs
docker logs videojockey

# Check container status
docker inspect videojockey

# Verify volumes
docker volume ls
docker volume inspect videojockey_data

# Test with minimal config
docker run --rm -it ghcr.io/yourusername/videojockey:latest
```

#### Database Issues

```bash
# Check database integrity
docker exec videojockey sqlite3 /data/videojockey.db "PRAGMA integrity_check"

# Repair database
docker exec videojockey sqlite3 /data/videojockey.db "VACUUM"

# Export and reimport
docker exec videojockey sqlite3 /data/videojockey.db ".dump" > backup.sql
docker exec -i videojockey sqlite3 /data/videojockey_new.db < backup.sql
```

#### Permission Issues

```bash
# Fix volume permissions
docker exec videojockey chown -R 1000:1000 /data /media

# Run with specific user
docker run -d \
  --user 1000:1000 \
  --name videojockey \
  videojockey:latest
```

#### Memory Issues

```bash
# Check memory usage
docker stats videojockey

# Increase memory limit
docker update --memory="1g" --memory-swap="2g" videojockey

# Check for memory leaks
docker exec videojockey dotnet-dump collect -p 1
docker exec videojockey dotnet-dump analyze core_file
```

### Debug Mode

```bash
# Run in debug mode
docker run -it \
  --rm \
  -e ASPNETCORE_ENVIRONMENT=Development \
  -e Logging__LogLevel__Default=Debug \
  -p 8080:8080 \
  videojockey:latest
```

### Health Check Failed

```bash
# Manual health check
curl http://localhost:8080/health

# Check with verbose output
curl -v http://localhost:8080/health

# Check from inside container
docker exec videojockey wget -O- http://localhost:8080/health
```

### Reset Application

```bash
# Complete reset (WARNING: Deletes all data)
docker stop videojockey
docker rm videojockey
docker volume rm videojockey_data videojockey_media
docker run -d \
  --name videojockey \
  -p 8080:8080 \
  -v videojockey_data:/data \
  -v videojockey_media:/media \
  videojockey:latest
```

---

## Security Best Practices

### Container Security

```yaml
# Secure docker-compose.yml
version: '3.8'

services:
  videojockey:
    image: ghcr.io/yourusername/videojockey:latest
    container_name: videojockey
    restart: unless-stopped
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - ./data:/data:rw
      - ./media:/media:rw
      - ./config:/config:ro
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
```

### Network Security

```bash
# Create isolated network
docker network create --driver bridge videojockey-net

# Run with custom network
docker run -d \
  --name videojockey \
  --network videojockey-net \
  videojockey:latest
```

### Secrets Management

All secrets (API keys, JWT secret) are stored encrypted in the SQLite database using ASP.NET Core Data Protection API. No Docker secrets or environment variables needed for sensitive data.

To manage secrets:
1. Login as admin
2. Navigate to Settings
3. Update API keys or other sensitive configuration
4. Changes are encrypted and saved to database

The encryption keys are stored in `/data/keys` and should be backed up along with the database.

---

## Support

### Getting Help

1. Check the [Documentation](https://github.com/yourusername/videojockey/wiki)
2. Search [Issues](https://github.com/yourusername/videojockey/issues)
3. Join [Discord Community](https://discord.gg/videojockey)
4. Email: support@videojockey.app

### Reporting Issues

When reporting issues, include:
- Docker version: `docker --version`
- Container logs: `docker logs videojockey`
- Configuration (without secrets)
- Steps to reproduce

### Contributing

See [CONTRIBUTING.md](https://github.com/yourusername/videojockey/blob/main/CONTRIBUTING.md) for guidelines.

---

## Appendix

### Minimum System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 1 core | 2+ cores |
| RAM | 512MB | 1GB |
| Storage | 10GB | 100GB+ |
| Docker | 20.10 | Latest stable |
| Network | 10 Mbps | 100+ Mbps |

### Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 8080 | HTTP | Web interface |
| 8443 | HTTPS | Secure web (optional) |

### Volume Reference

| Path | Purpose | Persistent |
|------|---------|------------|
| /data | Database, logs | Yes |
| /media | Video files | Yes |
| /config | Configuration | Yes |
| /tmp | Temporary files | No |

---

This deployment guide provides everything needed to successfully deploy and maintain Video Jockey in production environments.