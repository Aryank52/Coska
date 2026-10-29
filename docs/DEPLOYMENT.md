# COSKA Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose 2+
- Python 3.12+ (for local development)
- Node.js 18+ (for frontend development)
- Nebius Token Factory API key
- Tavily API key (optional, for web research)

## Environment Variables

Create `.env` from `.env.example`:

```bash
# Required
NEBIUS_API_KEY=your_nebius_token_factory_key
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b

# Optional (web research)
TAVILY_API_KEY=your_tavily_key

# Database
DATABASE_URL=sqlite:///./coska.db

# Application
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# Frontend
VITE_API_URL=https://your-domain.com/api
```

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env  # Edit with your keys
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173 (proxies /api to localhost:8000)
```

### Demo Payment API
```bash
cd demo/payment-api
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

## Docker Deployment

### Development with Docker Compose
```bash
docker-compose up --build
```

Services:
- `coska-backend`: http://localhost:8000
- `coska-frontend`: http://localhost:5173
- `payment-api`: http://localhost:8001
- `coska-db`: SQLite volume

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  coska-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - NEBIUS_API_KEY=${NEBIUS_API_KEY}
      - NEBIUS_BASE_URL=${NEBIUS_BASE_URL}
      - NEBIUS_MODEL=${NEBIUS_MODEL}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - DATABASE_URL=sqlite:///./data/coska.db
      - APP_ENV=production
    volumes:
      - coska-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  coska-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    environment:
      - VITE_API_URL=https://your-domain.com/api
    depends_on:
      - coska-backend
    restart: unless-stopped

  payment-api:
    build:
      context: ./demo/payment-api
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - DB_POOL_SIZE=30  # Fixed in production!
      - DATABASE_URL=sqlite+aiosqlite:///./data/payments.db
    volumes:
      - payment-data:/app/data
    restart: unless-stopped

volumes:
  coska-data:
  payment-data:
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## Nebius Serverless Deployment (Optional)

### Backend as Serverless Endpoint

1. Push backend to Git repository
2. In Nebius Console → Serverless Endpoints
3. Create new endpoint:
   - Source: Your Git repo / backend folder
   - Runtime: Python 3.12
   - Entry: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Environment variables: Add all from `.env`
   - Min/Max instances: 1-10

### Serverless Jobs for Async Work

For long-running investigations:

```yaml
# .nebius/job-investigation.yaml
name: coska-investigation
runtime: python-3.12
entrypoint: python -m app.agent.orchestrator
env:
  - NEBIUS_API_KEY
  - TAVILY_API_KEY
resources:
  cpu: 2
  memory: 4Gi
timeout: 600
```

Trigger via API:
```bash
curl -X POST https://serverless.nebius.com/v1/jobs/coska-investigation/runs \
  -H "Authorization: Bearer $NEBIUS_API_KEY" \
  -d '{"incident_id": "INC-XXX", "auto_approve": true}'
```

## Kubernetes Deployment (Advanced)

### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: coska
```

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coska-config
  namespace: coska
data:
  NEBIUS_BASE_URL: "https://api.tokenfactory.us-central1.nebius.com/v1/"
  NEBIUS_MODEL: "nvidia/nemotron-3-ultra-550b-a55b"
  DATABASE_URL: "sqlite:///./data/coska.db"
  APP_ENV: "production"
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: coska-secrets
  namespace: coska
type: Opaque
stringData:
  NEBIUS_API_KEY: "your_key_here"
  TAVILY_API_KEY: "your_key_here"
```

### Backend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coska-backend
  namespace: coska
spec:
  replicas: 2
  selector:
    matchLabels:
      app: coska-backend
  template:
    metadata:
      labels:
        app: coska-backend
    spec:
      containers:
      - name: backend
        image: your-registry/coska-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: coska-config
        - secretRef:
            name: coska-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: coska-data-pvc
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: coska-backend
  namespace: coska
spec:
  selector:
    app: coska-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Ingress (with TLS)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: coska-ingress
  namespace: coska
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  tls:
  - hosts:
    - coska.your-domain.com
    secretName: coska-tls
  rules:
  - host: coska.your-domain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: coska-backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: coska-frontend
            port:
              number: 80
```

## SSL/TLS Configuration

### Let's Encrypt with cert-manager
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### Self-Signed (Development)
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=coska.local"
```

## Monitoring & Observability

### Health Endpoints
- `GET /api/health` - Basic liveness
- `GET /api/health/ai` - AI provider connectivity

### Structured Logging
All logs in JSON format:
```json
{
  "timestamp": "2026-10-29T...",
  "level": "info",
  "logger": "orchestrator",
  "incident_id": "INC-XXX",
  "step": "VERIFYING",
  "duration_ms": 1234
}
```

### Recommended Stack
- **Logs**: Loki + Grafana
- **Metrics**: Prometheus + Grafana
- **Traces**: Jaeger (add OpenTelemetry to FastAPI)
- **Alerts**: Alertmanager → PagerDuty/Slack

## Backup & Recovery

### Database Backup
```bash
# SQLite backup (run on running container)
docker exec coska-backend sqlite3 /app/data/coska.db ".backup /app/data/coska-backup.db"

# Or copy volume
docker run --rm -v coska-data:/data -v $(pwd):/backup alpine \
  cp /data/coska.db /backup/coska-$(date +%Y%m%d).db
```

### Restore
```bash
docker run --rm -v coska-data:/data -v $(pwd):/backup alpine \
  cp /backup/coska-20261029.db /data/coska.db
```

## Scaling Considerations

### Horizontal Scaling
- Backend: Stateless, can run multiple replicas
- Frontend: Static files, CDN recommended
- Database: SQLite → PostgreSQL for multi-instance

### Database Migration (SQLite → PostgreSQL)
```bash
# Update DATABASE_URL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/coska

# Run migrations
alembic upgrade head
```

### AI Provider Limits
- Nebius Token Factory: Check quota limits
- Implement request queuing for high volume
- Cache common investigation patterns

## CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy COSKA
on:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build backend
        run: docker build -t coska-backend ./backend
      - name: Run tests
        run: docker run coska-backend pytest
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag coska-backend ${{ secrets.REGISTRY }}/coska-backend:${{ github.sha }}
          docker push ${{ secrets.REGISTRY }}/coska-backend:${{ github.sha }}

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build frontend
        run: |
          cd frontend
          npm ci
          npm run build
      - name: Deploy to CDN
        run: ... # Your CDN deploy step
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend fails to start | Check `.env` exists and has valid keys |
| AI health check fails | Verify Nebius API key and quota |
| Frontend shows CORS error | Check `VITE_API_URL` matches backend |
| Sandbox tests fail | Ensure Docker daemon accessible |
| Database locked | Single SQLite writer; use PostgreSQL for HA |
| High memory usage | Reduce sandbox memory limit |
| Slow investigations | Check Nebius latency, consider caching |

## Rollback Procedure

```bash
# Docker Compose
docker-compose down
docker-compose up -d --build  # Previous image tag

# Kubernetes
kubectl rollout undo deployment/coska-backend -n coska
```