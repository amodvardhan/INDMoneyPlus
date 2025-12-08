#!/bin/bash

# Web Application Deployment Script
# This script helps deploy only the web application

set -e

echo "🚀 Starting web application deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the web directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: Must run from web directory${NC}"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo -e "${YELLOW}⚠️  Warning: Node.js 20+ recommended. Current: $(node -v)${NC}"
fi

# Check for environment variables
if [ -z "$NEXT_PUBLIC_API_URL" ]; then
    echo -e "${YELLOW}⚠️  Warning: NEXT_PUBLIC_API_URL not set${NC}"
    echo "   Set it with: export NEXT_PUBLIC_API_URL=https://api.yourdomain.com"
fi

# Ensure symlink for lightweight-charts exists (for workspace setup)
if [ ! -d "node_modules/lightweight-charts" ] && [ -d "../node_modules/lightweight-charts" ]; then
    echo -e "${YELLOW}📦 Creating symlink for lightweight-charts...${NC}"
    mkdir -p node_modules
    ln -sf ../../node_modules/lightweight-charts node_modules/lightweight-charts
fi

# Install dependencies
echo -e "${GREEN}📦 Installing dependencies...${NC}"
npm ci

# Type check
echo -e "${GREEN}🔍 Running type check...${NC}"
npm run type-check || echo -e "${YELLOW}⚠️  Type check failed, continuing...${NC}"

# Lint
echo -e "${GREEN}🔍 Running linter...${NC}"
npm run lint || echo -e "${YELLOW}⚠️  Lint failed, continuing...${NC}"

# Build
echo -e "${GREEN}🏗️  Building application...${NC}"
npm run build

echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo "To start the production server:"
echo "  npm run start"
echo ""
echo "Or deploy using Docker:"
echo "  docker build -t portfolio-web:latest ."
echo "  docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=\$NEXT_PUBLIC_API_URL portfolio-web:latest"
