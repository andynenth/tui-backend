# Infrastructure Deployment Guide

**Document Purpose**: Deployment prerequisites, environment setup, and infrastructure requirements for Phase 5 implementation with hybrid persistence approach.

## Navigation
- [Main Planning Document](../../planning/PHASE_5_INFRASTRUCTURE_LAYER.md)
- [Technical Design](../../planning/PHASE_5_TECHNICAL_DESIGN.md)
- [Progress Tracking](../../planning/INFRASTRUCTURE_PROGRESS_TRACKING.md)

## Important Context
Based on the Database Integration Readiness Report, this deployment maintains in-memory performance for active games while adding async persistence for completed games only.

## Environment Requirements

### Development Environment

#### Required Software
```bash
# Core Requirements
Python 3.11+
Docker 24.0+
Docker Compose 2.20+
Node.js 18+ (for frontend compatibility testing)

# Database Clients
psql 15+ (PostgreSQL client)
redis-cli 7+ (Redis client)

# Development Tools
git 2.40+
make (for automation)
curl (for testing)
jq (for JSON processing)
```

#### Python Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Environment Variables
```bash
# Create .env file in backend directory
cat > backend/.env << EOF
# Memory Configuration
MAX_ACTIVE_GAMES=10000
MAX_MEMORY_MB=4096
MEMORY_CHECK_INTERVAL=60
GC_COMPLETED_GAMES_AFTER=300

# Redis Configuration (Rate Limiting Only)
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_MAX=10

# Archive Configuration (Completed Games Only)
ARCHIVE_BACKEND=s3  # or postgresql, filesystem
ARCHIVE_URL=s3://liap-archives/games/
ARCHIVE_BATCH_SIZE=100
ARCHIVE_FLUSH_INTERVAL=60
ARCHIVE_RETENTION_DAYS=90

# Performance Settings
EVENT_BUFFER_SIZE=10000
MAX_EVENTS_PER_GAME=1000
GAME_SUMMARY_CACHE_SIZE=1000

# Rate Limiting
RATE_LIMIT_PER_PLAYER_PER_MINUTE=60
RATE_LIMIT_PER_ROOM_PER_SECOND=10
RATE_LIMIT_WEBSOCKET_PER_SECOND=5

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_TIMEOUT=10
MEMORY_ALERT_THRESHOLD=80

# Feature Flags
USE_GAME_ARCHIVAL=true
USE_MEMORY_MONITORING=true
USE_RATE_LIMITING=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_CORRELATION_ID=true
EOF
```

### Docker Compose Setup

#### Development Stack
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  # Redis for rate limiting only
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save ""
      --appendonly no
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Optional: PostgreSQL for game archives only
  postgres-archive:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: archive
      POSTGRES_PASSWORD: archive
      POSTGRES_DB: liap_archive
    ports:
      - "5432:5432"
    volumes:
      - archive_data:/var/lib/postgresql/data
      - ./scripts/init-archive.sql:/docker-entrypoint-initdb.d/init.sql
    profiles:
      - archive  # Only start if using PostgreSQL backend

  # Optional: S3-compatible storage for archives
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    profiles:
      - archive  # Only start if using S3 backend

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_USERS_ALLOW_SIGN_UP: false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources

volumes:
  archive_data:
  minio_data:
  prometheus_data:
  grafana_data:
```

#### Test Environment Stack
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres-test:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: liap_test
    tmpfs:
      - /var/lib/postgresql/data
    ports:
      - "5434:5432"

  redis-test:
    image: redis:7-alpine
    command: redis-server --maxmemory 64mb
    tmpfs:
      - /data
    ports:
      - "6380:6379"

  test-runner:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      DATABASE_URL: postgresql://test:test@postgres-test:5432/liap_test
      REDIS_URL: redis://redis-test:6379/0
      PYTHONPATH: /app
    volumes:
      - ./backend:/app
      - ./test-results:/test-results
    depends_on:
      - postgres-test
      - redis-test
    command: >
      bash -c "
        alembic upgrade head &&
        pytest -v --cov=infrastructure --cov-report=html --cov-report=xml
      "
```

### Archive Storage Setup

#### PostgreSQL Archive Schema (Optional)
```sql
-- scripts/init-archive.sql
-- Only for completed games, not active games
CREATE SCHEMA IF NOT EXISTS archive;

CREATE TABLE IF NOT EXISTS archive.completed_games (
    game_id VARCHAR(50) PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    game_data JSONB NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    game_duration_seconds INTEGER,
    winner_name VARCHAR(100),
    final_scores JSONB
);

CREATE INDEX idx_completed_games_room ON archive.completed_games(room_id);
CREATE INDEX idx_completed_games_completed ON archive.completed_games(completed_at);
CREATE INDEX idx_completed_games_winner ON archive.completed_games(winner_name);

CREATE TABLE IF NOT EXISTS archive.game_events (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(50) REFERENCES archive.completed_games(game_id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    archived_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_game_events_game ON archive.game_events(game_id);
CREATE INDEX idx_game_events_type ON archive.game_events(event_type);
```

#### S3 Bucket Setup (Alternative)
```bash
# Create bucket for game archives
aws s3 mb s3://liap-game-archives

# Set lifecycle policy for automatic deletion
aws s3api put-bucket-lifecycle-configuration \
  --bucket liap-game-archives \
  --lifecycle-configuration file://archive-lifecycle.json
```

### Infrastructure Blockers

#### Pre-Deployment Checklist

##### Environment Dependencies
- [ ] Python 3.11+ with all dependencies installed
- [ ] Docker and Docker Compose installed
- [ ] Redis 7+ for rate limiting (minimal memory required)
- [ ] Archive backend chosen and configured (S3/PostgreSQL/filesystem)
- [ ] Sufficient memory allocated for game storage (4GB+ recommended)

##### Memory Management Prerequisites
- [ ] Memory limits configured in environment
- [ ] Memory monitoring tools installed
- [ ] GC settings optimized for game workload
- [ ] Swap configured as safety net

##### Archive Prerequisites (if using)
- [ ] Archive backend credentials configured
- [ ] Archive retention policy defined
- [ ] Archive monitoring setup
- [ ] Archive backup strategy (optional)

##### Monitoring Prerequisites
- [ ] Prometheus endpoint accessible
- [ ] Grafana dashboards imported
- [ ] Alert rules configured
- [ ] Log aggregation configured

##### Security Prerequisites
- [ ] Database credentials secured
- [ ] Redis password configured (production)
- [ ] TLS certificates available (production)
- [ ] Firewall rules configured

#### Common Blockers and Solutions

##### 1. Memory Pressure Issues
```bash
# Monitor memory usage
ps aux | grep python | awk '{sum+=$6} END {print "Memory used: " sum/1024 " MB"}'

# Common issues:
# - Out of memory errors
# - Slow garbage collection
# - Memory leaks

# Solutions:
# Increase memory limit
export MAX_MEMORY_MB=8192

# Force garbage collection
python -c "import gc; gc.collect()"

# Monitor for leaks
python -m tracemalloc
```

##### 2. Redis Connection Issues
```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping

# Common issues:
# - Connection refused: Check if Redis is running
# - Memory issues: Increase maxmemory setting
# - Persistence issues: Check disk space

# Solution:
docker-compose restart redis
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
```

##### 3. Archive Backend Issues
```bash
# Test S3 connection (if using)
aws s3 ls s3://liap-game-archives/

# Test PostgreSQL archive (if using)
psql $ARCHIVE_URL -c "SELECT count(*) FROM archive.completed_games;"

# Common issues:
# - Permission denied: Check IAM/credentials
# - Connection timeout: Check network/firewall
# - Disk full: Check archive storage

# Solutions:
# Switch to filesystem temporarily
export ARCHIVE_BACKEND=filesystem
export ARCHIVE_URL=/tmp/liap-archives/
```

##### 4. Port Conflicts
```bash
# Check for port usage
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # FastAPI

# Solution: Change ports in docker-compose.yml or stop conflicting services
```

### Deployment Scripts

#### Start Infrastructure
```bash
#!/bin/bash
# scripts/start-infrastructure.sh

set -e

echo "Starting infrastructure services..."

# Start databases
docker-compose up -d postgres postgres-events redis

# Wait for services
echo "Waiting for services to be healthy..."
sleep 10

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Verify services
echo "Verifying services..."
docker-compose ps

echo "Infrastructure ready!"
```

#### Stop Infrastructure
```bash
#!/bin/bash
# scripts/stop-infrastructure.sh

set -e

echo "Stopping infrastructure services..."
docker-compose down

echo "Infrastructure stopped!"
```

#### Reset Infrastructure
```bash
#!/bin/bash
# scripts/reset-infrastructure.sh

set -e

echo "WARNING: This will delete all data!"
read -p "Are you sure? (yes/no) " -n 3 -r
echo

if [[ $REPLY =~ ^yes$ ]]
then
    docker-compose down -v
    rm -rf ./data/*
    echo "Infrastructure reset complete!"
else
    echo "Reset cancelled."
fi
```

### Production Deployment Considerations

#### High Availability Setup
```yaml
# Additional services for production
services:
  pgbouncer:
    image: pgbouncer/pgbouncer:latest
    environment:
      DATABASES_DEFAULT: "liap_prod"
      DATABASES_HOST: "postgres-primary"
      POOL_MODE: "transaction"
      MAX_CLIENT_CONN: "1000"
      DEFAULT_POOL_SIZE: "25"

  redis-sentinel:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis-sentinel.conf
    volumes:
      - ./config/sentinel.conf:/etc/redis-sentinel.conf
```

#### Environment-Specific Configuration
```bash
# Production environment variables
ENVIRONMENT=production
DATABASE_POOL_MIN=20
DATABASE_POOL_MAX=100
REDIS_POOL_MIN=10
REDIS_POOL_MAX=50
LOG_LEVEL=WARNING
USE_EVENT_SOURCING=true
ENABLE_PROFILING=false
```

#### Monitoring Setup
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'liap-backend'
    static_configs:
      - targets: ['backend:9090']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Troubleshooting Guide

#### Memory Optimization
```python
# Monitor memory usage
import psutil
import gc

process = psutil.Process()
memory_info = process.memory_info()
print(f"Memory used: {memory_info.rss / 1024 / 1024:.2f} MB")

# Force cleanup of completed games
gc.collect()

# Adjust memory limits at runtime
import resource
resource.setrlimit(resource.RLIMIT_AS, (8 * 1024 * 1024 * 1024, -1))
```

#### Redis Memory Issues
```bash
# Check memory usage
redis-cli INFO memory

# Clear specific cache patterns
redis-cli --scan --pattern "cache:room:*" | xargs redis-cli DEL

# Optimize memory
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Archive Performance
```bash
# Monitor archive queue depth
redis-cli LLEN archive:queue

# Check archive write latency
tail -f logs/archive.log | grep "Archive completed"

# Manually trigger archival
curl -X POST http://localhost:8000/admin/archive/flush

# Check archive storage usage
# S3
aws s3 ls s3://liap-game-archives/ --recursive --summarize

# PostgreSQL
psql $ARCHIVE_URL -c "SELECT pg_size_pretty(pg_database_size('liap_archive'));"
```

### Health Check Verification
```bash
# Check all health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live

# Expected output:
# {"status": "healthy", "checks": {...}}
```