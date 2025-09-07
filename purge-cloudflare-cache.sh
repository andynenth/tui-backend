#!/bin/bash
# Purge Cloudflare cache for castellan.andynenth.dev

# Load environment variables from .env file
if [ -f "../.env" ]; then
    # Export the variables so they're available in this script
    export $(grep -v '^#' ../.env | grep -E '^(CLOUDFLARE_ZONE_ID|CLOUDFLARE_API_TOKEN)=' | xargs)
elif [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep -E '^(CLOUDFLARE_ZONE_ID|CLOUDFLARE_API_TOKEN)=' | xargs)
fi

# Configuration from environment
ZONE_ID="${CLOUDFLARE_ZONE_ID}"
API_TOKEN="${CLOUDFLARE_API_TOKEN}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if credentials are set
if [ -z "$ZONE_ID" ] || [ -z "$API_TOKEN" ]; then
    echo -e "${RED}❌ Error: Cloudflare credentials not found${NC}"
    echo ""
    echo "Please set these in your .env file:"
    echo "  CLOUDFLARE_ZONE_ID=your_zone_id"
    echo "  CLOUDFLARE_API_TOKEN=your_api_token"
    echo ""
    echo "To find these values:"
    echo "1. Zone ID: Cloudflare dashboard → Overview → Zone ID (right sidebar)"
    echo "2. API Token: Cloudflare → My Profile → API Tokens → Create Token"
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
    
    if echo "$response" | grep -q '"success":[[:space:]]*true'; then
        echo -e "${GREEN}✅ Cache purged successfully!${NC}"
        # Show zone ID if available
        zone_id=$(echo "$response" | jq -r '.result.id // empty' 2>/dev/null)
        if [ -n "$zone_id" ]; then
            echo -e "${BLUE}   Zone ID: $zone_id${NC}"
        fi
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
    
    if echo "$response" | grep -q '"success":[[:space:]]*true'; then
        echo -e "${GREEN}✅ URLs purged successfully!${NC}"
        # Show number of files purged if available
        file_count=$(echo "$response" | jq -r '.result.files | length // empty' 2>/dev/null)
        if [ -n "$file_count" ]; then
            echo -e "${BLUE}   Files purged: $file_count${NC}"
        fi
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