#!/bin/bash
# ============================================
# Fashion Intel Workbench — Local Dev Setup
# ============================================
# Usage: bash scripts/dev.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up local development environment...${NC}"

# Backend
echo -e "${YELLOW}→ Installing backend dependencies...${NC}"
cd backend
pip install -e ".[dev]" -q
if [ ! -f .env ]; then
    cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./fashion_intel.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=local-dev-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
CORS_ORIGINS=http://localhost:3000
EOF
    echo -e "${GREEN}✓${NC} backend/.env created"
fi
cd ..

# Frontend
echo -e "${YELLOW}→ Installing frontend dependencies...${NC}"
cd frontend
npm install -q
cd ..

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "Start backend:  cd backend && python -m uvicorn app.main:app --reload --port 8000"
echo "Start frontend: cd frontend && npm run dev"
echo "Login: admin / admin123"
