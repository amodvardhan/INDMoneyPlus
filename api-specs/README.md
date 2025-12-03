# API Specifications

This directory contains OpenAPI specifications for all microservices.

## Structure

- `auth-service.yaml` - Auth service API spec
- `aggregator-service.yaml` - Aggregator service API spec
- `marketdata-service.yaml` - Market data service API spec
- `analytics-service.yaml` - Analytics service API spec
- `agent-orchestrator.yaml` - Agent orchestrator API spec
- `order-orchestrator.yaml` - Order orchestrator API spec
- `notification-service.yaml` - Notification service API spec
- `admin-service.yaml` - Admin service API spec

## Code Generation

Use OpenAPI Generator to generate client SDKs:

```bash
# Generate TypeScript client
openapi-generator-cli generate \
  -i api-specs/auth-service.yaml \
  -g typescript-axios \
  -o web/src/generated/api-client

# Generate Python client
openapi-generator-cli generate \
  -i api-specs/auth-service.yaml \
  -g python \
  -o services/auth-service/generated
```

