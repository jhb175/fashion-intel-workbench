#!/bin/bash
# ============================================
# Fashion Intel Workbench — Server Deploy
# Run this on your server via SSH
# ============================================
set -e

DOMAIN="fashion.565312.xyz"
APP_DIR="/opt/fashion-intel"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}═══ Fashion Intel Workbench — Server Deploy ═══${NC}"

# 1. Install dependencies
echo -e "${YELLOW}[1/8] Installing dependencies...${NC}"
apt-get update -qq
apt-get install -y -qq docker.io docker-compose-plugin git python3 python3-pip certbot python3-certbot-nginx > /dev/null 2>&1
systemctl enable docker
systemctl start docker
echo -e "${GREEN}✓ Dependencies installed${NC}"

# 2. Clone repo
echo -e "${YELLOW}[2/8] Cloning repository...${NC}"
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone https://github.com/jhb175/fashion-intel-workbench.git "$APP_DIR"
    cd "$APP_DIR"
fi
echo -e "${GREEN}✓ Repository ready${NC}"

# 3. Generate .env
echo -e "${YELLOW}[3/8] Generating .env...${NC}"
if [ ! -f .env ]; then
    JWT_SECRET=$(openssl rand -base64 32)
    PG_PASS=$(openssl rand -hex 16)
    FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)

    cat > .env << EOF
POSTGRES_USER=fashion_intel
POSTGRES_PASSWORD=${PG_PASS}
POSTGRES_DB=fashion_intel
DATABASE_URL=postgresql+asyncpg://fashion_intel:${PG_PASS}@postgres:5432/fashion_intel
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
ENCRYPTION_KEY=${FERNET_KEY}
CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN}
NEXT_PUBLIC_API_URL=/api/v1
EOF
    echo -e "${GREEN}✓ .env created with generated secrets${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# 4. SSL cert
echo -e "${YELLOW}[4/8] Setting up SSL...${NC}"
mkdir -p nginx/ssl
if [ ! -f nginx/ssl/fullchain.pem ]; then
    # Try Let's Encrypt first, fall back to self-signed
    certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@${DOMAIN} 2>/dev/null && {
        cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem nginx/ssl/
        cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem nginx/ssl/
        echo -e "${GREEN}✓ Let's Encrypt SSL cert obtained${NC}"
    } || {
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/privkey.pem -out nginx/ssl/fullchain.pem \
            -subj "/CN=${DOMAIN}" 2>/dev/null
        echo -e "${YELLOW}✓ Self-signed SSL cert created (replace with Let's Encrypt later)${NC}"
    }
else
    echo -e "${GREEN}✓ SSL certs already exist${NC}"
fi

# 5. Configure host Nginx as reverse proxy
echo -e "${YELLOW}[5/8] Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/fashion-intel << EOF
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    ssl_certificate     ${APP_DIR}/nginx/ssl/fullchain.pem;
    ssl_certificate_key ${APP_DIR}/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    client_max_body_size 20m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    # Backend health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
    }

    # Uploaded files (logos)
    location /uploads/ {
        alias ${APP_DIR}/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Next.js static assets
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    # Frontend (everything else)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/fashion-intel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo -e "${GREEN}✓ Nginx configured for ${DOMAIN}${NC}"

# 6. Build Docker images (without the nginx service since host nginx is used)
echo -e "${YELLOW}[6/8] Building Docker images...${NC}"

# Create a simplified docker-compose for this setup (no nginx container, expose ports)
cat > docker-compose.server.yml << 'EOF'
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-fashion_intel}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-fashion_intel}
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: always
    command: ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-fashion_intel}
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        NEXT_PUBLIC_API_URL: /api/v1
    restart: always
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
EOF

docker compose -f docker-compose.server.yml build
echo -e "${GREEN}✓ Docker images built${NC}"

# 7. Start services
echo -e "${YELLOW}[7/8] Starting services...${NC}"
docker compose -f docker-compose.server.yml up -d
echo -e "${GREEN}✓ Services started${NC}"

# 8. Wait and verify
echo -e "${YELLOW}[8/8] Verifying deployment...${NC}"
sleep 15

if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Backend not ready yet (may need more time)${NC}"
fi

if curl -sf http://127.0.0.1:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠ Frontend not ready yet (may need more time)${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       Deploy Complete! 🎉                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Site:   https://${DOMAIN}"
echo -e "  Login:  admin / admin123"
echo ""
echo -e "  ${YELLOW}Logs:${NC}  docker compose -f docker-compose.server.yml logs -f"
echo -e "  ${YELLOW}Stop:${NC}  docker compose -f docker-compose.server.yml down"
echo ""
