#!/bin/bash

# Portfolio SuperApp - Deployment Script
# Usage: ./scripts/deploy.sh [build|start|stop|restart|redeploy|logs|health]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dev.yml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to wait for service health
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_wait=${3:-60}
    local wait_time=0
    
    print_info "Waiting for $service_name to be healthy..."
    
    while [ $wait_time -lt $max_wait ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            print_success "$service_name is healthy!"
            return 0
        fi
        sleep 2
        wait_time=$((wait_time + 2))
        echo -n "."
    done
    
    echo ""
    print_warning "$service_name did not become healthy within ${max_wait}s"
    return 1
}

# Function to build images
build_images() {
    print_info "Building Docker images..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    print_success "Images built successfully!"
}

# Function to start services
start_services() {
    print_info "Starting all services..."
    docker compose -f "$COMPOSE_FILE" up -d
    
    print_info "Waiting for services to be ready..."
    sleep 5
    
    # Wait for core services
    wait_for_service "http://localhost:8080/health" "auth-service" 60 || true
    wait_for_service "http://localhost:8081/health" "marketdata-service" 60 || true
    wait_for_service "http://localhost:8082/health" "analytics-service" 60 || true
    wait_for_service "http://localhost:8083/health" "aggregator-service" 60 || true
    wait_for_service "http://localhost:8084/health" "agent-orchestrator" 60 || true
    wait_for_service "http://localhost:8085/health" "notification-service" 60 || true
    wait_for_service "http://localhost:8086/health" "order-orchestrator" 60 || true
    wait_for_service "http://localhost:8088/health" "recommendations-service" 60 || true
    wait_for_service "http://localhost:8000/health" "api-gateway" 60 || true
    
    print_success "All services started!"
    echo ""
    print_info "📋 Service URLs:"
    echo "  Frontend:           http://localhost:3000"
    echo "  API Gateway:        http://localhost:8000"
    echo "  Auth Service:       http://localhost:8080"
    echo "  Marketdata:         http://localhost:8081"
    echo "  Analytics:          http://localhost:8082"
    echo "  Aggregator:         http://localhost:8083"
    echo "  Agent Orchestrator: http://localhost:8084"
    echo "  Notification:       http://localhost:8085"
    echo "  Order Orchestrator: http://localhost:8086"
    echo "  Recommendations:    http://localhost:8088"
    echo "  Prometheus:         http://localhost:9090"
    echo "  Grafana:            http://localhost:3001 (admin/admin)"
}

# Function to stop services
stop_services() {
    print_info "Stopping all services..."
    docker compose -f "$COMPOSE_FILE" down
    print_success "All services stopped!"
}

# Function to restart services
restart_services() {
    print_info "Restarting all services..."
    stop_services
    sleep 2
    start_services
}

# Function to redeploy (rebuild and restart)
redeploy() {
    print_info "Redeploying all services..."
    print_warning "This will rebuild images and restart all services..."
    
    stop_services
    sleep 2
    
    build_images
    start_services
    
    print_success "Redeployment complete!"
}

# Function to show logs
show_logs() {
    print_info "Showing logs (Ctrl+C to exit)..."
    docker compose -f "$COMPOSE_FILE" logs -f
}

# Function to check health
check_health() {
    print_info "Checking service health..."
    echo ""
    
    local services=(
        "auth-service:8080"
        "marketdata-service:8081"
        "analytics-service:8082"
        "aggregator-service:8083"
        "agent-orchestrator:8084"
        "notification-service:8085"
        "order-orchestrator:8086"
        "recommendations-service:8088"
        "api-gateway:8000"
    )
    
    local all_healthy=true
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$name is healthy"
        else
            print_error "$name is unhealthy or not responding"
            all_healthy=false
        fi
    done
    
    echo ""
    if [ "$all_healthy" = true ]; then
        print_success "All services are healthy!"
    else
        print_warning "Some services are unhealthy. Check logs with: ./scripts/deploy.sh logs"
    fi
}

# Function to restart a specific service
restart_service() {
    local service_name=$1
    if [ -z "$service_name" ]; then
        print_error "Service name required"
        echo "Usage: ./scripts/deploy.sh reload <service-name>"
        echo ""
        echo "Available services:"
        echo "  auth-service, marketdata-service, analytics-service, aggregator-service"
        echo "  agent-orchestrator, notification-service, order-orchestrator"
        echo "  recommendations-service, api-gateway, admin-service, web"
        exit 1
    fi
    
    print_info "Restarting $service_name..."
    docker compose -f "$COMPOSE_FILE" restart "$service_name"
    
    if [ $? -eq 0 ]; then
        print_success "$service_name restarted!"
        print_info "View logs with: ./scripts/deploy.sh logs $service_name"
    else
        print_error "Failed to restart $service_name"
        exit 1
    fi
}

# Function to watch all services
watch_all() {
    print_info "Watching all services and web for changes..."
    print_info "Services will auto-reload on file changes"
    print_info "Press Ctrl+C to stop watching"
    echo ""
    print_info "📡 Watching services:"
    print_info "  - recommendations-service (includes News API & Dashboard Notifications)"
    print_info "  - notification-service (email/SMS/push notifications)"
    print_info "  - All other backend services and web frontend"
    echo ""
    
    # List of services to watch
    local services=(
        "auth-service:services/auth-service"
        "marketdata-service:services/marketdata-service"
        "analytics-service:services/analytics-service"
        "aggregator-service:services/aggregator-service"
        "agent-orchestrator:services/agent-orchestrator"
        "notification-service:services/notification-service"
        "order-orchestrator:services/order-orchestrator"
        "recommendations-service:services/recommendations-service"
        "api-gateway:services/api-gateway"
        "admin-service:services/admin-service"
        "web:web"
    )
    
    # Check for file watcher
    local watcher=""
    if command -v fswatch &> /dev/null; then
        watcher="fswatch"
    elif command -v entr &> /dev/null; then
        watcher="entr"
    elif command -v inotifywait &> /dev/null; then
        watcher="inotifywait"
    fi
    
    if [ -z "$watcher" ]; then
        print_warning "No file watcher found. Using manual mode."
        print_info "For macOS: brew install fswatch"
        print_info "For Linux: sudo apt-get install entr or inotify-tools"
        echo ""
        print_info "Press Enter to restart all services, or Ctrl+C to exit"
        while read -r; do
            print_info "Restarting all services..."
            docker compose -f "$COMPOSE_FILE" restart
            print_success "All services reloaded! Press Enter again to restart..."
        done
        return
    fi
    
    # Start watchers for all services
    print_info "Starting watchers for ${#services[@]} services..."
    local pids=()
    
    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_config"
        
        if [ ! -d "$service_path" ]; then
            print_warning "Path not found: $service_path (skipping $service_name)"
            continue
        fi
        
        print_info "  ✓ Watching $service_name ($service_path)"
        
        # Start watcher in background based on available tool
        case "$watcher" in
            fswatch)
                (
                    fswatch -o "$service_path" 2>/dev/null | while read f; do
                        print_info "[$service_name] Change detected, restarting..."
                        docker compose -f "$COMPOSE_FILE" restart "$service_name" >/dev/null 2>&1
                        print_success "[$service_name] Reloaded!"
                    done
                ) &
                pids+=($!)
                ;;
            entr)
                (
                    find "$service_path" -type f 2>/dev/null | entr -p bash -c "
                        echo '[$service_name] Change detected, restarting...'
                        docker compose -f $COMPOSE_FILE restart $service_name >/dev/null 2>&1
                        echo '[$service_name] Reloaded!'
                    " 2>/dev/null
                ) &
                pids+=($!)
                ;;
            inotifywait)
                (
                    while inotifywait -r -e modify,create,delete "$service_path" 2>/dev/null; do
                        print_info "[$service_name] Change detected, restarting..."
                        docker compose -f "$COMPOSE_FILE" restart "$service_name" >/dev/null 2>&1
                        print_success "[$service_name] Reloaded!"
                    done
                ) &
                pids+=($!)
                ;;
        esac
    done
    
    if [ ${#pids[@]} -eq 0 ]; then
        print_error "No services to watch. Check that service directories exist."
        exit 1
    fi
    
    print_success "All watchers started! (${#pids[@]} services)"
    echo ""
    print_info "Monitoring for changes... Press Ctrl+C to stop"
    echo ""
    
    # Cleanup function
    cleanup() {
        print_info "Stopping all watchers..."
        for pid in "${pids[@]}"; do
            kill "$pid" 2>/dev/null || true
        done
        print_success "All watchers stopped"
        exit 0
    }
    
    # Set trap for cleanup
    trap cleanup INT TERM
    
    # Keep script running and wait for all background processes
    wait
}

# Function to watch for file changes and auto-reload
watch_service() {
    local service_name=$1
    local watch_path=${2:-""}
    
    if [ -z "$service_name" ]; then
        print_error "Service name required"
        echo "Usage: ./scripts/deploy.sh watch <service-name> [path]"
        echo ""
        echo "Available services:"
        echo "  auth-service, marketdata-service, analytics-service, aggregator-service"
        echo "  agent-orchestrator, notification-service, order-orchestrator"
        echo "  recommendations-service (includes News API & Dashboard Notifications)"
        echo "  api-gateway, admin-service, web"
        echo ""
        echo "Examples:"
        echo "  ./scripts/deploy.sh watch auth-service"
        echo "  ./scripts/deploy.sh watch recommendations-service"
        echo "  ./scripts/deploy.sh watch notification-service"
        echo "  ./scripts/deploy.sh watch recommendations-service services/recommendations-service"
        exit 1
    fi
    
    # Determine watch path
    if [ -z "$watch_path" ]; then
        case "$service_name" in
            auth-service) watch_path="services/auth-service" ;;
            marketdata-service) watch_path="services/marketdata-service" ;;
            analytics-service) watch_path="services/analytics-service" ;;
            aggregator-service) watch_path="services/aggregator-service" ;;
            agent-orchestrator) watch_path="services/agent-orchestrator" ;;
            notification-service) watch_path="services/notification-service" ;;
            order-orchestrator) watch_path="services/order-orchestrator" ;;
            recommendations-service) watch_path="services/recommendations-service" ;;
            api-gateway) watch_path="services/api-gateway" ;;
            admin-service) watch_path="services/admin-service" ;;
            web) watch_path="web" ;;
            *)
                print_error "Unknown service: $service_name"
                echo ""
                echo "Available services:"
                echo "  auth-service, marketdata-service, analytics-service, aggregator-service"
                echo "  agent-orchestrator, notification-service, order-orchestrator"
                echo "  recommendations-service (includes News API & Dashboard Notifications)"
                echo "  api-gateway, admin-service, web"
                exit 1
                ;;
        esac
    fi
    
    if [ ! -d "$watch_path" ]; then
        print_error "Path not found: $watch_path"
        exit 1
    fi
    
    print_info "Watching $watch_path for changes..."
    print_info "Service $service_name will auto-reload on file changes"
    if [ "$service_name" = "recommendations-service" ]; then
        print_info "📰 This includes: Recommendations API, News API, and Dashboard Notifications"
    elif [ "$service_name" = "notification-service" ]; then
        print_info "🔔 This includes: Email, SMS, Push notifications, and Webhooks"
    fi
    print_info "Press Ctrl+C to stop watching"
    echo ""
    
    # Check if fswatch is available (macOS)
    if command -v fswatch &> /dev/null; then
        fswatch -o "$watch_path" | while read f; do
            print_info "File change detected, restarting $service_name..."
            docker compose -f "$COMPOSE_FILE" restart "$service_name"
            print_success "$service_name reloaded!"
        done
    # Check if entr is available (Linux)
    elif command -v entr &> /dev/null; then
        find "$watch_path" -type f | entr -p docker compose -f "$COMPOSE_FILE" restart "$service_name"
    # Fallback: use inotifywait (Linux)
    elif command -v inotifywait &> /dev/null; then
        while inotifywait -r -e modify,create,delete "$watch_path" 2>/dev/null; do
            print_info "File change detected, restarting $service_name..."
            docker compose -f "$COMPOSE_FILE" restart "$service_name"
            print_success "$service_name reloaded!"
        done
    else
        print_warning "No file watcher found. Installing watch mode..."
        print_info "For macOS: brew install fswatch"
        print_info "For Linux: sudo apt-get install entr or inotify-tools"
        print_info ""
        print_info "Falling back to manual watch mode..."
        print_info "Press Enter to restart $service_name, or Ctrl+C to exit"
        while read -r; do
            docker compose -f "$COMPOSE_FILE" restart "$service_name"
            print_success "$service_name reloaded! Press Enter again to restart..."
        done
    fi
}

# Function to show service logs
show_service_logs() {
    local service_name=$1
    if [ -z "$service_name" ]; then
        show_logs
        return
    fi
    
    print_info "Showing logs for $service_name (Ctrl+C to exit)..."
    docker compose -f "$COMPOSE_FILE" logs -f "$service_name"
}

# Function to show usage
show_usage() {
    echo "Portfolio SuperApp - Deployment Script"
    echo ""
    echo "Usage: ./scripts/deploy.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build              - Build Docker images (no cache)"
    echo "  start              - Start all services"
    echo "  stop               - Stop all services"
    echo "  restart            - Restart all services"
    echo "  redeploy           - Rebuild images and restart all services"
    echo "  reload <service>   - Quick restart of a specific service (hot reload)"
    echo "  watch <service>    - Watch for file changes and auto-reload service"
    echo "  logs [service]     - Show logs (all services or specific service)"
    echo "  health             - Check health of all services"
    echo "  help               - Show this help message"
    echo ""
    echo "Hot Reload Examples:"
    echo "  ./scripts/deploy.sh reload auth-service           # Quick restart"
    echo "  ./scripts/deploy.sh watch recommendations-service # Auto-reload (includes News & Notifications)"
    echo "  ./scripts/deploy.sh watch notification-service    # Auto-reload notification service"
    echo "  ./scripts/deploy.sh watch-all                     # Watch ALL services + web"
    echo "  ./scripts/deploy.sh watch web web                 # Watch specific path"
    echo ""
    echo "Other Examples:"
    echo "  ./scripts/deploy.sh build                         # Build all images"
    echo "  ./scripts/deploy.sh start                         # Start all services"
    echo "  ./scripts/deploy.sh redeploy                      # Full redeploy"
    echo "  ./scripts/deploy.sh logs auth-service            # View specific service logs"
}

# Main script logic
case "${1:-help}" in
    build)
        build_images
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    redeploy)
        redeploy
        ;;
    reload|restart-service)
        restart_service "$2"
        ;;
    watch)
        watch_service "$2" "$3"
        ;;
    watch-all|watchall)
        watch_all
        ;;
    logs)
        show_service_logs "$2"
        ;;
    health)
        check_health
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac

