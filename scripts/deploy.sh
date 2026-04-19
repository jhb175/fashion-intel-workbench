#!/bin/bash
# ============================================
# Fashion Intel Workbench — One-Click Deploy
# ============================================
# Usage: bash scripts/deploy.sh
# Requires: Docker + Docker Compose

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Fashion Intel Workbench — Deploy Script ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Install: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker found"

if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose found"

# Create .env if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}→ Creating .env from template...${NC}"
    cp .env.example .env

    # Generate secrets
    JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "change-me-in-production")

    # Replace placeholders
    sed -i "s|JWT_SECRET_KEY=change-me-in-production|JWT_SECRET_KEY=${JWT_SECRET}|g" .env
    sed -i "s|ENCRYPTION_KEY=change-me-in-production|ENCRYPTION_KEY=${FERNET_KEY}|g" .env
    sed -i "s|POSTGRES_PASSWORD=postgres|POSTGRES_PASSWORD=$(openssl rand -hex 16 2>/dev/null || echo 'strongpassword123')|g" .env

    echo -e "${GREEN}✓${NC} .env created with generated secrets"
    echo -e "${YELLOW}  ⚠ Edit .env to set CORS_ORIGINS to your domain${NC}"
else
    echo -e "${GREEN}✓${NC} .env already exists"
fi

# Create SSL directory
mkdir -p nginx/ssl

if [ ! -f nginx/ssl/fullchain.pem ]; then
    echo -e "${YELLOW}→ Generating self-signed SSL cert (replace with real cert later)...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/privkey.pem \
        -out nginx/ssl/fullchain.pem \
        -subj "/CN=localhost" 2>/dev/null
    echo -e "${GREEN}✓${NC} Self-signed SSL cert created"
else
    echo -e "${GREEN}✓${NC} SSL certs already exist"
fi

# Build and start
echo ""
echo -e "${YELLOW}→ Building Docker images...${NC}"
docker compose -f docker-compose.prod.yml build

echo ""
echo -e "${YELLOW}→ Starting services...${NC}"
docker compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${YELLOW}→ Waiting for services to start...${NC}"
sleep 10

# Run database migration
echo -e "${YELLOW}→ Running database migration...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python -m alembic upgrade head 2>/dev/null || echo "  (migration skipped — tables may already exist)"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Deploy Complete! 🎉             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}HTTPS:${NC}  https://localhost"
echo -e "  ${GREEN}HTTP:${NC}   http://localhost (redirects to HTTPS)"
echo -e "  ${GREEN}API:${NC}    https://localhost/health"
echo -e "  ${GREEN}Login:${NC}  admin / admin123"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo -e "  1. Edit .env → set CORS_ORIGINS to your domain"
echo -e "  2. Replace nginx/ssl/ certs with real ones (Let's Encrypt)"
echo -e "  3. Login → AI 配置 → add your OpenAI API key"
echo -e "  4. 后台管理 → 资讯源 → ⚡ 立即采集全部"
echo ""
