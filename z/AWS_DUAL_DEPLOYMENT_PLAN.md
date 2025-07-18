# AWS Dual-Deployment Implementation Plan
## EC2 → Lambda Migration-Ready Architecture

### Executive Summary
This plan outlines the architecture and implementation strategy for building an application that initially deploys to AWS EC2 but is designed from the ground up to support AWS Lambda deployment without major refactoring. The key is establishing clear boundaries between platform-specific adapters and core business logic.

---

## Architecture Principles

### 1. **Hexagonal Architecture (Ports & Adapters)**
- Core business logic is completely isolated from infrastructure concerns
- Platform-specific code lives in adapter layers
- Dependencies flow inward (infrastructure → application → domain)

### 2. **Dependency Injection**
- All external dependencies are injected, not hardcoded
- Configuration is environment-aware
- Runtime-specific implementations can be swapped

### 3. **Stateless Design**
- No in-memory session state
- All state externalized to databases/caches
- Request-scoped lifecycle for all operations

---

## Project Structure

```
project-root/
├── src/
│   ├── core/                    # Shared business logic (platform-agnostic)
│   │   ├── domain/              # Domain models and entities
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── order.py
│   │   │   └── product.py
│   │   ├── services/            # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py
│   │   │   ├── order_service.py
│   │   │   └── product_service.py
│   │   ├── interfaces/          # Port definitions (abstractions)
│   │   │   ├── __init__.py
│   │   │   ├── repositories.py
│   │   │   ├── messaging.py
│   │   │   └── cache.py
│   │   └── exceptions/          # Custom exceptions
│   │       └── __init__.py
│   │
│   ├── adapters/                # Platform-specific implementations
│   │   ├── repositories/        # Data access implementations
│   │   │   ├── __init__.py
│   │   │   ├── dynamodb/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_repository.py
│   │   │   └── postgres/
│   │   │       ├── __init__.py
│   │   │       └── user_repository.py
│   │   ├── messaging/           # Message queue adapters
│   │   │   ├── __init__.py
│   │   │   ├── sqs_adapter.py
│   │   │   └── sns_adapter.py
│   │   ├── cache/              # Cache implementations
│   │   │   ├── __init__.py
│   │   │   ├── redis_adapter.py
│   │   │   └── elasticache_adapter.py
│   │   └── external/           # Third-party integrations
│   │       ├── __init__.py
│   │       ├── stripe_adapter.py
│   │       └── sendgrid_adapter.py
│   │
│   ├── api/                    # API layer (shared request/response handling)
│   │   ├── __init__.py
│   │   ├── schemas/            # Request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── user_schemas.py
│   │   │   └── order_schemas.py
│   │   ├── handlers/           # Request handlers (platform-agnostic)
│   │   │   ├── __init__.py
│   │   │   ├── user_handlers.py
│   │   │   └── order_handlers.py
│   │   └── middleware/         # Shared middleware
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── validation.py
│   │
│   ├── platforms/              # Platform-specific entry points
│   │   ├── ec2/               # EC2-specific code
│   │   │   ├── __init__.py
│   │   │   ├── app.py         # FastAPI/Flask app
│   │   │   ├── server.py      # Server entry point
│   │   │   ├── config.py      # EC2-specific config
│   │   │   └── middleware/    # EC2-specific middleware
│   │   │       └── __init__.py
│   │   └── lambda/            # Lambda-specific code
│   │       ├── __init__.py
│   │       ├── handler.py     # Lambda handler entry point
│   │       ├── config.py      # Lambda-specific config
│   │       ├── middleware/    # Lambda-specific middleware
│   │       │   └── __init__.py
│   │       └── events/        # Event source adapters
│   │           ├── __init__.py
│   │           ├── api_gateway.py
│   │           ├── sqs.py
│   │           └── s3.py
│   │
│   └── shared/                 # Shared utilities
│       ├── __init__.py
│       ├── config/             # Configuration management
│       │   ├── __init__.py
│       │   ├── base.py         # Base configuration
│       │   └── loaders.py      # Config loaders
│       ├── logging/            # Structured logging
│       │   ├── __init__.py
│       │   └── logger.py
│       ├── monitoring/         # Metrics and tracing
│       │   ├── __init__.py
│       │   ├── metrics.py
│       │   └── tracing.py
│       └── utils/              # General utilities
│           ├── __init__.py
│           ├── datetime.py
│           └── serialization.py
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests (by module)
│   │   ├── core/
│   │   ├── adapters/
│   │   └── api/
│   ├── integration/            # Integration tests
│   │   ├── ec2/
│   │   └── lambda/
│   └── fixtures/               # Test fixtures
│       └── __init__.py
│
├── infrastructure/             # Infrastructure as Code
│   ├── terraform/             # Terraform configs
│   │   ├── modules/
│   │   │   ├── ec2/
│   │   │   └── lambda/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── shared/
│   └── docker/                # Docker configurations
│       ├── ec2/
│       │   └── Dockerfile
│       └── lambda/
│           └── Dockerfile
│
├── scripts/                   # Deployment and utility scripts
│   ├── deploy_ec2.sh
│   ├── deploy_lambda.sh
│   └── run_tests.sh
│
├── docs/                      # Documentation
│   ├── architecture/
│   ├── api/
│   └── deployment/
│
├── .github/                   # GitHub Actions workflows
│   └── workflows/
│       ├── ec2_deploy.yml
│       └── lambda_deploy.yml
│
├── requirements/              # Python dependencies
│   ├── base.txt              # Shared dependencies
│   ├── ec2.txt               # EC2-specific deps
│   └── lambda.txt            # Lambda-specific deps
│
├── .env.example              # Environment variables template
├── .gitignore
├── pyproject.toml            # Project metadata
└── README.md
```

---

## Phase 1: EC2 Implementation (Weeks 1-6)

### Week 1-2: Core Domain & Services
**Shared Components:**
```python
# src/core/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..domain.user import User

class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[User]:
        pass
```

```python
# src/core/services/user_service.py
from ..interfaces.repositories import UserRepository
from ..domain.user import User
from typing import Optional

class UserService:
    def __init__(self, user_repository: UserRepository):
        self._repository = user_repository
    
    async def get_user(self, user_id: str) -> Optional[User]:
        return await self._repository.get_by_id(user_id)
    
    async def create_user(self, email: str, name: str) -> User:
        user = User(email=email, name=name)
        return await self._repository.save(user)
```

### Week 3-4: EC2 Platform Layer
**EC2-Specific Components:**
```python
# src/platforms/ec2/app.py
from fastapi import FastAPI
from ...shared.config.loaders import load_config
from ...adapters.repositories.postgres import PostgresUserRepository
from ...core.services.user_service import UserService
from ...api.handlers.user_handlers import UserHandlers

def create_app() -> FastAPI:
    # Load EC2-specific configuration
    config = load_config("ec2")
    
    # Initialize dependencies
    user_repo = PostgresUserRepository(config.database_url)
    user_service = UserService(user_repo)
    user_handlers = UserHandlers(user_service)
    
    # Create FastAPI app
    app = FastAPI()
    
    # Register routes
    app.include_router(user_handlers.router)
    
    return app

# src/platforms/ec2/server.py
import uvicorn
from .app import create_app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Week 5-6: Infrastructure & Deployment
**Infrastructure as Code:**
```hcl
# infrastructure/terraform/modules/ec2/main.tf
resource "aws_instance" "app_server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  user_data = templatefile("${path.module}/user_data.sh", {
    app_port = var.app_port
  })
  
  tags = {
    Name = "${var.environment}-app-server"
  }
}

resource "aws_alb_target_group" "app" {
  name     = "${var.environment}-app-tg"
  port     = var.app_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  
  health_check {
    path = "/health"
  }
}
```

---

## Phase 2: Lambda Preparation (Weeks 7-8)

### Week 7: Lambda Adapters
**Lambda-Specific Components:**
```python
# src/platforms/lambda/handler.py
import json
from typing import Dict, Any
from ...shared.config.loaders import load_config
from ...adapters.repositories.dynamodb import DynamoDBUserRepository
from ...core.services.user_service import UserService
from ...api.handlers.user_handlers import UserHandlers
from .events.api_gateway import parse_api_gateway_event

# Initialize dependencies at module level (Lambda container reuse)
config = load_config("lambda")
user_repo = DynamoDBUserRepository(config.dynamodb_table)
user_service = UserService(user_repo)
user_handlers = UserHandlers(user_service)

async def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for API Gateway events"""
    try:
        # Parse API Gateway event
        request = parse_api_gateway_event(event)
        
        # Route to appropriate handler
        if request.path == "/users" and request.method == "GET":
            response = await user_handlers.list_users(request)
        elif request.path.startswith("/users/") and request.method == "GET":
            user_id = request.path.split("/")[-1]
            response = await user_handlers.get_user(user_id)
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Not found"})
            }
        
        return {
            "statusCode": response.status_code,
            "body": json.dumps(response.body),
            "headers": response.headers
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
```

### Week 8: Testing & Documentation
**Cross-Platform Testing:**
```python
# tests/integration/test_user_service.py
import pytest
from src.core.services.user_service import UserService
from src.adapters.repositories.postgres import PostgresUserRepository
from src.adapters.repositories.dynamodb import DynamoDBUserRepository

@pytest.mark.parametrize("repository_class", [
    PostgresUserRepository,
    DynamoDBUserRepository
])
async def test_user_service_with_different_repos(repository_class):
    """Ensure service works with both repository implementations"""
    repo = repository_class(test_config)
    service = UserService(repo)
    
    user = await service.create_user("test@example.com", "Test User")
    assert user.email == "test@example.com"
    
    retrieved = await service.get_user(user.id)
    assert retrieved.id == user.id
```

---

## Key Design Patterns

### 1. **Dependency Injection Container**
```python
# src/shared/config/container.py
from typing import Dict, Any, Callable

class DIContainer:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register(self, name: str, factory: Callable):
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        if name not in self._services:
            self._services[name] = self._factories[name]()
        return self._services[name]
```

### 2. **Request/Response Abstraction**
```python
# src/api/base.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class Request:
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    query_params: Dict[str, str]

@dataclass
class Response:
    status_code: int
    body: Any
    headers: Dict[str, str] = None
```

### 3. **Environment-Aware Configuration**
```python
# src/shared/config/base.py
import os
from abc import ABC, abstractmethod

class BaseConfig(ABC):
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        pass

class EC2Config(BaseConfig):
    def get_database_config(self) -> Dict[str, Any]:
        return {
            "type": "postgres",
            "url": os.getenv("DATABASE_URL")
        }

class LambdaConfig(BaseConfig):
    def get_database_config(self) -> Dict[str, Any]:
        return {
            "type": "dynamodb",
            "table_name": os.getenv("DYNAMODB_TABLE")
        }
```

---

## Migration Checklist: EC2 → Lambda

### Pre-Migration Validation
- [ ] All business logic in `core/` is platform-agnostic
- [ ] No direct infrastructure dependencies in services
- [ ] All state is externalized (no in-memory caching)
- [ ] Request handling uses abstraction layer
- [ ] Configuration is environment-aware
- [ ] Dependencies are injected, not imported

### Migration Steps
1. **Create Lambda-specific adapters** (if different from EC2)
2. **Implement Lambda handler** with event parsing
3. **Update configuration** for Lambda environment
4. **Deploy infrastructure** using Lambda Terraform module
5. **Run integration tests** against Lambda endpoint
6. **Implement gradual rollout** (canary deployment)

### Post-Migration
- [ ] Monitor Lambda cold starts
- [ ] Optimize package size
- [ ] Configure reserved concurrency
- [ ] Set up X-Ray tracing
- [ ] Implement Lambda layers for dependencies

---

## Best Practices & Guidelines

### 1. **Shared Code Guidelines**
- Keep `core/` completely free of AWS SDK imports
- Use interfaces/protocols for all external dependencies
- Implement platform-specific code only in `platforms/` and `adapters/`
- Write unit tests that run without AWS dependencies

### 2. **Configuration Management**
- Use environment variables for all configuration
- Implement configuration validation on startup
- Keep sensitive config in AWS Secrets Manager/Parameter Store
- Use different config classes for EC2 vs Lambda

### 3. **Logging & Monitoring**
- Use structured logging (JSON format)
- Include correlation IDs in all log entries
- Implement platform-specific metric collectors
- Use AWS X-Ray for distributed tracing

### 4. **Error Handling**
- Define custom exceptions in `core/exceptions`
- Implement platform-specific error formatters
- Use consistent error response schemas
- Log errors with full context

### 5. **Testing Strategy**
- Unit tests for core business logic (no AWS dependencies)
- Integration tests with mocked AWS services
- End-to-end tests for each platform
- Performance tests to compare EC2 vs Lambda

---

## Cost Optimization

### EC2 Considerations
- Use Auto Scaling Groups with appropriate metrics
- Implement request caching where appropriate
- Use RDS Proxy for database connections
- Consider Spot Instances for non-critical workloads

### Lambda Preparations
- Minimize deployment package size
- Use Lambda Layers for shared dependencies
- Implement connection pooling for databases
- Consider using Lambda@Edge for geographic distribution

---

## Timeline Summary

**Weeks 1-6: EC2 Implementation**
- Core domain and services development
- EC2 platform implementation
- Infrastructure setup and deployment

**Weeks 7-8: Lambda Preparation**
- Lambda adapter development
- Cross-platform testing
- Documentation and migration guide

**Future Phase: Lambda Migration**
- Gradual rollout with traffic splitting
- Performance optimization
- Full cutover when metrics are satisfactory

---

## Success Metrics

### Technical Metrics
- Code reuse between platforms: >80%
- Unit test coverage: >90%
- Integration test coverage: >80%
- Deployment time: <10 minutes

### Business Metrics
- Zero downtime during migration
- Response time parity (±10%)
- Cost reduction target: 30-50%
- Improved scalability metrics

---

## Conclusion

This architecture ensures that the initial EC2 deployment is production-ready while maintaining the flexibility to migrate to Lambda with minimal code changes. The key is maintaining strict separation between business logic and infrastructure concerns, allowing platform-specific adapters to be swapped out as needed.

The modular structure, dependency injection, and clear interfaces make it possible to run the same core application on different AWS compute platforms, optimizing for cost and performance as requirements evolve.