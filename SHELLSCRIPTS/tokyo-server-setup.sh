#!/bin/bash
# Initial setup script for Tokyo EC2 instance
# Run this on the Tokyo server after first deployment

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🗾 Tokyo Server Initial Setup${NC}"

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run with sudo: sudo ./tokyo-server-setup.sh${NC}"
    exit 1
fi

# Step 1: Install Docker and Docker Compose (if not already installed)
echo -e "${GREEN}📦 Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    apt-get update
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add ubuntu user to docker group
    usermod -aG docker ubuntu
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

# Install docker-compose standalone
if ! command -v docker-compose &> /dev/null; then
    curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
fi

# Step 2: Install nginx and certbot
echo -e "${GREEN}🌐 Installing nginx and certbot...${NC}"
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# Step 3: Configure firewall
echo -e "${GREEN}🔥 Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5050/tcp  # For direct game access during testing
ufw --force enable

# Step 4: Create necessary directories
echo -e "${GREEN}📁 Creating directories...${NC}"
sudo -u ubuntu mkdir -p /home/ubuntu/liap-tui-data
sudo -u ubuntu mkdir -p /home/ubuntu/logs
sudo -u ubuntu mkdir -p /home/ubuntu/nginx-config
chmod 755 /home/ubuntu/logs

echo -e "${GREEN}✅ Basic setup complete!${NC}"
echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo "1. Deploy the game using: ./deploy-ec2-ssl-tokyo-no-rebuild.sh"
echo "2. Test the game at: http://YOUR_EC2_IP"
echo "3. Update DNS A record to point castellan.andynenth.dev to this server"
echo "4. Wait for DNS propagation (5-30 minutes)"
echo "5. Get SSL certificate:"
echo "   sudo certbot certonly --standalone -d castellan.andynenth.dev"
echo "6. Deploy again to activate SSL"
echo ""
echo -e "${GREEN}🌏 Server Info:${NC}"
echo "   Region: ap-northeast-1 (Tokyo)"
echo "   Instance IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
