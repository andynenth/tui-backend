# 🚀 Oracle Cloud Native Deployment Checklist

**Project**: liap-tui Game Server Migration
**Target**: Oracle Cloud Tokyo (155.248.175.54)
**Goal**: $17/month → $0/month cost savings
**Started**: _______________
**Completed**: _______________

---

## 📋 Phase 1: Production File Transfer

### 1.1 Local Build Preparation
- [ ] **Navigate to liap-tui project directory**
  ```bash
  cd /path/to/liap-tui
  ```

- [ ] **Build frontend production bundle**
  ```bash
  cd frontend
  npm install
  npm run build
  cd ..
  ```

- [ ] **Verify build output exists**
  ```bash
  ls -la frontend/dist/
  # Should show: index.html, static/, assets/
  ```

### 1.2 Create Production Archive
- [ ] **Create optimized production archive**
  ```bash
  tar --exclude='.git' \
      --exclude='node_modules' \
      --exclude='tests' \
      --exclude='docs' \
      --exclude='*.md' \
      --exclude='.github' \
      --exclude='frontend/src' \
      --exclude='frontend/node_modules' \
      -czf liap-tui-production.tar.gz \
      backend/ \
      frontend/dist/ \
      requirements.txt \
      package.json \
      .env.example
  ```

- [ ] **Verify archive size (should be < 50MB)**
  ```bash
  ls -lh liap-tui-production.tar.gz
  ```

### 1.3 Transfer to Oracle Cloud
- [ ] **Upload to Oracle server**
  ```bash
  scp liap-tui-production.tar.gz opc@155.248.175.54:~/
  ```

- [ ] **SSH into Oracle server**
  ```bash
  ssh -i ~/.ssh/oracle-tokyo-key opc@155.248.175.54
  ```

- [ ] **Extract files on server**
  ```bash
  cd /home/opc
  tar -xzf liap-tui-production.tar.gz
  rm liap-tui-production.tar.gz
  ls -la  # Verify liap-tui directory created
  ```

---

## 📋 Phase 2: Environment Setup

### 2.1 Python Runtime Installation
- [ ] **Install Python 3.11**
  ```bash
  sudo dnf install -y python3.11 python3.11-pip python3.11-devel
  ```

- [ ] **Verify Python installation**
  ```bash
  python3.11 --version
  # Should show: Python 3.11.x
  ```

### 2.2 Virtual Environment Setup
- [ ] **Navigate to project directory**
  ```bash
  cd /home/opc/liap-tui
  ```

- [ ] **Create virtual environment**
  ```bash
  python3.11 -m venv venv
  ```

- [ ] **Activate virtual environment**
  ```bash
  source venv/bin/activate
  ```

- [ ] **Verify activation (prompt should show (venv))**

- [ ] **Install Python dependencies**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **Verify key packages installed**
  ```bash
  pip list | grep -E "(fastapi|uvicorn|websockets)"
  ```

### 2.3 Frontend Files Setup
- [ ] **Verify frontend build exists**
  ```bash
  ls -la frontend/dist/
  ```

- [ ] **Create backend static directory**
  ```bash
  mkdir -p backend/static
  ```

- [ ] **Copy frontend build to backend static**
  ```bash
  cp -r frontend/dist/* backend/static/ 2>/dev/null || true
  ```

- [ ] **Verify static files copied**
  ```bash
  ls -la backend/static/
  ```

---

## 📋 Phase 3: System Service Configuration

### 3.1 Create Systemd Service
- [ ] **Create service file**
  ```bash
  sudo tee /etc/systemd/system/liap-tui.service << 'EOF'
  [Unit]
  Description=Liap TUI Game Backend
  After=network.target
  StartLimitIntervalSec=0

  [Service]
  Type=exec
  User=opc
  Group=opc
  WorkingDirectory=/home/opc/liap-tui
  Environment=PATH=/home/opc/liap-tui/venv/bin
  Environment=PYTHONPATH=/home/opc/liap-tui
  ExecStart=/home/opc/liap-tui/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8080 --workers 1
  Restart=always
  RestartSec=3
  StandardOutput=journal
  StandardError=journal
  MemoryMax=512M
  MemoryHigh=400M

  [Install]
  WantedBy=multi-user.target
  EOF
  ```

### 3.2 Service Management
- [ ] **Reload systemd daemon**
  ```bash
  sudo systemctl daemon-reload
  ```

- [ ] **Enable service for auto-start**
  ```bash
  sudo systemctl enable liap-tui
  ```

- [ ] **Start the service**
  ```bash
  sudo systemctl start liap-tui
  ```

- [ ] **Check service status (should be active/running)**
  ```bash
  sudo systemctl status liap-tui
  ```

- [ ] **Test application directly**
  ```bash
  curl http://127.0.0.1:8080/health
  # Should return health check response
  ```

---

## 📋 Phase 4: Nginx Reverse Proxy

### 4.1 Nginx Installation
- [ ] **Install Nginx**
  ```bash
  sudo dnf install -y nginx
  ```

- [ ] **Enable Nginx for auto-start**
  ```bash
  sudo systemctl enable nginx
  ```

### 4.2 Nginx Configuration
- [ ] **Create site configuration**
  ```bash
  sudo tee /etc/nginx/conf.d/liap-tui.conf << 'EOF'
  server {
      listen 80;
      server_name 155.248.175.54 castellan.andynenth.dev;
      client_max_body_size 10M;

      # Static files
      location /static/ {
          alias /home/opc/liap-tui/backend/static/;
          expires 30d;
          add_header Cache-Control "public, immutable";
      }

      # API and WebSocket proxy
      location / {
          proxy_pass http://127.0.0.1:8080;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_cache_bypass $http_upgrade;

          proxy_connect_timeout 60s;
          proxy_send_timeout 60s;
          proxy_read_timeout 60s;
      }

      location /health {
          proxy_pass http://127.0.0.1:8080/health;
          access_log off;
      }
  }
  EOF
  ```

### 4.3 Nginx Service Start
- [ ] **Test Nginx configuration**
  ```bash
  sudo nginx -t
  # Should show: syntax is ok, test is successful
  ```

- [ ] **Start Nginx**
  ```bash
  sudo systemctl start nginx
  ```

- [ ] **Check Nginx status**
  ```bash
  sudo systemctl status nginx
  ```

- [ ] **Test web access**
  ```bash
  curl http://127.0.0.1/
  # Should return your application
  ```

---

## 📋 Phase 5: Environment Configuration

### 5.1 Production Environment Variables
- [ ] **Create production .env file**
  ```bash
  cd /home/opc/liap-tui
  tee .env << 'EOF'
  ENV=production
  HOST=127.0.0.1
  PORT=8080
  DEBUG=false
  EOF
  ```

### 5.2 File Permissions
- [ ] **Set proper ownership**
  ```bash
  sudo chown -R opc:opc /home/opc/liap-tui
  ```

- [ ] **Set executable permissions**
  ```bash
  chmod +x /home/opc/liap-tui/venv/bin/uvicorn
  ```

- [ ] **Restart service with new environment**
  ```bash
  sudo systemctl restart liap-tui
  sudo systemctl status liap-tui
  ```

---

## 📋 Phase 6: Firewall & Security

### 6.1 Firewall Configuration
- [ ] **Configure firewall ports**
  ```bash
  sudo firewall-cmd --permanent --add-service=http
  sudo firewall-cmd --permanent --add-service=https
  sudo firewall-cmd --permanent --add-service=ssh
  sudo firewall-cmd --reload
  ```

- [ ] **Verify firewall rules**
  ```bash
  sudo firewall-cmd --list-all
  # Should show: services: http https ssh
  ```

### 6.2 SELinux Configuration
- [ ] **Check SELinux status**
  ```bash
  getenforce
  ```

- [ ] **Configure SELinux for Nginx (if enforcing)**
  ```bash
  sudo setsebool -P httpd_can_network_connect 1
  sudo setsebool -P httpd_can_network_relay 1
  ```

- [ ] **Test external access**
  ```bash
  curl http://155.248.175.54/
  # Should return your application from external IP
  ```

---

## 📋 Phase 7: Monitoring & Logging

### 7.1 Log Management Setup
- [ ] **View application logs**
  ```bash
  sudo journalctl -u liap-tui -f
  # Should show recent application logs
  ```

- [ ] **View Nginx logs**
  ```bash
  sudo tail -f /var/log/nginx/access.log
  sudo tail -f /var/log/nginx/error.log
  ```

### 7.2 Log Rotation
- [ ] **Create log rotation config**
  ```bash
  sudo tee /etc/logrotate.d/liap-tui << 'EOF'
  /var/log/nginx/*.log {
      daily
      missingok
      rotate 7
      compress
      delaycompress
      notifempty
      create 644 nginx nginx
      postrotate
          systemctl reload nginx
      endscript
  }
  EOF
  ```

---

## 📋 Phase 8: SSL Certificate

### 8.1 Certbot Installation
- [ ] **Install Certbot**
  ```bash
  sudo dnf install -y certbot python3-certbot-nginx
  ```

### 8.2 SSL Certificate Generation
- [ ] **Stop Nginx for standalone mode**
  ```bash
  sudo systemctl stop nginx
  ```

- [ ] **Generate SSL certificate (AFTER DNS points to Oracle)**
  ```bash
  sudo certbot certonly --standalone -d castellan.andynenth.dev
  # Only run this AFTER DNS is updated!
  ```

- [ ] **Restart Nginx**
  ```bash
  sudo systemctl start nginx
  ```

### 8.3 Auto-renewal Setup
- [ ] **Test certificate renewal**
  ```bash
  sudo certbot renew --dry-run
  ```

- [ ] **Add renewal to crontab**
  ```bash
  echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
  ```

---

## 📋 Phase 9: Performance Optimization

### 9.1 Memory Optimization
- [ ] **Create swap file for memory bursts**
  ```bash
  sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```

- [ ] **Verify swap is active**
  ```bash
  free -h
  # Should show swap space available
  ```

### 9.2 Resource Monitoring
- [ ] **Install monitoring tools**
  ```bash
  sudo dnf install -y htop
  ```

- [ ] **Check resource usage**
  ```bash
  htop
  free -h
  df -h
  ```

---

## 📋 Phase 10: Testing & Validation

### 10.1 Functional Testing
- [ ] **Test application health endpoint**
  ```bash
  curl http://localhost:8080/health
  ```

- [ ] **Test Nginx proxy**
  ```bash
  curl http://localhost/
  ```

- [ ] **Test from external IP**
  ```bash
  curl http://155.248.175.54/
  ```

### 10.2 Performance Testing
- [ ] **Check memory usage**
  ```bash
  ps aux | grep uvicorn
  free -h
  ```

- [ ] **Check service status**
  ```bash
  sudo systemctl status liap-tui
  sudo systemctl status nginx
  ```

- [ ] **Test WebSocket connections (if applicable)**
  ```bash
  # Use browser dev tools or wscat if available
  ```

---

## 📋 Phase 11: DNS Cutover

### 11.1 Pre-cutover Preparation
- [ ] **Lower DNS TTL on current domain (do this 24h before cutover)**
  ```
  Set TTL to 300 seconds (5 minutes)
  Wait 24 hours for old TTL to expire
  ```

### 11.2 Testing Before DNS Change
- [ ] **Test with IP address directly**
  ```bash
  curl http://155.248.175.54/
  ```

- [ ] **Test in browser with IP**
  ```
  Open: http://155.248.175.54
  Verify: Game loads and functions correctly
  ```

### 11.3 DNS Update
- [ ] **Update DNS A record**
  ```
  Record: castellan.andynenth.dev
  Type: A
  Value: 155.248.175.54
  TTL: 300
  ```

- [ ] **Monitor DNS propagation**
  ```bash
  dig castellan.andynenth.dev
  nslookup castellan.andynenth.dev
  ```

- [ ] **Test domain access**
  ```bash
  curl http://castellan.andynenth.dev/
  ```

### 11.4 SSL Configuration (After DNS)
- [ ] **Generate SSL certificate**
  ```bash
  sudo systemctl stop nginx
  sudo certbot certonly --standalone -d castellan.andynenth.dev
  sudo systemctl start nginx
  ```

- [ ] **Update Nginx for HTTPS**
  ```bash
  # Add SSL configuration to nginx conf
  # Redirect HTTP to HTTPS
  ```

---

## 📋 Phase 12: Final Validation

### 12.1 Complete Functionality Test
- [ ] **Test HTTPS access**
  ```bash
  curl https://castellan.andynenth.dev/
  ```

- [ ] **Test game functionality in browser**
  ```
  Navigate to: https://castellan.andynenth.dev
  Test: Complete game flow
  Verify: WebSocket connections work
  Check: No console errors
  ```

### 12.2 Performance Validation
- [ ] **Monitor resource usage under load**
  ```bash
  htop
  sudo journalctl -u liap-tui -f
  ```

- [ ] **Verify auto-restart functionality**
  ```bash
  sudo systemctl restart liap-tui
  sudo systemctl status liap-tui
  ```

### 12.3 AWS Cleanup (After 7 days stable operation)
- [ ] **Verify Oracle deployment is stable**
- [ ] **Document any issues and resolutions**
- [ ] **Terminate AWS instances**
  ```bash
  # Run on your local machine:
  aws ec2 terminate-instances --region ap-northeast-1 --instance-ids [old-instance-id]
  aws ec2 terminate-instances --region us-east-1 --instance-ids [old-instance-id]
  ```

---

## 🎯 Success Criteria Checklist

- [ ] **Application accessible via domain**: https://castellan.andynenth.dev
- [ ] **SSL certificate valid and working**
- [ ] **WebSocket connections functional**
- [ ] **Memory usage stable under 400MB**
- [ ] **No service crashes or restarts**
- [ ] **Logs capturing properly**
- [ ] **Auto-restart on reboot working**
- [ ] **DNS propagated globally**
- [ ] **AWS resources terminated**
- [ ] **Monthly cost confirmed as $0**

---

## 📝 Notes & Issues

**Date**: _______
**Issue**: ________________________________
**Resolution**: ____________________________

**Date**: _______
**Issue**: ________________________________
**Resolution**: ____________________________

**Date**: _______
**Issue**: ________________________________
**Resolution**: ____________________________

---

## 🎉 Deployment Complete!

**Completed Date**: _______________
**Final Domain**: https://castellan.andynenth.dev
**Monthly Savings**: $17/month → $0/month
**Performance**: _______________
**Uptime**: _______________

**✅ Migration Successful!**
