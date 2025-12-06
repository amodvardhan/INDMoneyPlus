#!/bin/bash

set -e

MIGRATE_ONLY=false
SEED_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --migrate-only)
            MIGRATE_ONLY=true
            shift
            ;;
        --seed-only)
            SEED_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 Bootstrapping Portfolio Superapp development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Create .env.dev.local file if it doesn't exist
if [ ! -f .env.dev.local ]; then
    if [ -f .env.example ]; then
        echo "📝 Creating .env.dev.local file from .env.example..."
        cp .env.example .env.dev.local
        echo "✅ Created .env.dev.local - please review and update as needed"
    else
        echo "⚠️  .env.example not found, creating .env.dev.local with defaults..."
        # Create minimal .env.dev.local with essential variables
        cat > .env.dev.local << 'EOF'
# Portfolio SuperApp - Development Environment Variables
# Auto-generated - review and update as needed

POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=portfolio_superapp
JWT_SECRET=dev-secret-key-change-in-production
LOG_LEVEL=INFO
EOF
        echo "✅ Created .env.dev.local with default values"
    fi
fi

# Start infrastructure services if not seed-only
if [ "$SEED_ONLY" = false ]; then
    echo "🐳 Starting infrastructure services..."
    docker compose -f docker-compose.dev.yml up -d postgres redis redpanda vector-db-mock 2>/dev/null || \
    docker compose -f docker-compose.ci.yml up -d postgres redis redpanda vector-db-mock 2>/dev/null || true

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
    until docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-user} >/dev/null 2>&1 || \
          docker compose -f docker-compose.ci.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-user} >/dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo "❌ PostgreSQL failed to start within $timeout seconds"
        exit 1
    fi
done

echo "✅ PostgreSQL is ready!"

# Create databases
echo "📦 Creating databases..."
    for db in auth_db aggregator_db marketdata_db order_db admin_db worker_db notification_db agent_orchestrator_db recommendations_db; do
        docker compose -f docker-compose.dev.yml exec -T postgres psql -U ${POSTGRES_USER:-user} -d postgres -c "CREATE DATABASE $db;" 2>/dev/null || \
        docker compose -f docker-compose.ci.yml exec -T postgres psql -U ${POSTGRES_USER:-user} -d postgres -c "CREATE DATABASE $db;" 2>/dev/null || \
        echo "  $db may already exist"
    done
fi

# Run migrations
if [ "$SEED_ONLY" = false ]; then
echo "🔄 Running database migrations..."
    for service_dir in services/*/; do
        if [ -d "$service_dir/alembic" ] && [ -f "$service_dir/alembic.ini" ]; then
            service_name=$(basename "$service_dir")
            echo "  Running migrations for $service_name..."
            
            # Try to run migrations in container if service is running
            if docker compose -f docker-compose.dev.yml ps "$service_name" 2>/dev/null | grep -q "Up"; then
                docker compose -f docker-compose.dev.yml exec -T "$service_name" sh -c \
                    "cd /app && poetry run alembic upgrade head" 2>/dev/null || \
                docker compose -f docker-compose.dev.yml exec -T "$service_name" sh -c \
                    "cd /app && alembic upgrade head" 2>/dev/null || true
            else
                # Run migrations locally if service not running
                if [ -f "$service_dir/pyproject.toml" ]; then
                    cd "$service_dir"
                    poetry install --no-interaction --no-ansi >/dev/null 2>&1 || true
                    poetry run alembic upgrade head 2>/dev/null || \
                    alembic upgrade head 2>/dev/null || true
        cd ../..
                fi
            fi
        fi
    done
    echo "✅ Migrations complete!"
fi

# Seed test data
if [ "$MIGRATE_ONLY" = false ]; then
    echo "🌱 Seeding test data..."
    
    # Run seed script if it exists
    if [ -f "./scripts/seed.sh" ]; then
        ./scripts/seed.sh
    elif [ -d "./seed" ]; then
        # Run SQL seed files
        for sql_file in ./seed/*.sql; do
            if [ -f "$sql_file" ]; then
                echo "  Seeding from $(basename $sql_file)..."
                docker compose -f docker-compose.dev.yml exec -T postgres psql -U ${POSTGRES_USER:-user} -d portfolio_superapp < "$sql_file" 2>/dev/null || \
                docker compose -f docker-compose.ci.yml exec -T postgres psql -U ${POSTGRES_USER:-user} -d portfolio_superapp < "$sql_file" 2>/dev/null || true
    fi
done

        # Run service-specific seed scripts
        for service_dir in services/*/; do
            if [ -f "$service_dir/scripts/seed.py" ] || [ -f "$service_dir/scripts/seed.sh" ]; then
                service_name=$(basename "$service_dir")
                echo "  Seeding $service_name..."
                if [ -f "$service_dir/scripts/seed.py" ]; then
                    if docker compose -f docker-compose.dev.yml ps "$service_name" 2>/dev/null | grep -q "Up"; then
                        docker compose -f docker-compose.dev.yml exec -T "$service_name" \
                            poetry run python scripts/seed.py 2>/dev/null || true
                    fi
                elif [ -f "$service_dir/scripts/seed.sh" ]; then
                    bash "$service_dir/scripts/seed.sh" || true
                fi
            fi
        done
    fi
    
    echo "✅ Seed data loaded!"
fi

if [ "$MIGRATE_ONLY" = false ] && [ "$SEED_ONLY" = false ]; then
    echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "📋 Next steps:"
    echo "  1. Start all services: make dev-up"
    echo "  2. Check service health: make health-check"
    echo "  3. View logs: make dev-logs"
echo "  4. Access Frontend: http://localhost:3000"
    echo "  5. Access API Gateway: http://localhost:8000"
fi
