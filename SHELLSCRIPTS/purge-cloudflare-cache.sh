#!/bin/bash
# Purge Cloudflare cache for castellan.andynenth.dev

# Configuration
ZONE_ID="23a6d2d5eb8d91293fdaa75a2bee60fa"  # andynenth.dev zone
API_TOKEN="uCwtKKmBTDF7qjghASBfRsICJa7xV56F_c8Iafrq"  # Your API token

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if credentials are set
if [ "$ZONE_ID" = "YOUR_ZONE_ID" ] || [ "$API_TOKEN" = "YOUR_API_TOKEN" ]; then
    echo -e "${RED}❌ Error: Please set ZONE_ID and API_TOKEN in this script${NC}"
    echo "1. Find Zone ID: Cloudflare dashboard → Overview → Zone ID (right sidebar)"
    echo "2. Create API Token: Cloudflare → My Profile → API Tokens → Create Token"
    echo "   - Use template: 'Purge Cache'"
    echo "   - Or create custom with 'Zone:Cache Purge' permission"
    exit 1
fi

# Function to purge everything
purge_all() {
    echo -e "${YELLOW}🔄 Purging entire cache...${NC}"
    response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"purge_everything":true}')
    
    if echo "$response" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ Cache purged successfully!${NC}"
    else
        echo -e "${RED}❌ Error purging cache:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    fi
}

# Function to purge specific URLs
purge_urls() {
    echo -e "${YELLOW}🔄 Purging specific URLs...${NC}"
    # Main pages and static assets
    urls='["https://castellan.andynenth.dev/","https://castellan.andynenth.dev/index.html","https://castellan.andynenth.dev/bundle.js","https://castellan.andynenth.dev/bundle.css","https://castellan.andynenth.dev/favicon.ico"]'
    
    response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{\"files\":$urls}")
    
    if echo "$response" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ URLs purged successfully!${NC}"
    else
        echo -e "${RED}❌ Error purging URLs:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    fi
}

# Main menu
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Cloudflare Cache Purge Tool${NC}"
    echo "Usage: $0 [all|urls]"
    echo "  all  - Purge entire cache"
    echo "  urls - Purge specific URLs"
    exit 0
fi

case $1 in
    all)
        purge_all
        ;;
    urls)
        purge_urls
        ;;
    *)
        echo -e "${RED}Invalid option: $1${NC}"
        echo "Use: $0 [all|urls]"
        exit 1
        ;;
esac