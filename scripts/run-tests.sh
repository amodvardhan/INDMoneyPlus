#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Running tests for Portfolio SuperApp..."

# Check if services are running
if ! docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Services not running. Starting infrastructure services...${NC}"
    docker compose -f docker-compose.dev.yml up -d postgres redis redpanda vector-db-mock
    sleep 5
fi

# Wait for services to be ready
echo "⏳ Waiting for infrastructure services..."
./scripts/docker-wait-for.sh http://localhost:5432 postgres 30 || {
    echo -e "${RED}❌ PostgreSQL not ready${NC}"
    exit 1
}

# Run migrations before tests
echo "🔄 Running migrations..."
./scripts/bootstrap-dev.sh --migrate-only

# Run Python service tests
echo ""
echo "🐍 Running Python service tests..."
FAILED_SERVICES=()

for service_dir in services/*/; do
    if [ -d "$service_dir/tests" ] && [ -f "$service_dir/pyproject.toml" ]; then
        service_name=$(basename "$service_dir")
        echo ""
        echo "  Testing $service_name..."
        
        cd "$service_dir"
        
        # Install dependencies if needed
        if ! poetry show pytest >/dev/null 2>&1; then
            poetry install --no-interaction --no-ansi >/dev/null 2>&1 || true
        fi
        
        # Set test environment variables
        export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-user}:${POSTGRES_PASSWORD:-password}@localhost:5432/${service_name}_test_db"
        export REDIS_URL="redis://localhost:6379/0"
        export TESTING=true
        
        # Create test database
        docker compose -f ../../docker-compose.dev.yml exec -T postgres psql -U ${POSTGRES_USER:-user} -c "CREATE DATABASE ${service_name}_test_db;" 2>/dev/null || true
        
        # Run tests
        if poetry run pytest -v --tb=short 2>&1; then
            echo -e "  ${GREEN}✅ $service_name tests passed${NC}"
        else
            echo -e "  ${RED}❌ $service_name tests failed${NC}"
            FAILED_SERVICES+=("$service_name")
        fi
        
        cd ../..
    fi
done

# Run frontend tests if they exist
if [ -d "web" ] && [ -f "web/package.json" ]; then
    echo ""
    echo "⚛️  Running frontend tests..."
    cd web
    
    if [ ! -d "node_modules" ]; then
        npm install >/dev/null 2>&1 || pnpm install >/dev/null 2>&1 || true
    fi
    
    if npm run test 2>&1 || pnpm test 2>&1; then
        echo -e "  ${GREEN}✅ Frontend tests passed${NC}"
    else
        echo -e "  ${RED}❌ Frontend tests failed${NC}"
        FAILED_SERVICES+=("web")
    fi
    
    cd ..
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ ${#FAILED_SERVICES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Tests failed for: ${FAILED_SERVICES[*]}${NC}"
    exit 1
fi

