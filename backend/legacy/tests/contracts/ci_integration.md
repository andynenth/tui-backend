# Contract Tests CI/CD Integration Guide

## Overview

This guide shows how to integrate adapter contract tests into your CI/CD pipeline to ensure adapters remain compatible with the WebSocket API contracts.

## GitHub Actions Integration

### Basic Contract Test Workflow

Create `.github/workflows/contract-tests.yml`:

```yaml
name: Contract Tests

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'backend/api/adapters/**'
      - 'backend/tests/contracts/**'
      - 'backend/api/routes/ws.py'
  pull_request:
    branches: [ main ]
    paths:
      - 'backend/api/adapters/**'
      - 'backend/tests/contracts/**'

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run contract tests
      run: |
        cd backend
        python -m pytest tests/contracts/ -v
    
    - name: Run adapter contract compliance
      run: |
        cd backend
        python tests/contracts/test_adapter_contracts.py
    
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: contract-test-results
        path: backend/tests/contracts/test-results/
```

### Advanced Workflow with Golden Master Checks

```yaml
name: Adapter Compatibility Tests

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  compatibility-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Capture fresh golden masters
      run: |
        cd backend
        python capture_golden_masters_integrated.py
    
    - name: Run compatibility tests
      run: |
        cd backend
        python tests/contracts/test_adapter_contracts.py > compatibility-report.txt
    
    - name: Check compatibility threshold
      run: |
        cd backend
        # Extract match percentage from report
        MATCH_RATE=$(grep "Matched:" compatibility-report.txt | grep -o '[0-9]*' | head -1)
        TOTAL=$(grep "Total golden masters:" compatibility-report.txt | grep -o '[0-9]*' | head -1)
        PERCENTAGE=$((MATCH_RATE * 100 / TOTAL))
        
        echo "Compatibility: $PERCENTAGE%"
        
        if [ $PERCENTAGE -lt 95 ]; then
          echo "❌ Compatibility below 95% threshold"
          exit 1
        else
          echo "✅ Compatibility check passed"
        fi
    
    - name: Create issue on failure
      if: failure()
      uses: actions/create-issue@v2
      with:
        title: 'Adapter Compatibility Check Failed'
        body: |
          The adapter compatibility check has failed.
          
          Please review the compatibility report and fix any issues.
          
          [View workflow run](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})
```

## GitLab CI Integration

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - compatibility

contract-tests:
  stage: test
  image: python:3.9
  script:
    - cd backend
    - pip install -r requirements.txt
    - pip install pytest pytest-asyncio
    - python -m pytest tests/contracts/ -v
    - python tests/contracts/test_adapter_contracts.py
  artifacts:
    reports:
      junit: backend/tests/contracts/junit.xml
    paths:
      - backend/tests/contracts/test-results/
  only:
    changes:
      - backend/api/adapters/**/*
      - backend/tests/contracts/**/*
      - backend/api/routes/ws.py

golden-master-check:
  stage: compatibility
  image: python:3.9
  script:
    - cd backend
    - pip install -r requirements.txt
    - python capture_golden_masters_integrated.py
    - python tests/contracts/test_adapter_contracts.py
  allow_failure: true
  only:
    - schedules
```

## Jenkins Pipeline

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'cd backend && python -m venv venv'
                sh 'cd backend && ./venv/bin/pip install -r requirements.txt'
                sh 'cd backend && ./venv/bin/pip install pytest pytest-asyncio'
            }
        }
        
        stage('Contract Tests') {
            steps {
                sh 'cd backend && ./venv/bin/python -m pytest tests/contracts/ -v --junit-xml=test-results/junit.xml'
            }
            post {
                always {
                    junit 'backend/test-results/junit.xml'
                }
            }
        }
        
        stage('Adapter Compliance') {
            steps {
                sh 'cd backend && ./venv/bin/python tests/contracts/test_adapter_contracts.py > compliance-report.txt'
                
                script {
                    def report = readFile('backend/compliance-report.txt')
                    if (report.contains('Failed: 0')) {
                        echo "✅ All contracts passed"
                    } else {
                        error "❌ Contract compliance failed"
                    }
                }
            }
        }
        
        stage('Golden Master Check') {
            when {
                expression { env.RUN_GOLDEN_MASTER_CHECK == 'true' }
            }
            steps {
                sh 'cd backend && ./venv/bin/python capture_golden_masters_integrated.py'
                sh 'cd backend && ./venv/bin/python tests/contracts/test_adapter_contracts.py'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'backend/tests/contracts/test-results/**/*', fingerprint: true
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'backend/tests/contracts/test-results',
                reportFiles: 'index.html',
                reportName: 'Contract Test Report'
            ])
        }
        failure {
            emailext (
                subject: "Contract Tests Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "The contract tests have failed. Please check the results at ${env.BUILD_URL}",
                to: "${env.TEAM_EMAIL}"
            )
        }
    }
}
```

## Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: contract-tests
        name: Run contract tests
        entry: bash -c 'cd backend && python tests/contracts/test_adapter_contracts.py'
        language: system
        files: ^backend/(api/adapters/|tests/contracts/)
        pass_filenames: false
```

## Docker Integration

Create `Dockerfile.contract-tests`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pytest pytest-asyncio

COPY backend/ .

CMD ["python", "tests/contracts/test_adapter_contracts.py"]
```

Use in CI:

```bash
docker build -f Dockerfile.contract-tests -t contract-tests .
docker run --rm contract-tests
```

## Monitoring Contract Test Results

### Metrics to Track

1. **Contract Pass Rate**: Percentage of contracts passing
2. **Golden Master Match Rate**: Percentage of golden masters matching
3. **Test Execution Time**: How long contract tests take
4. **Failure Trends**: Which contracts fail most often

### Example Monitoring Script

```python
#!/usr/bin/env python3
import json
import sys
from datetime import datetime

def parse_test_results(filename):
    """Parse test results and send to monitoring system"""
    with open(filename, 'r') as f:
        results = json.load(f)
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "total_contracts": results.get("total", 0),
        "passed_contracts": results.get("passed", 0),
        "failed_contracts": results.get("failed", 0),
        "pass_rate": results.get("passed", 0) / results.get("total", 1) * 100
    }
    
    # Send to monitoring system (e.g., Datadog, CloudWatch)
    print(f"Contract test metrics: {json.dumps(metrics)}")
    
    # Fail if pass rate is below threshold
    if metrics["pass_rate"] < 95:
        sys.exit(1)

if __name__ == "__main__":
    parse_test_results("test-results/contract-results.json")
```

## Best Practices

1. **Run on Every PR**: Ensure adapters don't break contracts
2. **Schedule Regular Checks**: Detect drift over time
3. **Monitor Trends**: Track pass rates over time
4. **Fast Feedback**: Run contract tests early in pipeline
5. **Clear Reporting**: Make failures easy to understand

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Python path includes backend directory
2. **Async Warnings**: Use pytest-asyncio for async tests
3. **Golden Master Drift**: Regularly update golden masters
4. **Flaky Tests**: Add retries for network-dependent tests

### Debug Commands

```bash
# Run with verbose output
python -m pytest tests/contracts/ -vvs

# Run specific test
python -m pytest tests/contracts/test_adapter_contracts.py::test_contract_compliance -v

# Generate coverage report
python -m pytest tests/contracts/ --cov=api.adapters --cov-report=html
```