# DEPLOYMENT.md - COSKA Deployment Guide

## Quick Start (Development)

### Prerequisites
- Python 3.12+
- Node.js 20+
- SQLite (included)
- Optional: Docker for sandbox

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # Port 5173
```

### Verify
- Backend: http://localhost:8000/api/health
- Frontend: http://localhost:5173
- Docs: http://localhost:8000/docs (FastAPI auto-docs)

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

#### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AI_PROVIDER=nebius
      - NEBIUS_API_KEY=${NEBIUS_API_KEY}
      - NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
      - NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b
      - TAVILY_ENABLED=true
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - AUTH_REQUIRED=true
      - SESSION_SECRET=${SESSION_SECRET}
      - DATABASE_URL=sqlite:///./data/coska.db
      - APP_ENV=production
      - SANDBOX_MODE=docker
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api
    restart: unless-stopped
```

#### Dockerfile (Multi-stage)
```dockerfile
# Build stage - Backend
FROM python:3.12-slim AS backend-builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --user -r requirements.txt

# Build stage - Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Runtime stage
FROM python:3.12-slim
WORKDIR /app

# Copy Python packages
COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend
COPY backend/ .

# Copy frontend build
COPY --from=frontend-builder /app/dist ./frontend/dist

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name coska.example.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name coska.example.com;

        ssl_certificate /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API
        location /api/ {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
        }

        # Health
        location /health {
            proxy_pass http://api/api/health;
            access_log off;
        }
    }
}
```

#### Deploy
```bash
# Set secrets
export NEBIUS_API_KEY=your_key
export TAVILY_API_KEY=your_key
export SESSION_SECRET=$(openssl rand -hex 32)

# Deploy
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify
curl https://coska.example.com/api/health
```

---

### Option 2: Separate Deployments

#### Backend (Render/Railway/Fly.io)
```yaml
# render.yaml
services:
  - type: web
    name: coska-api
    runtime: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: AI_PROVIDER
        value: nebius
      - key: NEBIUS_API_KEY
        sync: false
      - key: TAVILY_API_KEY
        sync: false
      - key: AUTH_REQUIRED
        value: "true"
      - key: SESSION_SECRET
        generateValue: true
      - key: DATABASE_URL
        value: sqlite:///./data/coska.db
      - key: SANDBOX_MODE
        value: docker
    disk:
      name: data
      mountPath: /app/data
      sizeGB: 1
```

#### Frontend (Vercel/Netlify)
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://your-api.render.com/api/$1" }
  ],
  "env": {
    "VITE_API_URL": "https://your-api.render.com"
  }
}
```

---

## Environment Variables

### Required for Live Integration
```bash
# AI Provider
AI_PROVIDER=nebius                    # mock | nebius | auto
NEBIUS_API_KEY=                       # Nebius Token Factory key
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b

# Tavily
TAVILY_ENABLED=true
TAVILY_API_KEY=

# Auth (Production)
AUTH_REQUIRED=true
SESSION_SECRET=                       # 32+ bytes, generate: openssl rand -hex 32

# Database
DATABASE_URL=sqlite:///./data/coska.db

# Sandbox
SANDBOX_MODE=docker                   # local | docker | auto
SANDBOX_TIMEOUT=300
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1.0

# Safety Budgets
MAX_AGENT_STEPS=40
MAX_TOOL_CALLS=25
MAX_RETRIES=3
MAX_INVESTIGATION_TIME=300
```

### Development (Defaults)
```bash
AI_PROVIDER=mock
TAVILY_ENABLED=false
AUTH_REQUIRED=false
SANDBOX_MODE=local
```

---

## Health & Monitoring

### Health Endpoints
```bash
# Basic
curl http://localhost:8000/api/health

# AI Provider
curl http://localhost:8000/api/health/ai

# Tavily
curl http://localhost:8000/api/health/tavily

# Sandbox
curl http://localhost:8000/api/health/sandbox
```

### Expected Responses
```json
// /api/health
{"status": "healthy", "service": "coska", "version": "0.1.0"}

// /api/health/ai (mock)
{"status": "healthy", "provider": "mock", "model": "coska-deterministic-mock", "reachable": true, "authenticated": true, "model_available": true}

// /api/health/ai (nebius)
{"status": "healthy", "provider": "nebius", "model": "nvidia/nemotron-3-ultra-550b-a55b", "reachable": true, "authenticated": true, "model_available": true}

// /api/health/tavily
{"status": "healthy", "configured": true, "connected": true}

// /api/health/sandbox
{"status": "healthy", "provider": "local_safe", "available": true, "mode": "local"}
```

---

## Database Management

### Backup
```bash
# SQLite backup (online)
sqlite3 data/coska.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Or copy (WAL mode safe)
cp data/coska.db backup_$(date +%Y%m%d_%H%M%S).db
cp data/coska.db-wal backup_$(date +%Y%m%d_%H%M%S).db-wal
cp data/coska.db-shm backup_$(date +%Y%m%d_%H%M%S).db-shm
```

### Restore
```bash
# Stop services first
docker-compose stop

# Restore
cp backup_20261030_120000.db data/coska.db
cp backup_20261030_120000.db-wal data/coska.db-wal
cp backup_20261030_120000.db-shm data/coska.db-shm

# Restart
docker-compose up -d
```

### Migration (Future)
```bash
# When schema changes:
# 1. Create migration script
# 2. Test on copy
# 3. Backup
# 4. Run migration
# 5. Verify
```

---

## Scaling Considerations

| Component | Current | Scaling Approach |
|-----------|---------|------------------|
| API | Single FastAPI | Horizontal (load balancer + multiple replicas) |
| Database | SQLite | Migrate to PostgreSQL + connection pooling |
| Sandbox | Local/Docker | Kubernetes jobs / gVisor |
| RAG | In-memory BM25 | Redis cache + vector DB hybrid |
| Auth | In-memory sessions | Redis-backed distributed sessions |
| Rate Limiting | In-memory | Redis-backed distributed |
| Audit Logs | SQLite table | Elasticsearch / OpenSearch |

---

## Security Hardening (Production)

### SSL/TLS
```nginx
# nginx.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Secrets Rotation
```bash
# Rotate NEBIUS_API_KEY
# 1. Generate new key in Nebius console
# 2. Update deployment secret
# 3. Restart api service
# 4. Verify health check

# Rotate SESSION_SECRET
# 1. Generate new: openssl rand -hex 32
# 2. Update deployment secret
# 3. All users logged out (expected)
# 3. Restart api service
```

### Database Encryption (Future)
```bash
# SQLite encryption (SQLCipher)
# Or migrate to PostgreSQL with TDE
```

---

## Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| API returns 500 | Check logs: `docker-compose logs api` | Check DB permissions, env vars |
| Frontend shows "API unreachable" | Check VITE_API_URL, CORS | Verify nginx proxy, API health |
| Database locked | SQLite concurrency | Enable WAL mode, reduce concurrent writes |
| Sandbox fails | Docker not running | Enable Docker, check `docker ps` |
| AI provider unhealthy | Check `/api/health/ai` | Verify API key, network |
| Tavily not working | Check `/api/health/tavily` | Verify API key, enable TAVILY_ENABLED |
| Rate limited (429) | Check rate limit middleware | Adjust limits, add Redis backend |
| Database locked | Concurrent writes | Enable WAL, reduce concurrency |

---

## Backup Strategy

```bash
#!/bin/bash
# backup.sh - Run via cron daily

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Stop writes briefly (optional)
# docker-compose pause api

# Backup SQLite + WAL/SHM
cp /app/data/coska.db $BACKUP_DIR/coska_$DATE.db
cp /app/data/coska.db-wal $BACKUP_DIR/coska_$DATE.db-wal 2>/dev/null || true
cp /app/data/coska.db-shm $BACKUP_DIR/coska_$DATE.db-shm 2>/dev/null || true

# Compress
tar -czf $BACKUP_DIR/coska_$DATE.tar.gz -C $BACKUP_DIR coska_$DATE.db*

# Cleanup old (keep 30 days)
find $BACKUP_DIR -name "coska_*.tar.gz" -mtime +30 -delete

# Resume
# docker-compose unpause api

echo "Backup complete: $BACKUP_DIR/coska_$DATE.tar.gz"
```

---

## Rollback Procedure

```bash
# 1. Stop services
docker-compose stop

# 2. Restore database
cp /backups/coska_20261030_120000.db /app/data/coska.db
cp /backups/coska_20261030_120000.db-wal /app/data/coska.db-wal
cp /backups/coska_20261030_120000.db-shm /app/data/coska.db-shm

# 3. Restore code (if needed)
git checkout v1.2.3  # Previous tag
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Verify
curl https://coska.example.com/api/health
python scripts/evaluate_coska.py
```

---

## CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install backend deps
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run backend tests
        run: |
          cd backend
          python -m pytest -q
      
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install frontend deps
        run: |
          cd frontend
          npm ci
      
      - name: TypeScript check
        run: |
          cd frontend
          npx tsc --noEmit
      
      - name: Build frontend
        run: |
          cd frontend
          npm run build
      
      - name: Security scan
        run: |
          python scripts/security_check.py
      
      - name: Evaluation harness
        run: |
          python scripts/evaluate_coska.py
```

---

## Rollout Strategy

| Phase | Traffic | Duration | Success Criteria |
|-------|---------|----------|------------------|
| Canary | 5% | 1 hour | Health checks pass, no errors |
| Partial | 25% | 2 hours | P99 latency < 500ms, error rate < 0.1% |
| Full | 100% | - | All metrics stable |

---

## Maintenance Windows

| Task | Frequency | Window |
|------|-----------|--------|
| Database backup | Daily | 03:00 UTC |
| Security scan | Weekly | Monday 02:00 UTC |
| Dependency audit | Monthly | 1st Monday 02:00 UTC |
| Log rotation | Daily | 04:00 UTC |
| Certificate renewal | 90 days | Automated (Let's Encrypt) |