# HTTPS Setup Guide for Liap Tui on EC2

This guide walks you through setting up HTTPS with Let's Encrypt SSL certificates for your Liap Tui deployment.

## Prerequisites

- Domain name pointing to your EC2 Elastic IP
- EC2 instance running Ubuntu 22.04
- Port 443 open in security group
- Nginx installed (done by performance optimization script)

## Option 1: Using Certbot with Nginx (Recommended)

### Step 1: Install Certbot

```bash
# Connect to EC2
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip

# Install Certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

### Step 2: Configure Nginx

Create or update the Nginx configuration:

```bash
sudo tee /etc/nginx/sites-available/liap-tui-ssl << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (will be added by Certbot)
    # ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:5050;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # API endpoints
    location /api {
        proxy_pass http://localhost:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files with caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        proxy_pass http://localhost:5050;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Default location
    location / {
        proxy_pass http://localhost:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

### Step 3: Enable the Site

```bash
# Enable the new configuration
sudo ln -sf /etc/nginx/sites-available/liap-tui-ssl /etc/nginx/sites-enabled/

# Remove default site if exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t
```

### Step 4: Obtain SSL Certificate

```bash
# Replace your-domain.com with your actual domain
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts:
- Enter email address
- Agree to terms
- Choose whether to share email
- Certbot will automatically configure Nginx

### Step 5: Update Docker Environment

Update your docker-compose.yml:

```yaml
environment:
  - ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

Restart the container:
```bash
cd /home/ubuntu
docker-compose down
docker-compose up -d
```

### Step 6: Test HTTPS

```bash
# Test SSL configuration
curl https://your-domain.com/api/health

# Test SSL certificate
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Step 7: Setup Auto-Renewal

Certbot automatically sets up renewal, but verify:

```bash
# Test renewal
sudo certbot renew --dry-run

# Check cron job
sudo systemctl status certbot.timer
```

## Option 2: Using Docker with Nginx Proxy

### Step 1: Create Docker Compose with HTTPS

Create `docker-compose.https.yml`:

```yaml
version: '3.8'

services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ./certs:/etc/nginx/certs
      - ./vhost:/etc/nginx/vhost.d
      - ./html:/usr/share/nginx/html
    restart: unless-stopped

  letsencrypt:
    image: nginxproxy/acme-companion
    container_name: letsencrypt
    volumes_from:
      - nginx-proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./acme:/etc/acme.sh
    environment:
      - DEFAULT_EMAIL=your-email@example.com
    restart: unless-stopped

  liap-tui:
    build:
      context: .
      dockerfile: Dockerfile.prod
    image: liap-tui:latest
    container_name: liap-tui-game
    expose:
      - "5050"
    volumes:
      - game_data:/app/data
    environment:
      # Application settings
      - DATABASE_PATH=/app/data/game_events.db
      - API_HOST=0.0.0.0
      - API_PORT=5050
      - DEBUG=false

      # HTTPS proxy settings
      - VIRTUAL_HOST=your-domain.com,www.your-domain.com
      - LETSENCRYPT_HOST=your-domain.com,www.your-domain.com
      - VIRTUAL_PORT=5050

      # WebSocket support
      - VIRTUAL_PROTO=http

      # CORS
      - ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
    restart: unless-stopped

volumes:
  game_data:
    driver: local
```

### Step 2: Deploy with HTTPS

```bash
# Stop existing containers
docker-compose down

# Start with HTTPS support
docker-compose -f docker-compose.https.yml up -d
```

## Option 3: Using AWS Certificate Manager with ALB

### Step 1: Request Certificate

```bash
# Request certificate from ACM
aws acm request-certificate \
    --domain-name your-domain.com \
    --subject-alternative-names www.your-domain.com \
    --validation-method DNS
```

### Step 2: Create Application Load Balancer

```bash
# This requires moving away from single EC2 to ALB setup
# Not recommended for free tier users due to ALB costs
```

## Post-Setup Tasks

### 1. Update Security Headers

Add to Nginx configuration:

```nginx
# Content Security Policy
add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss://your-domain.com;" always;

# Additional security
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

### 2. Configure WebSocket for WSS

Update frontend WebSocket connection:

```javascript
// In frontend/network/websocketService.js
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws/${roomId}`;
```

### 3. Monitor Certificate Expiry

Add to monitoring script:

```bash
#!/bin/bash
# Check SSL certificate expiry

DOMAIN="your-domain.com"
EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "WARNING: SSL certificate expires in $DAYS_LEFT days!"
fi
```

### 4. Test SSL Configuration

Use online tools:
- https://www.ssllabs.com/ssltest/
- https://securityheaders.com/

### 5. Update Documentation

Update all references from HTTP to HTTPS:
- README.md
- API documentation
- Deployment scripts

## Troubleshooting

### Certificate Not Renewing

```bash
# Check certbot logs
sudo journalctl -u certbot.timer

# Manually renew
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal
```

### Mixed Content Warnings

Check browser console for mixed content. Update all HTTP references to HTTPS or use protocol-relative URLs.

### WebSocket Connection Failed

Ensure Nginx configuration includes proper WebSocket headers and the frontend uses `wss://` for secure connections.

### Rate Limiting

Let's Encrypt has rate limits:
- 50 certificates per domain per week
- 5 duplicate certificates per week

## Rollback Procedure

If HTTPS causes issues:

```bash
# Disable HTTPS in Nginx
sudo rm /etc/nginx/sites-enabled/liap-tui-ssl
sudo ln -s /etc/nginx/sites-available/liap-tui /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Update docker-compose
# Change ALLOWED_ORIGINS back to HTTP
docker-compose restart
```

## Best Practices

1. **Always Test in Staging**: Use Let's Encrypt staging environment first
2. **Monitor Expiry**: Set up alerts 30 days before expiry
3. **Backup Certificates**: Keep backups of `/etc/letsencrypt/`
4. **Use Strong Ciphers**: Regularly update SSL configuration
5. **Enable HSTS**: Prevents downgrade attacks
6. **Regular Updates**: Keep Certbot and Nginx updated

---

Remember: HTTPS is essential for security, SEO, and user trust!