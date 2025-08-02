# CI/CD Pipeline Documentation

## Overview

This repository uses GitHub Actions for automated testing, building, and deployment. The pipeline is designed to provide fast feedback while maintaining high code quality.

## Pipeline Stages

### 🔥 Stage 1: Unit Tests & Code Quality (2-3 minutes)
**Purpose**: Fast feedback loop for developers
**Triggers**: Every push and pull request

**Backend checks**:
- Black code formatting validation
- Pylint static analysis
- Unit tests with coverage (`backend/tests/unit/`)

**Frontend checks**:
- ESLint code quality
- TypeScript type checking
- Jest unit tests with coverage

**Benefits**:
- Catches basic issues immediately
- Enforces consistent code style
- Provides coverage metrics

### 🔗 Stage 2: Integration Tests (5-10 minutes)
**Purpose**: Test module interactions
**Triggers**: After unit tests pass

**What it tests**:
- API integration tests (`backend/tests/integration/`)
- WebSocket communication flows
- Database interactions
- Bot system integration

**Benefits**:
- Catches integration bugs
- Validates real-world scenarios
- Tests cross-module communication

### 🌐 Stage 3: End-to-End Tests (10-15 minutes)
**Purpose**: Full system validation
**Triggers**: After integration tests pass

**What it tests**:
- Complete game flows (`backend/tests/e2e/`)
- Performance benchmarks
- Multi-user scenarios
- Real-time features

**Benefits**:
- Validates user experience
- Catches system-level issues
- Performance regression detection

### 🐳 Stage 4: Docker Build & Security (3-5 minutes)
**Purpose**: Production readiness
**Triggers**: Parallel with other stages

**What it does**:
- Builds production Docker image
- Vulnerability scanning with Trivy
- Security report generation
- Build cache optimization

**Benefits**:
- Ensures deployable artifacts
- Security vulnerability detection
- Consistent build environment

### 🚀 Stage 5: Deploy (2-5 minutes)
**Purpose**: Production deployment
**Triggers**: Only on main branch, after all tests pass

**What it does**:
- Pushes Docker image to registry
- Deploys to production environment
- Sends deployment notifications

**Benefits**:
- Automated production deployment
- Zero-downtime releases
- Rollback capability

## Performance Monitoring

**Performance Check Job** (PR only):
- Runs performance benchmarks
- Compares against baseline
- Comments on PR with results
- Alerts on performance regressions

## Configuration

### Environment Variables
```yaml
PYTHON_VERSION: '3.11'    # Python runtime version
NODE_VERSION: '18'        # Node.js version for frontend
```

### Required Secrets
For deployment to work, set these in repository settings:

```
DOCKER_REGISTRY     # Docker registry URL (e.g., docker.io, ghcr.io)
DOCKER_USERNAME     # Registry username
DOCKER_PASSWORD     # Registry password/token
```

## Branch Protection

**Recommended settings** for main branch:
- Require status checks to pass
- Require branches to be up to date
- Require review from code owners
- Dismiss stale reviews when new commits are pushed

**Required status checks**:
- Unit Tests & Code Quality
- Integration Tests
- End-to-End Tests
- Docker Build & Security Scan

## Local Development

**Before pushing**, run these locally:
```bash
# Backend quality checks
cd backend
source venv/bin/activate
black . --check
pylint engine/ api/
pytest tests/unit/ -v

# Frontend quality checks  
cd frontend
npm run lint
npm run type-check
npm test
```

## Troubleshooting

### Common Issues

**1. Unit Tests Failing**
```bash
# Run locally to debug
cd backend && pytest tests/unit/ -v -s
cd frontend && npm test
```

**2. Integration Tests Flaky**
- Check for race conditions in async tests
- Verify test isolation and cleanup
- Review test dependencies

**3. Docker Build Fails**
- Check Dockerfile syntax
- Verify all required files are included
- Test build locally: `docker build -t liap-tui:test .`

**4. Deployment Issues**
- Verify secrets are configured
- Check Docker registry permissions
- Review deployment logs in Actions tab

### Performance Issues

**Slow pipeline**:
- Unit tests should be < 3 minutes
- Integration tests should be < 10 minutes
- Consider parallelization for large test suites

**Test optimization**:
- Use pytest markers to run subsets: `pytest -m "not slow"`
- Cache dependencies between jobs
- Optimize Docker layer caching

## Monitoring

**Pipeline health metrics**:
- Average build time per stage
- Test success rates
- Coverage trends
- Performance benchmark history

**Alerts**:
- Failed deployments
- Performance regressions
- Security vulnerabilities
- Coverage drops

## Best Practices

### For Developers

**1. Fast Feedback**
- Run unit tests locally before pushing
- Use pre-commit hooks for formatting
- Write tests for new features

**2. Test Organization**
- Unit tests: Fast, isolated, mocked
- Integration tests: Real dependencies
- E2E tests: Full user scenarios

**3. CI-Friendly Code**
- Avoid hardcoded paths
- Use environment variables
- Make tests deterministic

### For DevOps

**1. Pipeline Optimization**
- Cache dependencies aggressively
- Run jobs in parallel when possible
- Fail fast on critical issues

**2. Security**
- Regular dependency updates
- Vulnerability scanning
- Secrets rotation

**3. Monitoring**
- Track pipeline metrics
- Set up alerts for failures
- Monitor deployment success rates

## Pipeline Files

- `.github/workflows/ci.yml` - Main CI/CD pipeline
- `backend/pytest.ini` - Test configuration
- `frontend/package.json` - Frontend scripts
- `Dockerfile` - Production build

## Support

For pipeline issues:
1. Check the Actions tab for detailed logs
2. Review this documentation
3. Test locally using the same commands
4. Open an issue with pipeline logs attached

---

**Next Steps**: This pipeline provides a solid foundation. Consider adding:
- Staging environment deployment
- Database migration testing  
- Load testing for high-traffic scenarios
- Multi-browser E2E testing