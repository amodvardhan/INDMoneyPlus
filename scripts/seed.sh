#!/bin/bash

# Seed script to load test data into services
# This is called by bootstrap-dev.sh

set -e

echo "🌱 Seeding test data..."

# Load SQL seed files if they exist
if [ -d "./seed" ]; then
    for sql_file in ./seed/*.sql; do
        if [ -f "$sql_file" ]; then
            db_name="portfolio_superapp"
            echo "  Loading $(basename $sql_file) into $db_name..."
            docker compose -f docker-compose.dev.yml exec -T postgres \
                psql -U ${POSTGRES_USER:-user} -d $db_name < "$sql_file" 2>/dev/null || \
            docker compose -f docker-compose.ci.yml exec -T postgres \
                psql -U ${POSTGRES_USER:-user} -d $db_name < "$sql_file" 2>/dev/null || true
        fi
    done
fi

# Run service-specific seed scripts
for service_dir in services/*/; do
    if [ -f "$service_dir/scripts/seed.py" ]; then
        service_name=$(basename "$service_dir")
        echo "  Seeding $service_name via Python script..."
        
        if docker compose -f docker-compose.dev.yml ps "$service_name" 2>/dev/null | grep -q "Up"; then
            docker compose -f docker-compose.dev.yml exec -T "$service_name" \
                poetry run python scripts/seed.py 2>/dev/null || true
        elif [ -f "$service_dir/pyproject.toml" ]; then
            cd "$service_dir"
            poetry install --no-interaction --no-ansi >/dev/null 2>&1 || true
            poetry run python scripts/seed.py 2>/dev/null || true
            cd ../..
        fi
    fi
done

echo "✅ Seed data loaded!"

