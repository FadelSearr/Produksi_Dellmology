#!/bin/bash
# Dellmology Pro - Complete Startup Script
# Run this script to start all services

set -e  # Exit on error

echo "🚀 Starting Dellmology Pro Platform..."
echo "========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}[1/5]${NC} Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Start Database
echo -e "${YELLOW}[2/5]${NC} Starting Database..."
docker-compose up -d db redis
sleep 5  # Wait for DB to be ready

echo -e "${GREEN}✓ Database started${NC}"

# Check .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠  .env file not found, creating from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}  ⚠  Please update .env with your credentials${NC}"
fi

echo -e "${GREEN}✓ Environment configured${NC}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✓ All infrastructure started${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

echo "📚 Next steps:"
echo ""
echo "  Terminal 1 - Python ML Services:"
echo "    $ cd apps/ml-engine"
echo "    $ python -m venv venv"
echo "    $ source venv/bin/activate  (or venv\\Scripts\\activate on Windows)"
echo "    $ pip install -r requirements.txt"
echo "    $ python global_market_aggregator.py"
echo ""

echo "  Terminal 2 - Go Streamer:"
echo "    $ cd apps/streamer"
echo "    $ go mod download"
echo "    $ go run main.go market_regime.go broker_analysis.go"
echo ""

echo "  Terminal 3 - Next.js Frontend:"
echo "    $ cd apps/web"
echo "    $ npm install"
echo "    $ npm run dev"
echo ""

echo "  Then open browser: http://localhost:3000"
echo ""

echo -e "${GREEN}✓ Platform ready to launch!${NC}"
echo ""
echo "📊 Docker Services Running:"
docker ps --format "{{.Names}}\t{{.Status}}" | grep -E "dellmology|postgres|redis|timescale" || true
