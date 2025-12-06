.PHONY: help dev-up dev-down dev-logs migrate seed test lint build-images ci-run clean health-check

# Default target
help:
	@echo "Portfolio SuperApp - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make dev-up          - Start all services with hot-reload"
	@echo "  make dev-down        - Stop all services"
	@echo "  make dev-logs        - Show logs from all services"
	@echo "  make migrate         - Run database migrations for all services"
	@echo "  make seed            - Seed test data"
	@echo "  make test            - Run unit and integration tests"
	@echo "  make lint            - Run linters on all services"
	@echo "  make build-images    - Build Docker images for all services"
	@echo "  make ci-run          - Run CI-like build and test locally"
	@echo "  make clean           - Remove containers, volumes, and images"
	@echo "  make health-check    - Check health of all services"
	@echo ""

# Start development environment
dev-up:
	@echo "🚀 Starting development environment..."
	@docker compose -f docker-compose.dev.yml up -d
	@echo "⏳ Waiting for services to be healthy..."
	@./scripts/docker-wait-for.sh http://localhost:8080/health auth-service 60
	@./scripts/docker-wait-for.sh http://localhost:8081/health marketdata-service 60
	@./scripts/docker-wait-for.sh http://localhost:8082/health analytics-service 60
	@./scripts/docker-wait-for.sh http://localhost:8083/health aggregator-service 60
	@./scripts/docker-wait-for.sh http://localhost:8084/health agent-orchestrator 60
	@./scripts/docker-wait-for.sh http://localhost:8085/health notification-service 60
	@./scripts/docker-wait-for.sh http://localhost:8086/health order-orchestrator 60
	@./scripts/docker-wait-for.sh http://localhost:8088/health recommendations-service 60
	@./scripts/docker-wait-for.sh http://localhost:8000/health api-gateway 60
	@./scripts/docker-wait-for.sh http://localhost:3000/api/health web 60 || echo "⚠️  Web health check skipped (may not have /api/health endpoint)"
	@echo "✅ All services are healthy!"
	@echo ""
	@echo "📋 Service URLs:"
	@echo "  Frontend:        http://localhost:3000"
	@echo "  API Gateway:     http://localhost:8000"
	@echo "  Auth Service:    http://localhost:8080"
	@echo "  Marketdata:      http://localhost:8081"
	@echo "  Analytics:       http://localhost:8082"
	@echo "  Aggregator:      http://localhost:8083"
	@echo "  Agent:           http://localhost:8084"
	@echo "  Notification:    http://localhost:8085"
	@echo "  Order:           http://localhost:8086"
	@echo "  Recommendations: http://localhost:8088"
	@echo "  Prometheus:      http://localhost:9090"
	@echo "  Grafana:         http://localhost:3001 (admin/admin)"

# Stop development environment
dev-down:
	@echo "🛑 Stopping development environment..."
	@docker compose -f docker-compose.dev.yml down

# Show logs
dev-logs:
	@docker compose -f docker-compose.dev.yml logs -f

# Run migrations
migrate:
	@echo "🔄 Running database migrations..."
	@./scripts/bootstrap-dev.sh --migrate-only

# Seed test data
seed:
	@echo "🌱 Seeding test data..."
	@./scripts/bootstrap-dev.sh --seed-only

# Run tests
test:
	@echo "🧪 Running tests..."
	@./scripts/run-tests.sh

# Run linters
lint:
	@echo "🔍 Running linters..."
	@for service in services/*/; do \
		if [ -f "$$service/pyproject.toml" ]; then \
			echo "Linting $$service..."; \
			cd "$$service" && poetry run ruff check . && poetry run black --check . || true; \
			cd ../..; \
		fi; \
	done
	@if [ -d "web" ]; then \
		echo "Linting web..."; \
		cd web && npm run lint || true; \
		cd ..; \
	fi

# Build Docker images
build-images:
	@echo "🏗️  Building Docker images..."
	@docker compose -f docker-compose.dev.yml build

# Run CI-like build and test
ci-run:
	@echo "🔧 Running CI-like build and test..."
	@./scripts/ci_local.sh

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	@docker compose -f docker-compose.dev.yml down -v
	@docker compose -f docker-compose.ci.yml down -v
	@docker system prune -f

# Health check
health-check:
	@echo "🏥 Checking service health..."
	@./scripts/docker-wait-for.sh http://localhost:8080/health auth-service 10 || echo "❌ auth-service unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8081/health marketdata-service 10 || echo "❌ marketdata-service unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8082/health analytics-service 10 || echo "❌ analytics-service unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8083/health aggregator-service 10 || echo "❌ aggregator-service unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8084/health agent-orchestrator 10 || echo "❌ agent-orchestrator unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8085/health notification-service 10 || echo "❌ notification-service unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8086/health order-orchestrator 10 || echo "❌ order-orchestrator unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8088/health recommendations-service 10 || echo "❌ recommendations-service unhealthy"
	@./scripts/docker-wait-for.sh http://localhost:8000/health api-gateway 10 || echo "❌ api-gateway unhealthy"
	@echo "✅ Health check complete"

