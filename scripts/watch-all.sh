#!/bin/bash

# Quick watch-all script for hot reload
# Usage: ./scripts/watch-all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Call the watch-all function from deploy.sh
exec "$SCRIPT_DIR/deploy.sh" watch-all "$@"
