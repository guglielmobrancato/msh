# VPS Deployment Guide - Ancile AI

This guide covers deploying the autonomous intelligence portal to a VPS for 24/7 operation.

## Prerequisites

- VPS with Ubuntu 22.04 (DigitalOcean, Linode, AWS EC2, etc.)
- SSH access to the VPS
- Domain name (optional, for HTTPS)

## Initial VPS Setup

### 1. Connect to VPS

```bash
ssh root@your-vps-ip
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Git
sudo apt install git -y

# Install Node.js (for Strapi)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

### 3. Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE ancile_ai;
CREATE USER intel_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ancile_ai TO intel_user;
\q
```

## Deploy Intelligence Portal

### 1. Clone Repository

```bash
# Create app directory
mkdir -p /var/www/ancile-ai
cd /var/www/ancile-ai

# Clone your repository (replace with your repo URL)
git clone https://github.com/yourusername/intelligence-portal.git
cd intelligence-portal
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env with production values
nano .env
```

**Critical `.env` values to set:**
```
GEMINI_API_KEY=your_actual_gemini_key
NEWS_API_KEY=your_actual_newsapi_key
DATABASE_URL=postgresql://intel_user:your_secure_password_here@localhost:5432/ancile_ai
STRAPI_URL=http://localhost:1337
STRAPI_API_TOKEN=your_strapi_token
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
ENVIRONMENT=production
```

### 4. Initialize Database

```bash
python scripts/setup_database.py
```

### 5. Test Pipeline

```bash
# Dry run first
python scripts/run_pipeline.py --dry-run

# Full run (if dry-run successful)
python scripts/run_pipeline.py --max-articles 1
```

## Deploy Strapi CMS

### 1. Install Strapi

```bash
cd /var/www/ancile-ai
npx create-strapi-app@latest ancile-ai-cms --dbclient=postgres
```

Configure Strapi database connection when prompted:
- Database name: `sovereign_intel_cms`
- Host: `localhost`
- Port: `5432`
- Username: `intel_user`
- Password: `your_secure_password_here`

### 2. Configure Content Type

Follow the steps in `docs/STRAPI_SETUP.md` to create the Article content type and API token.

### 3. Build for Production

```bash
cd ancile-ai-cms
NODE_ENV=production npm run build
```

## Automate with Cron

### 1. Create Cron Job

```bash
# Edit crontab
crontab -e
```

### 2. Add Pipeline Schedule

Run pipeline every 6 hours:

```cron
# Ancile AI Pipeline - Runs every 6 hours
0 */6 * * * /var/www/ancile-ai/intelligence-portal/venv/bin/python /var/www/ancile-ai/intelligence-portal/scripts/run_pipeline.py >> /var/log/ancile-ai.log 2>&1

# Rotate logs weekly
0 0 * * 0 echo "" > /var/log/ancile-ai.log
```

### 3. Verify Cron is Running

```bash
# Check cron service
sudo systemctl status cron

# View scheduled jobs
crontab -l

# Monitor log
tail -f /var/log/sovereign-intel.log
```

## Process Management (PM2)

For better process management, use PM2:

### 1. Install PM2

```bash
sudo npm install -g pm2
```

### 2. Start Strapi with PM2

```bash
cd /var/www/ancile-ai/ancile-ai-cms
pm2 start npm --name "strapi-cms" -- start
pm2 save
pm2 startup  # Follow the instructions
```

### 3. Monitor Processes

```bash
pm2 status
pm2 logs strapi-cms
pm2 restart strapi-cms
```

## Security Best Practices

### 1. Firewall Configuration

```bash
# Install UFW
sudo apt install ufw -y

# Allow SSH (CRITICAL - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (if exposing Strapi publicly)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### 2. SSH Key Authentication

```bash
# On your local machine, generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy to VPS
ssh-copy-id root@your-vps-ip

# Disable password authentication on VPS
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### 3. Secure PostgreSQL

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure only local connections allowed
# Change 'peer' to 'md5' for password authentication

sudo systemctl restart postgresql
```

## Monitoring & Maintenance

### Check Pipeline Logs

```bash
# View recent logs
tail -n 100 /var/log/ancile-ai.log

# Follow live logs
tail -f /var/log/ancile-ai.log

# Search for errors
grep "ERROR\|Failed" /var/log/ancile-ai.log
```

### Database Maintenance

```bash
# Check database size
sudo -u postgres psql -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database;"

# Backup database
pg_dump -U intel_user ancile_ai > backup_$(date +%Y%m%d).sql

# Restore database
psql -U intel_user ancile_ai < backup_20260212.sql
```

### Update Application

```bash
cd /var/www/ancile-ai/intelligence-portal
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

## HTTPS Setup (Optional)

If exposing Strapi publicly:

```bash
# Install Nginx
sudo apt install nginx -y

# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/ancile-ai
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:1337;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/ancile-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Troubleshooting

**Pipeline not running on schedule**
```bash
# Check cron logs
sudo journalctl -u cron -f

# Manually test cron command
/var/www/ancile-ai/intelligence-portal/venv/bin/python /var/www/ancile-ai/intelligence-portal/scripts/run_pipeline.py
```

**Database connection errors**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U intel_user -d ancile_ai -h localhost
```

**Strapi not accessible**
```bash
# Check PM2 status
pm2 status

# Restart Strapi
pm2 restart strapi-cms

# View logs
pm2 logs strapi-cms
```

## Cost Optimization

- **VPS**: Start with $10/month droplet (2GB RAM)
- **Bandwidth**: Monitor usage, upgrade if needed
- **Gemini API**: Use free tier (15 RPM) or paid ($0.001/1K tokens)
- **Storage**: Enable log rotation to save disk space

## Monitoring Tools (Optional)

- **Uptime monitoring**: UptimeRobot (free)
- **Error tracking**: Sentry.io (free tier)
- **Analytics**: Simple Analytics or Plausible (privacy-focused)

---

**Your intelligence portal is now running autonomously 24/7!**
