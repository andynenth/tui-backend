#!/bin/bash
# Security Audit Script for Liap Tui EC2 Deployment

set -e

# Configuration
EC2_HOST="${EC2_HOST:-your-ec2-ip-here}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-~/.ssh/your-key.pem}"
INSTANCE_ID="${INSTANCE_ID:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Security score tracking
SECURITY_SCORE=100
ISSUES=()
WARNINGS=()
RECOMMENDATIONS=()

# Check configuration
if [ "$EC2_HOST" = "your-ec2-ip-here" ]; then
    echo -e "${RED}❌ Error: Please set EC2_HOST environment variable${NC}"
    exit 1
fi

# Function to run remote command
run_remote() {
    ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "$1" 2>/dev/null
}

echo -e "${BLUE}🔒 Security Audit for Liap Tui${NC}"
echo -e "${BLUE}==============================${NC}"
echo -e "Host: ${EC2_HOST}"
echo -e "Date: $(date)"
echo ""

# 1. Check SSH Configuration
echo -e "${BLUE}1. SSH Security${NC}"

# Check for password authentication
PASSWORD_AUTH=$(run_remote "grep '^PasswordAuthentication' /etc/ssh/sshd_config | awk '{print \$2}'" || echo "yes")
if [ "$PASSWORD_AUTH" = "yes" ]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 10))
    ISSUES+=("SSH password authentication is enabled")
    RECOMMENDATIONS+=("Disable password authentication: sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config")
    echo -e "${RED}  ❌ Password authentication enabled${NC}"
else
    echo -e "${GREEN}  ✅ Password authentication disabled${NC}"
fi

# Check for root login
ROOT_LOGIN=$(run_remote "grep '^PermitRootLogin' /etc/ssh/sshd_config | awk '{print \$2}'" || echo "yes")
if [ "$ROOT_LOGIN" = "yes" ]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 10))
    ISSUES+=("Root SSH login is permitted")
    RECOMMENDATIONS+=("Disable root login: sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config")
    echo -e "${RED}  ❌ Root login permitted${NC}"
else
    echo -e "${GREEN}  ✅ Root login disabled${NC}"
fi

# Check SSH port
SSH_PORT=$(run_remote "grep '^Port' /etc/ssh/sshd_config | awk '{print \$2}'" || echo "22")
if [ "$SSH_PORT" = "22" ]; then
    WARNINGS+=("SSH running on default port 22")
    echo -e "${YELLOW}  ⚠️  SSH on default port${NC}"
else
    echo -e "${GREEN}  ✅ SSH on non-standard port${NC}"
fi

# 2. System Updates
echo -e "\n${BLUE}2. System Updates${NC}"

UPDATES_AVAILABLE=$(run_remote "sudo apt update > /dev/null 2>&1 && apt list --upgradable 2>/dev/null | grep -c upgradable" || echo "0")
if [ "$UPDATES_AVAILABLE" -gt 0 ]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 5))
    WARNINGS+=("$UPDATES_AVAILABLE system updates available")
    echo -e "${YELLOW}  ⚠️  ${UPDATES_AVAILABLE} updates available${NC}"
else
    echo -e "${GREEN}  ✅ System up to date${NC}"
fi

# Check for security updates
SECURITY_UPDATES=$(run_remote "sudo apt list --upgradable 2>/dev/null | grep -c security" || echo "0")
if [ "$SECURITY_UPDATES" -gt 0 ]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 10))
    ISSUES+=("$SECURITY_UPDATES security updates pending")
    RECOMMENDATIONS+=("Install security updates: sudo apt update && sudo apt upgrade -y")
    echo -e "${RED}  ❌ ${SECURITY_UPDATES} security updates pending${NC}"
fi

# 3. Firewall Status
echo -e "\n${BLUE}3. Firewall Configuration${NC}"

UFW_STATUS=$(run_remote "sudo ufw status | grep -c 'Status: active'" || echo "0")
if [ "$UFW_STATUS" -eq 0 ]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 15))
    ISSUES+=("Firewall is not active")
    RECOMMENDATIONS+=("Enable firewall: sudo ufw enable")
    echo -e "${RED}  ❌ Firewall inactive${NC}"
else
    echo -e "${GREEN}  ✅ Firewall active${NC}"

    # Check open ports
    echo -e "${YELLOW}  Open ports:${NC}"
    run_remote "sudo ufw status | grep ALLOW" | sed 's/^/    /'
fi

# 4. Docker Security
echo -e "\n${BLUE}4. Docker Security${NC}"

# Check if Docker daemon is exposed
DOCKER_EXPOSED=$(run_remote "sudo netstat -tlnp | grep -c ':2375\\|:2376'" || echo "0")
if [ "$DOCKER_EXPOSED" -gt 0 ]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 20))
    ISSUES+=("Docker daemon exposed on network")
    echo -e "${RED}  ❌ Docker daemon exposed${NC}"
else
    echo -e "${GREEN}  ✅ Docker daemon not exposed${NC}"
fi

# Check Docker version
DOCKER_VERSION=$(run_remote "docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+'" || echo "unknown")
echo -e "  Docker version: ${DOCKER_VERSION}"

# Check for running containers as root
ROOT_CONTAINERS=$(run_remote "docker ps -q | xargs -I {} docker inspect {} --format '{{.Config.User}}' | grep -c '^$\\|^root$'" || echo "0")
if [ "$ROOT_CONTAINERS" -gt 0 ]; then
    WARNINGS+=("$ROOT_CONTAINERS containers running as root")
    echo -e "${YELLOW}  ⚠️  ${ROOT_CONTAINERS} containers running as root${NC}"
else
    echo -e "${GREEN}  ✅ No containers running as root${NC}"
fi

# 5. Application Security
echo -e "\n${BLUE}5. Application Security${NC}"

# Check HTTPS
if ! curl -k https://${EC2_HOST} > /dev/null 2>&1; then
    SECURITY_SCORE=$((SECURITY_SCORE - 10))
    WARNINGS+=("HTTPS not configured")
    RECOMMENDATIONS+=("Implement HTTPS with Let's Encrypt")
    echo -e "${YELLOW}  ⚠️  HTTPS not configured${NC}"
else
    echo -e "${GREEN}  ✅ HTTPS configured${NC}"
fi

# Check for exposed debug endpoints
DEBUG_EXPOSED=$(curl -s http://${EC2_HOST}/api/debug/room-stats > /dev/null 2>&1 && echo "1" || echo "0")
if [ "$DEBUG_EXPOSED" = "1" ]; then
    WARNINGS+=("Debug endpoints accessible")
    echo -e "${YELLOW}  ⚠️  Debug endpoints exposed${NC}"
fi

# Check environment variables
SENSITIVE_ENV=$(run_remote "docker exec liap-tui-game env | grep -E 'PASSWORD|SECRET|KEY|TOKEN' | wc -l" || echo "0")
if [ "$SENSITIVE_ENV" -gt 0 ]; then
    WARNINGS+=("Potential sensitive data in environment variables")
    echo -e "${YELLOW}  ⚠️  Check environment variables for secrets${NC}"
fi

# 6. Database Security
echo -e "\n${BLUE}6. Database Security${NC}"

# Check database file permissions
DB_PERMS=$(run_remote "ls -l /home/ubuntu/liap-tui-data/game_events.db 2>/dev/null | awk '{print \$1}'" || echo "")
if [[ "$DB_PERMS" == *"rw-rw-rw-"* ]]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 5))
    ISSUES+=("Database file has world-writable permissions")
    echo -e "${RED}  ❌ Database world-writable${NC}"
else
    echo -e "${GREEN}  ✅ Database permissions OK${NC}"
fi

# Check backup encryption
ENCRYPTED_BACKUPS=$(run_remote "ls /home/ubuntu/backups/*.gpg 2>/dev/null | wc -l" || echo "0")
if [ "$ENCRYPTED_BACKUPS" -eq 0 ]; then
    WARNINGS+=("Backups are not encrypted")
    RECOMMENDATIONS+=("Encrypt backups: gpg -c backup.tar.gz")
    echo -e "${YELLOW}  ⚠️  Backups not encrypted${NC}"
else
    echo -e "${GREEN}  ✅ ${ENCRYPTED_BACKUPS} encrypted backups found${NC}"
fi

# 7. Network Security
echo -e "\n${BLUE}7. Network Security${NC}"

# Check for unusual listening ports
LISTENING_PORTS=$(run_remote "sudo netstat -tlnp | grep -v '127.0.0.1\\|::1' | grep LISTEN | wc -l" || echo "0")
echo -e "  Listening ports: ${LISTENING_PORTS}"

# Check for failed login attempts
FAILED_LOGINS=$(run_remote "sudo grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -24h | wc -l" || echo "0")
if [ "$FAILED_LOGINS" -gt 100 ]; then
    SECURITY_SCORE=$((SECURITY_SCORE - 5))
    WARNINGS+=("High number of failed login attempts: $FAILED_LOGINS")
    RECOMMENDATIONS+=("Consider installing fail2ban")
    echo -e "${YELLOW}  ⚠️  ${FAILED_LOGINS} failed login attempts (24h)${NC}"
elif [ "$FAILED_LOGINS" -gt 0 ]; then
    echo -e "${YELLOW}  ⚠️  ${FAILED_LOGINS} failed login attempts (24h)${NC}"
else
    echo -e "${GREEN}  ✅ No failed login attempts${NC}"
fi

# 8. AWS Security (if instance ID provided)
if [ ! -z "$INSTANCE_ID" ]; then
    echo -e "\n${BLUE}8. AWS Security${NC}"

    # Check security groups
    SECURITY_GROUPS=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId' --output text 2>/dev/null || echo "")
    if [ ! -z "$SECURITY_GROUPS" ]; then
        echo -e "  Security Groups: ${SECURITY_GROUPS}"

        # Check for overly permissive rules
        for sg in $SECURITY_GROUPS; do
            OPEN_RULES=$(aws ec2 describe-security-groups --group-ids $sg --query 'SecurityGroups[0].IpPermissions[?FromPort==`22` && IpRanges[?CidrIp==`0.0.0.0/0`]]' --output text 2>/dev/null || echo "")
            if [ ! -z "$OPEN_RULES" ]; then
                SECURITY_SCORE=$((SECURITY_SCORE - 10))
                ISSUES+=("SSH (port 22) open to the world in security group $sg")
                echo -e "${RED}    ❌ SSH open to 0.0.0.0/0 in $sg${NC}"
            fi
        done
    fi
fi

# 9. Logging and Monitoring
echo -e "\n${BLUE}9. Logging & Monitoring${NC}"

# Check if logs are being rotated
LOG_ROTATION=$(run_remote "ls /etc/logrotate.d/ | grep -c docker" || echo "0")
if [ "$LOG_ROTATION" -eq 0 ]; then
    WARNINGS+=("Docker logs not configured for rotation")
    echo -e "${YELLOW}  ⚠️  Log rotation not configured${NC}"
else
    echo -e "${GREEN}  ✅ Log rotation configured${NC}"
fi

# Check disk space for logs
LOG_SIZE=$(run_remote "du -sh /var/log 2>/dev/null | awk '{print \$1}'" || echo "unknown")
echo -e "  Log directory size: ${LOG_SIZE}"

# Generate Security Score and Report
echo -e "\n${BLUE}═══════════════════════════════${NC}"
echo -e "${BLUE}Security Score: ${SECURITY_SCORE}/100${NC}"

if [ $SECURITY_SCORE -ge 90 ]; then
    GRADE="A"
    GRADE_COLOR=$GREEN
elif [ $SECURITY_SCORE -ge 80 ]; then
    GRADE="B"
    GRADE_COLOR=$GREEN
elif [ $SECURITY_SCORE -ge 70 ]; then
    GRADE="C"
    GRADE_COLOR=$YELLOW
elif [ $SECURITY_SCORE -ge 60 ]; then
    GRADE="D"
    GRADE_COLOR=$YELLOW
else
    GRADE="F"
    GRADE_COLOR=$RED
fi

echo -e "${GRADE_COLOR}Grade: ${GRADE}${NC}"
echo -e "${BLUE}═══════════════════════════════${NC}"

# List issues
if [ ${#ISSUES[@]} -gt 0 ]; then
    echo -e "\n${RED}🚨 Critical Issues:${NC}"
    for issue in "${ISSUES[@]}"; do
        echo -e "  • $issue"
    done
fi

# List warnings
if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  Warnings:${NC}"
    for warning in "${WARNINGS[@]}"; do
        echo -e "  • $warning"
    done
fi

# List recommendations
if [ ${#RECOMMENDATIONS[@]} -gt 0 ]; then
    echo -e "\n${BLUE}💡 Recommendations:${NC}"
    for rec in "${RECOMMENDATIONS[@]}"; do
        echo -e "  • $rec"
    done
fi

# Additional security recommendations
echo -e "\n${BLUE}🔐 Security Best Practices:${NC}"
echo -e "  1. Enable MFA for AWS account"
echo -e "  2. Use AWS Systems Manager Session Manager instead of SSH"
echo -e "  3. Implement AWS CloudTrail for audit logging"
echo -e "  4. Set up AWS Config for compliance monitoring"
echo -e "  5. Use AWS Secrets Manager for sensitive data"
echo -e "  6. Enable VPC Flow Logs for network monitoring"
echo -e "  7. Implement regular security scanning with AWS Inspector"

# Generate report file
REPORT_FILE="security_audit_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "Liap Tui Security Audit Report"
    echo "Generated: $(date)"
    echo "Host: ${EC2_HOST}"
    echo ""
    echo "Security Score: ${SECURITY_SCORE}/100 (Grade: ${GRADE})"
    echo ""
    echo "Critical Issues:"
    for issue in "${ISSUES[@]}"; do
        echo "  - $issue"
    done
    echo ""
    echo "Warnings:"
    for warning in "${WARNINGS[@]}"; do
        echo "  - $warning"
    done
    echo ""
    echo "Recommendations:"
    for rec in "${RECOMMENDATIONS[@]}"; do
        echo "  - $rec"
    done
} > "$REPORT_FILE"

echo -e "\n${GREEN}📄 Full report saved to: ${REPORT_FILE}${NC}"

# Create remediation script
if [ ${#ISSUES[@]} -gt 0 ] || [ ${#RECOMMENDATIONS[@]} -gt 0 ]; then
    REMEDIATION_FILE="security_remediation_$(date +%Y%m%d_%H%M%S).sh"
    {
        echo "#!/bin/bash"
        echo "# Security Remediation Script"
        echo "# Generated: $(date)"
        echo ""
        echo "# WARNING: Review each command before running!"
        echo ""

        if [[ " ${RECOMMENDATIONS[@]} " =~ "Disable password authentication" ]]; then
            echo "# Disable SSH password authentication"
            echo "# sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
            echo "# sudo systemctl restart sshd"
            echo ""
        fi

        if [[ " ${RECOMMENDATIONS[@]} " =~ "Install security updates" ]]; then
            echo "# Install security updates"
            echo "# sudo apt update && sudo apt upgrade -y"
            echo ""
        fi

        if [[ " ${RECOMMENDATIONS[@]} " =~ "Enable firewall" ]]; then
            echo "# Enable firewall"
            echo "# sudo ufw allow 22/tcp"
            echo "# sudo ufw allow 80/tcp"
            echo "# sudo ufw allow 443/tcp"
            echo "# sudo ufw --force enable"
            echo ""
        fi

        echo "# Remember to:"
        echo "# - Test changes in staging first"
        echo "# - Have a backup connection ready"
        echo "# - Document all changes made"
    } > "$REMEDIATION_FILE"

    chmod +x "$REMEDIATION_FILE"
    echo -e "${YELLOW}🔧 Remediation script created: ${REMEDIATION_FILE}${NC}"
    echo -e "${YELLOW}   Review and uncomment commands before running!${NC}"
fi

echo ""
