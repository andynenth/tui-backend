# Deployment Documentation

This directory contains all deployment-related documentation for the Liap Tui project.

## 📁 Structure

### [ec2-migration/](ec2-migration/)
Complete documentation for AWS EC2 deployment and migration from ECS:
- Step-by-step deployment guides
- Migration checklists and status
- Troubleshooting guides
- Operations manual

### Deployment Guides
- **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Docker concepts and Liap Tui's Docker setup
- **[HTTPS_SETUP_GUIDE.md](HTTPS_SETUP_GUIDE.md)** - SSL/TLS configuration with Let's Encrypt

### [operations/](operations/)
Operational procedures and guides:
- **[DISASTER_RECOVERY_PLAN.md](operations/DISASTER_RECOVERY_PLAN.md)** - Comprehensive disaster recovery procedures

## 🚀 Quick Start

For deploying Liap Tui to AWS EC2:
1. Start with [ec2-migration/EC2_DEPLOYMENT_GUIDE.md](ec2-migration/EC2_DEPLOYMENT_GUIDE.md)
2. Use [ec2-migration/MIGRATION_CHECKLIST.md](ec2-migration/MIGRATION_CHECKLIST.md) to track progress
3. Refer to [ec2-migration/EC2_TROUBLESHOOTING_GUIDE.md](ec2-migration/EC2_TROUBLESHOOTING_GUIDE.md) if issues arise

## 📊 Current Status

- ✅ **EC2 Migration Complete** - Successfully migrated from ECS to EC2
- ✅ **Docker Compose Setup** - Production-ready Docker configuration
- ✅ **Database Persistence** - SQLite with volume mapping
- ✅ **Monitoring & Backups** - Automated health checks and daily backups
