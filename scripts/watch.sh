#!/bin/bash

# Quick watch script for hot reload
# Usage: ./scripts/watch.sh <service-name> [path]
#
# Examples:
#   ./scripts/watch.sh recommendations-service  # Watch recommendations (includes News API & Dashboard Notifications)
#   ./scripts/watch.sh notification-service     # Watch notification service (email/SMS/push)
#   ./scripts/watch.sh marketdata-service       # Watch marketdata service
#   ./scripts/watch.sh web                     # Watch web frontend
#
# Available services:
#   - recommendations-service (includes News API & Dashboard Notifications)
#   - notification-service (email/SMS/push notifications)
#   - auth-service, marketdata-service, analytics-service, aggregator-service
#   - agent-orchestrator, order-orchestrator, api-gateway, admin-service, web

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Call the watch function from deploy.sh
exec "$SCRIPT_DIR/deploy.sh" watch "$@"

