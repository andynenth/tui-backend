#!/bin/bash
# Fix nginx configuration on Tokyo server

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 Fixing nginx configuration on Tokyo server...${NC}"

TARGET_IP="54.250.35.226"
TARGET_KEY="~/.ssh/liap-tui-tokyo-key.pem"

# SSH into Tokyo server and fix nginx
ssh -i "$TARGET_KEY" ubuntu@$TARGET_IP << 'ENDSSH'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'

    echo -e "${YELLOW}📋 Checking Docker status...${NC}"
    docker ps

    echo -e "${YELLOW}🔍 Checking if game is running on port 8080...${NC}"
    if curl -s http://localhost:8080/api/health | grep -q "healthy"; then
        echo -e "${GREEN}✅ Game is running on port 8080${NC}"
    else
        echo -e "${RED}❌ Game is not responding on port 8080${NC}"
        echo "Starting game container..."
        docker-compose up -d
        sleep 5
    fi

    echo -e "${YELLOW}📝 Creating nginx configuration for HTTP (no SSL yet)...${NC}"
    
    # Create temporary nginx config for HTTP only
    sudo tee /etc/nginx/sites-available/liap-tui-http << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_read_timeout 86400;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://localhost:8080/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

    # Enable the site
    echo -e "${YELLOW}🔄 Enabling nginx configuration...${NC}"
    sudo ln -sf /etc/nginx/sites-available/liap-tui-http /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx config
    echo -e "${YELLOW}🧪 Testing nginx configuration...${NC}"
    sudo nginx -t
    
    # Reload nginx
    echo -e "${YELLOW}♻️  Reloading nginx...${NC}"
    sudo systemctl reload nginx
    
    echo -e "${GREEN}✅ Nginx configured!${NC}"
    
    # Test the setup
    echo -e "${YELLOW}🔍 Testing HTTP access...${NC}"
    if curl -s http://localhost/api/health | grep -q "healthy"; then
        echo -e "${GREEN}✅ Game is accessible via nginx!${NC}"
    else
        echo -e "${RED}❌ Game is not accessible via nginx${NC}"
        echo "Checking logs..."
        docker logs liap-tui-game --tail 20
    fi
ENDSSH

echo -e "${GREEN}✅ Configuration complete!${NC}"
echo -e "${GREEN}🌐 Your game should now be accessible at:${NC}"
echo "   http://$TARGET_IP"
echo
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Test the game at http://$TARGET_IP"
echo "2. Update DNS: castellan.andynenth.dev → $TARGET_IP"
echo "3. After DNS propagation, setup SSL:"
echo "   ssh -i $TARGET_KEY ubuntu@$TARGET_IP"
echo "   sudo certbot certonly --standalone -d castellan.andynenth.dev"
echo "   Then run: ./deploy-ec2-ssl-tokyo-no-rebuild.sh"