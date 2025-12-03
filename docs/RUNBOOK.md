# Runbook

## Local Development

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and pnpm
- Python 3.11+ and Poetry

### Setup

1. Clone the repository
2. Run bootstrap script:
   ```bash
   ./scripts/bootstrap-dev.sh
   ```

3. Start all services:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

4. Start frontend:
   ```bash
   cd web && pnpm install && pnpm dev
   ```

### Access Points

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Auth Service: http://localhost:8001
- Service docs: http://localhost:800X/docs

## Deployment

### Infrastructure

1. Initialize Terraform:
   ```bash
   cd infra/terraform
   terraform init
   ```

2. Plan changes:
   ```bash
   terraform plan
   ```

3. Apply:
   ```bash
   terraform apply
   ```

### Kubernetes

1. Deploy with Helm:
   ```bash
   helm install portfolio-superapp deployment/helm/portfolio-superapp \
     --namespace portfolio-superapp \
     --create-namespace
   ```

2. Check status:
   ```bash
   kubectl get pods -n portfolio-superapp
   ```

## Troubleshooting

### Service not starting
- Check logs: `docker-compose logs <service-name>`
- Verify environment variables
- Check database connectivity

### Database connection issues
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check connection string in .env
- Ensure database exists

### Frontend build errors
- Clear .next directory: `rm -rf web/.next`
- Reinstall dependencies: `cd web && rm -rf node_modules && pnpm install`

## Monitoring

- Health checks: `/health` endpoint on each service
- Logs: Check Docker logs or Kubernetes logs
- Metrics: Prometheus endpoints (to be implemented)

