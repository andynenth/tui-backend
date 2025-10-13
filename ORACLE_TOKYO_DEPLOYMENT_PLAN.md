# Oracle Cloud Tokyo Deployment Plan
**Target**: Deploy liap-tui game to Oracle Cloud Always Free ARM instances in Tokyo region
**Goal**: Eliminate $17/month AWS costs with free, more powerful infrastructure
**Timeline**: 1-2 days for complete migration

## 📋 Phase 1: Account & Infrastructure Setup

### 1.1 Oracle Cloud Account Creation
- [ ] **Create Oracle Cloud account** at https://cloud.oracle.com
- [ ] **Verify email address and phone number**
- [ ] **Complete identity verification** (may require credit card for verification)
- [ ] **Access Oracle Cloud Console**
- [ ] **Confirm Always Free tier eligibility**

### 1.2 Region Selection & VCN Setup
- [ ] **Select Tokyo region** (ap-tokyo-1) in console
- [ ] **Create Virtual Cloud Network (VCN)**
  ```
  Name: liap-tui-vcn
  CIDR: 10.0.0.0/16
  DNS Resolution: Enabled
  DNS Label: liaptui
  ```
- [ ] **Create public subnet**
  ```
  Name: public-subnet
  CIDR: 10.0.1.0/24
  Route Table: Default Route Table
  Security List: Default Security List
  ```
- [ ] **Configure Internet Gateway** (should be auto-created)
- [ ] **Verify internet connectivity** in route table

### 1.3 Security Configuration
- [ ] **Update Default Security List** with required ports:
  ```
  Ingress Rules:
  - Port 22 (SSH): 0.0.0.0/0
  - Port 80 (HTTP): 0.0.0.0/0
  - Port 443 (HTTPS): 0.0.0.0/0
  - Port 8080 (App): 0.0.0.0/0 (temporary)
  ```
- [ ] **Generate SSH key pair** for instance access
  ```bash
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle-tokyo-key
  chmod 600 ~/.ssh/oracle-tokyo-key
  ```

---

## 📋 Phase 2: Compute Instance Creation

### 2.1 Always Free ARM Instance
- [ ] **Navigate to Compute > Instances**
- [ ] **Create Instance** with specifications:
  ```
  Name: liap-tui-tokyo-arm
  Image: Oracle Linux 8 (ARM)
  Shape: VM.Standard.A1.Flex
  OCPUs: 4 (maximum free tier)
  Memory: 24 GB (maximum free tier)
  ```
- [ ] **Configure networking**:
  ```
  VCN: liap-tui-vcn
  Subnet: public-subnet
  Assign Public IP: Yes
  ```
- [ ] **Add SSH public key** (from step 1.3)
- [ ] **Wait for instance to reach RUNNING state** (~2-3 minutes)
- [ ] **Note down Public IP address**

### 2.2 Instance Access Verification
- [ ] **Test SSH connection**:
  ```bash
  ssh -i ~/.ssh/oracle-tokyo-key opc@[PUBLIC_IP]
  ```
- [ ] **Verify ARM architecture**:
  ```bash
  uname -m  # Should show: aarch64
  lscpu     # Should show ARM architecture
  ```
- [ ] **Check available resources**:
  ```bash
  nproc     # Should show: 4
  free -h   # Should show: ~24GB total memory
  df -h     # Should show: ~45GB boot volume
  ```

---

## 📋 Phase 3: Environment Configuration

### 3.1 System Updates & Base Packages
- [ ] **Update system packages**:
  ```bash
  sudo dnf update -y
  sudo dnf install -y git curl wget unzip
  ```
- [ ] **Install development tools**:
  ```bash
  sudo dnf groupinstall -y "Development Tools"
  sudo dnf install -y openssl-devel zlib-devel
  ```

### 3.2 Python 3.11 Installation
- [ ] **Install Python 3.11**:
  ```bash
  sudo dnf install -y python3.11 python3.11-pip python3.11-devel
  sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
  sudo alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1
  ```
- [ ] **Verify Python installation**:
  ```bash
  python3 --version  # Should show: Python 3.11.x
  pip3 --version
  ```

### 3.3 Node.js Installation (Latest LTS)
- [ ] **Install Node.js via NodeSource**:
  ```bash
  curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
  sudo dnf install -y nodejs
  ```
- [ ] **Verify Node.js installation**:
  ```bash
  node --version   # Should show: v20.x.x or later
  npm --version
  ```

### 3.4 Nginx Installation & Configuration
- [ ] **Install Nginx**:
  ```bash
  sudo dnf install -y nginx
  sudo systemctl enable nginx
  sudo systemctl start nginx
  ```
- [ ] **Test Nginx is running**:
  ```bash
  sudo systemctl status nginx
  curl http://localhost
  ```
- [ ] **Configure firewall** (Oracle Linux uses firewalld):
  ```bash
  sudo firewall-cmd --permanent --add-service=http
  sudo firewall-cmd --permanent --add-service=https
  sudo firewall-cmd --permanent --add-port=8080/tcp
  sudo firewall-cmd --reload
  ```

---

## 📋 Phase 4: Application Deployment

### 4.1 Code Deployment
- [ ] **Clone repository**:
  ```bash
  cd /home/opc
  git clone [YOUR_REPO_URL] liap-tui
  cd liap-tui
  ```
- [ ] **Set up Python virtual environment**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- [ ] **Install frontend dependencies**:
  ```bash
  cd frontend
  npm install
  npm run build
  cd ..
  ```

### 4.2 Environment Configuration
- [ ] **Create environment file**:
  ```bash
  cp .env.example .env  # If exists
  # Or create new .env with required variables
  ```
- [ ] **Configure application for production**:
  ```bash
  # Update any config files for Oracle environment
  # Set correct host/port bindings
  # Configure WebSocket settings
  ```

### 4.3 Application Services Setup
- [ ] **Create systemd service for backend**:
  ```bash
  sudo tee /etc/systemd/system/liap-tui.service << 'EOF'
  [Unit]
  Description=Liap TUI Game Backend
  After=network.target

  [Service]
  Type=exec
  User=opc
  WorkingDirectory=/home/opc/liap-tui
  Environment=PATH=/home/opc/liap-tui/venv/bin
  ExecStart=/home/opc/liap-tui/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
  Restart=always
  RestartSec=10

  [Install]
  WantedBy=multi-user.target
  EOF
  ```
- [ ] **Enable and start service**:
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable liap-tui
  sudo systemctl start liap-tui
  ```
- [ ] **Verify service is running**:
  ```bash
  sudo systemctl status liap-tui
  curl http://localhost:8080/health  # Test health endpoint
  ```

### 4.4 Nginx Reverse Proxy Configuration
- [ ] **Create Nginx site configuration**:
  ```bash
  sudo tee /etc/nginx/conf.d/liap-tui.conf << 'EOF'
  server {
      listen 80;
      server_name [PUBLIC_IP] castellan.andynenth.dev;

      location / {
          proxy_pass http://localhost:8080;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  EOF
  ```
- [ ] **Test Nginx configuration**:
  ```bash
  sudo nginx -t
  sudo systemctl reload nginx
  ```

---

## 📋 Phase 5: Testing & Validation

### 5.1 Basic Connectivity Tests
- [ ] **Test HTTP access**:
  ```bash
  curl http://[PUBLIC_IP]
  # Should return your application response
  ```
- [ ] **Test from external network**:
  ```
  Open browser: http://[PUBLIC_IP]
  Verify game loads and functions
  ```
- [ ] **Test WebSocket connections**:
  ```
  Use browser dev tools to verify WebSocket connects
  Test real-time game functionality
  ```

### 5.2 Performance Validation
- [ ] **Check resource usage**:
  ```bash
  htop           # Monitor CPU/memory usage
  iotop          # Monitor disk I/O
  netstat -tulpn # Check listening ports
  ```
- [ ] **Load testing** (optional):
  ```bash
  # Use curl or browser to test multiple connections
  # Verify performance meets expectations
  ```

### 5.3 SSL Certificate Setup
- [ ] **Install Certbot**:
  ```bash
  sudo dnf install -y certbot python3-certbot-nginx
  ```
- [ ] **Stop nginx temporarily** (for standalone mode):
  ```bash
  sudo systemctl stop nginx
  ```
- [ ] **Obtain SSL certificate** (after DNS points to Oracle):
  ```bash
  sudo certbot certonly --standalone -d castellan.andynenth.dev
  ```
- [ ] **Update Nginx configuration for HTTPS**:
  ```bash
  # Add SSL configuration to nginx
  # Redirect HTTP to HTTPS
  ```
- [ ] **Restart nginx**:
  ```bash
  sudo systemctl start nginx
  ```

---

## 📋 Phase 6: DNS Migration & Go-Live

### 6.1 Parallel Testing Phase
- [ ] **Update local hosts file for testing**:
  ```bash
  # Add to /etc/hosts (or C:\Windows\System32\drivers\etc\hosts on Windows):
  [ORACLE_PUBLIC_IP] castellan.andynenth.dev
  ```
- [ ] **Test complete functionality** with domain name
- [ ] **Verify SSL works** (after certificate installation)
- [ ] **Test from multiple networks/devices**

### 6.2 DNS Cutover
- [ ] **Update DNS A record**:
  ```
  Change: castellan.andynenth.dev
  From: [AWS_IP] (43.207.88.153)
  To: [ORACLE_IP]
  TTL: 300 (5 minutes for faster propagation)
  ```
- [ ] **Monitor DNS propagation**:
  ```bash
  nslookup castellan.andynenth.dev
  dig castellan.andynenth.dev
  ```
- [ ] **Test from multiple locations** after propagation

### 6.3 Go-Live Monitoring
- [ ] **Monitor application logs**:
  ```bash
  sudo journalctl -u liap-tui -f
  tail -f /var/log/nginx/access.log
  ```
- [ ] **Check for errors or issues**
- [ ] **Verify user connectivity and functionality**
- [ ] **Monitor resource usage during live traffic**

---

## 📋 Phase 7: Post-Deployment & Cleanup

### 7.1 Monitoring & Maintenance Setup
- [ ] **Set up log rotation**:
  ```bash
  sudo logrotate -d /etc/logrotate.d/nginx
  ```
- [ ] **Configure automatic updates**:
  ```bash
  sudo dnf install -y dnf-automatic
  sudo systemctl enable dnf-automatic.timer
  ```
- [ ] **Set up basic monitoring script** (CPU, memory, disk usage)
- [ ] **Create backup strategy** for application data

### 7.2 Documentation & Handoff
- [ ] **Document server access details**:
  ```
  Server IP: [ORACLE_PUBLIC_IP]
  SSH Key: ~/.ssh/oracle-tokyo-key
  User: opc
  Services: liap-tui.service, nginx
  ```
- [ ] **Update deployment scripts** for Oracle environment
- [ ] **Create runbook** for common maintenance tasks

### 7.3 AWS Cleanup (After 30 Days)
- [ ] **Verify Oracle deployment is stable**
- [ ] **Test failover procedures**
- [ ] **Schedule AWS resource cleanup**:
  ```bash
  # Terminate remaining AWS instances
  # Release Elastic IPs
  # Delete unused EBS volumes
  # Remove load balancers
  ```
- [ ] **Calculate actual cost savings**

---

## 🚨 Rollback Plan (Emergency)

### If Oracle Deployment Fails:
1. **Keep AWS instances running** during testing phase
2. **Revert DNS** back to AWS IP instantly
3. **Use AWS AMI backup** to restore if needed
4. **Document lessons learned** for retry

### Success Criteria:
- [ ] **Application loads correctly** on Oracle
- [ ] **WebSocket connections work** properly
- [ ] **SSL certificate installed** and working
- [ ] **DNS propagated** globally
- [ ] **Performance equals or exceeds** AWS setup
- [ ] **Zero downtime** during DNS cutover

---

## 💰 Expected Outcome
**Monthly Cost Reduction**: $17/month → $0/month = $204/year savings
**Performance Improvement**: 1 core, 1GB → 4 cores, 24GB
**Geographic Coverage**: Same Tokyo region, same latency benefits
