#!/bin/bash

# Simulate CI build and test locally
# This script mimics what CI does: build images, run tests, check linting

set -e

echo "🔧 Running CI-like build and test locally..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Start CI infrastructure
echo "📦 Step 1: Starting CI infrastructure..."
docker compose -f docker-compose.ci.yml up -d
sleep 5

# Step 2: Build images
echo ""
echo "🏗️  Step 2: Building Docker images..."
FAILED_BUILDS=()

for service_dir in services/*/; do
    if [ -f "$service_dir/Dockerfile" ]; then
        service_name=$(basename "$service_dir")
        echo "  Building $service_name..."
        if docker build -t "portfolio-$service_name:ci" \
            --target prod \
            -f "$service_dir/Dockerfile" \
            "$service_dir" >/dev/null 2>&1; then
            echo -e "    ${GREEN}✅ $service_name built${NC}"
        else
            echo -e "    ${RED}❌ $service_name build failed${NC}"
            FAILED_BUILDS+=("$service_name")
        fi
    fi
done

if [ -f "web/Dockerfile" ]; then
    echo "  Building web..."
    if docker build -t "portfolio-web:ci" \
        --target prod \
        -f web/Dockerfile \
        web >/dev/null 2>&1; then
        echo -e "    ${GREEN}✅ web built${NC}"
    else
        echo -e "    ${RED}❌ web build failed${NC}"
        FAILED_BUILDS+=("web")
    fi
fi

if [ ${#FAILED_BUILDS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Build failed for: ${FAILED_BUILDS[*]}${NC}"
    docker compose -f docker-compose.ci.yml down
    exit 1
fi

# Step 3: Run linters
echo ""
echo "🔍 Step 3: Running linters..."
LINT_FAILURES=()

for service_dir in services/*/; do
    if [ -f "$service_dir/pyproject.toml" ]; then
        service_name=$(basename "$service_dir")
        echo "  Linting $service_name..."
        cd "$service_dir"
        if poetry run ruff check . >/dev/null 2>&1 && \
           poetry run black --check . >/dev/null 2>&1; then
            echo -e "    ${GREEN}✅ $service_name lint passed${NC}"
        else
            echo -e "    ${RED}❌ $service_name lint failed${NC}"
            LINT_FAILURES+=("$service_name")
        fi
        cd ../..
    fi
done

if [ -d "web" ] && [ -f "web/package.json" ]; then
    echo "  Linting web..."
    cd web
    if npm run lint >/dev/null 2>&1 || pnpm lint >/dev/null 2>&1; then
        echo -e "    ${GREEN}✅ web lint passed${NC}"
    else
        echo -e "    ${RED}❌ web lint failed${NC}"
        LINT_FAILURES+=("web")
    fi
    cd ..
fi

if [ ${#LINT_FAILURES[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Lint failures (non-blocking): ${LINT_FAILURES[*]}${NC}"
fi

# Step 4: Run tests
echo ""
echo "🧪 Step 4: Running tests..."
./scripts/bootstrap-dev.sh --migrate-only

# Run tests in CI mode (using CI compose)
export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-user}:${POSTGRES_PASSWORD:-password}@localhost:5432"
export REDIS_URL="redis://localhost:6379/0"
export TESTING=true

TEST_FAILURES=()

for service_dir in services/*/; do
    if [ -d "$service_dir/tests" ] && [ -f "$service_dir/pyproject.toml" ]; then
        service_name=$(basename "$service_dir")
        echo "  Testing $service_name..."
        
        cd "$service_dir"
        
        # Create test database
        docker compose -f ../../docker-compose.ci.yml exec -T postgres \
            psql -U ${POSTGRES_USER:-user} -c "CREATE DATABASE ${service_name}_test_db;" 2>/dev/null || true
        
        export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-user}:${POSTGRES_PASSWORD:-password}@localhost:5432/${service_name}_test_db"
        
        if poetry run pytest -v --tb=short --cov=. --cov-report=term-missing >/dev/null 2>&1; then
            echo -e "    ${GREEN}✅ $service_name tests passed${NC}"
        else
            echo -e "    ${RED}❌ $service_name tests failed${NC}"
            TEST_FAILURES+=("$service_name")
        fi
        
        cd ../..
    fi
done

# Step 5: Cleanup
echo ""
echo "🧹 Step 5: Cleaning up..."
docker compose -f docker-compose.ci.yml down

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 CI Simulation Summary:"
echo "  Builds: ${#FAILED_BUILDS[@]} failed"
echo "  Lints: ${#LINT_FAILURES[@]} failed"
echo "  Tests: ${#TEST_FAILURES[@]} failed"

if [ ${#FAILED_BUILDS[@]} -eq 0 ] && [ ${#TEST_FAILURES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ CI simulation passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ CI simulation failed!${NC}"
    exit 1
fi

