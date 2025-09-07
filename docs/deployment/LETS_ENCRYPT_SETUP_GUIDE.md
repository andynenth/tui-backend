# Let's Encrypt HTTPS Setup for Castellan Game

## Overview

This guide sets up HTTPS for castellan.andynenth.dev using Let's Encrypt free SSL certificate with nginx as a reverse proxy.

## Prerequisites

- EC2 instance running Ubuntu
- Domain pointing to EC2 (castellan.andynenth.dev → 34.233.7.20)
- SSH access to EC2
- Docker application running on port 80

## Step 1: Connect to EC2 and Install Software

```bash
# SSH into your EC2
ssh -i your-key.pem ubuntu@34.233.7.20

# Update system
sudo apt update
sudo apt upgrade -y

# Install nginx and certbot
sudo apt install nginx certbot python3-certbot-nginx -y

# Stop nginx temporarily (to free port 80 for certbot)
sudo systemctl stop nginx
```

## Step 2: Obtain SSL Certificate

```bash
# Get certificate using standalone mode
sudo certbot certonly --standalone -d castellan.andynenth.dev

# You'll see prompts:
# - Enter email: your-email@example.com
# - Agree to terms: A
# - Share email with EFF: N (optional)

# If successful, you'll see:
# Certificate saved at: /etc/letsencrypt/live/castellan.andynenth.dev/fullchain.pem
# Key saved at: /etc/letsencrypt/live/castellan.andynenth.dev/privkey.pem
```

## Step 3: Update Docker to Use Different Port

First, modify your Docker setup to use port 8080 instead of 80:

```bash
cd /home/ubuntu/liap-tui

# Create a new docker-compose override file
cat > docker-compose.ssl.yml << 'EOF'
version: '3.8'

services:
  liap-tui:
    ports:
      - "8080:80"  # Changed from 80:80
EOF

# Stop current container
docker-compose down

# Start with new port mapping
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d
```

## Step 4: Configure Nginx as HTTPS Reverse Proxy

Create nginx configuration:

```bash
# Create nginx config for castellan
sudo nano /etc/nginx/sites-available/castellan

# Add this configuration:
```

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name castellan.andynenth.dev;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name castellan.andynenth.dev;

    # SSL certificates from Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/castellan.andynenth.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/castellan.andynenth.dev/privkey.pem;

    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/castellan.access.log;
    error_log /var/log/nginx/castellan.error.log;

    # Proxy settings for WebSocket support
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for game connections
        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
    }

    # WebSocket specific location (optional, for clarity)
    location /ws/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/castellan /etc/nginx/sites-enabled/

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# If test passes, start nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Step 5: Update EC2 Security Group

In AWS Console:
1. Go to EC2 → Security Groups
2. Find your instance's security group
3. Add inbound rule:
   - Type: HTTPS
   - Port: 443
   - Source: 0.0.0.0/0 (or restrict as needed)

## Step 6: Set Up Auto-Renewal

Let's Encrypt certificates expire every 90 days. Set up auto-renewal:

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# If successful, add cron job
sudo crontab -e

# Add this line (runs twice daily):
0 */12 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

## Step 7: Test Your Setup

```bash
# Check HTTPS
curl -I https://castellan.andynenth.dev

# Check HTTP redirect
curl -I http://castellan.andynenth.dev

# Check certificate
echo | openssl s_client -connect castellan.andynenth.dev:443 -servername castellan.andynenth.dev 2>/dev/null | openssl x509 -noout -dates
```

## Troubleshooting

### If certbot fails:
```bash
# Check if port 80 is free
sudo lsof -i :80

# Make sure nginx is stopped
sudo systemctl stop nginx

# Try again
sudo certbot certonly --standalone -d castellan.andynenth.dev
```

### If nginx won't start:
```bash
# Check syntax
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Check if ports are in use
sudo lsof -i :80
sudo lsof -i :443
```

### If WebSocket doesn't work:
- Ensure proxy headers are set correctly
- Check browser console for errors
- Verify Docker is running on port 8080

## Maintenance

### Check certificate expiration:
```bash
sudo certbot certificates
```

### Manually renew certificate:
```bash
sudo certbot renew
sudo systemctl reload nginx
```

### Monitor logs:
```bash
# Nginx access log
sudo tail -f /var/log/nginx/castellan.access.log

# Nginx error log
sudo tail -f /var/log/nginx/castellan.error.log

# Certbot log
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

## Result

After completing these steps:
- ✅ https://castellan.andynenth.dev - Secure game access
- ✅ http://castellan.andynenth.dev - Auto-redirects to HTTPS
- ✅ WebSocket connections work over WSS
- ✅ Auto-renewal every 90 days

## Quick Commands Reference

```bash
# Restart services
sudo systemctl restart nginx
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml restart

# Check status
sudo systemctl status nginx
docker-compose ps

# View certificates
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run
```
