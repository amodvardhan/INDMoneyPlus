#!/bin/bash
# Wrapper script to flush Redis cache - runs from project root
# Usage: ./scripts/flush_redis.sh [--all|--ticker TICKER --exchange EXCHANGE|--stats]

# Check if running in Docker or locally
if command -v docker &> /dev/null && docker compose -f docker-compose.dev.yml ps marketdata-service 2>/dev/null | grep -q "Up"; then
    # Running in Docker - execute inside container
    echo "🐳 Running in Docker container..."
    docker compose -f docker-compose.dev.yml exec marketdata-service poetry run python scripts/flush_redis.py "$@"
elif command -v poetry &> /dev/null; then
    # Running locally with Poetry
    cd services/marketdata-service || exit 1
    poetry run python scripts/flush_redis.py "$@"
else
    echo "❌ Error: Neither Docker nor Poetry is available."
    echo ""
    echo "Options:"
    echo "1. Install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
    echo "2. Use Docker: make dev-up (then run this script again)"
    echo "3. Use API endpoint: curl -X POST http://localhost:8003/api/v1/cache/flush"
    exit 1
fi
