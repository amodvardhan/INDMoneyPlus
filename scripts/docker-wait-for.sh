#!/bin/bash

# Wait for a service to be healthy by polling a health endpoint
# Usage: ./scripts/docker-wait-for.sh <url> <service-name> [timeout-seconds]

set -e

URL="${1}"
SERVICE_NAME="${2}"
TIMEOUT="${3:-60}"

if [ -z "$URL" ] || [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <url> <service-name> [timeout-seconds]"
    exit 1
fi

echo "⏳ Waiting for $SERVICE_NAME to be healthy at $URL (timeout: ${TIMEOUT}s)..."

COUNTER=0
while [ $COUNTER -lt $TIMEOUT ]; do
    if curl -sf "$URL" > /dev/null 2>&1; then
        echo "✅ $SERVICE_NAME is healthy!"
        exit 0
    fi
    sleep 1
    COUNTER=$((COUNTER + 1))
    if [ $((COUNTER % 5)) -eq 0 ]; then
        echo "   Still waiting... (${COUNTER}/${TIMEOUT}s)"
    fi
done

echo "❌ $SERVICE_NAME failed to become healthy within ${TIMEOUT}s"
exit 1

