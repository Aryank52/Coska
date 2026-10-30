# TOOLING_MAP.md - COSKA Installed Tools & Skills Map

## Overview

This document maps all installed tools, skills, and extensions in the coding environment to their relevance for COSKA development.

---

## Installed Skills (OpenCode)

| Skill | Purpose | Relevance | When to Use |
|-------|---------|-----------|-------------|
| **opencode** | OpenCode self-documentation | High | When asking about OpenCode itself, configuration, migration, plugins, SDK, CLI, TUI |
| **report** | Issue/bug reporting | Medium | When user wants to report OpenCode issue/bug |

### Skill Usage
```bash
# Load skill
skill opencode

# Or reference directly - appears as <skill_content> block
```

---

## Development Tools

### Backend (Python)

| Tool | Version | Purpose | Safe Scope |
|------|---------|---------|------------|
| **Python** | 3.12.10 | Runtime | Full |
| **uvicorn** | 0.32.0 | ASGI server | Dev/Prod |
| **FastAPI** | 0.115.0 | Web framework | Full |
| **SQLAlchemy** | 2.0.34 | Async ORM | Full |
| **Pydantic** | 2.9.2 | Validation | Full |
| **Pydantic Settings** | 2.6.1 | Config management | Full |
| **httpx** | 0.28.1 | Async HTTP client | External APIs only |
| **tenacity** | 8.5.0 | Retry logic | External calls |
| **structlog** | 24.4.0 | Structured logging | Full |
| **pytest** | 8.3.3 | Testing | Test scope |
| **pytest-asyncio** | 0.23.8 | Async testing | Test scope |
| **pytest-cov** | 5.0.0 | Coverage | Test scope |
| **docker** | 7.1.0 | Sandbox (optional) | Sandbox only |
| **passlib** | - | Argon2id hashing | Auth only |
| **python-jose** | - | JWT tokens | Auth only |

### Frontend (TypeScript/React)

| Tool | Version | Purpose | Safe Scope |
|------|---------|---------|------------|
| **Node.js** | 24.16.0 | Runtime | Dev/Build |
| **npm** | 10.x | Package manager | Dev/Build |
| **Vite** | 5.4.21 | Build tool | Dev/Build |
| **TypeScript** | 5.x | Type safety | Full |
| **React** | 18 | UI framework | Full |
| **React Router** | 6 | Routing | Full |
| **Axios** | 1.7 | HTTP client | API calls |
| **Lucide React** | 0.4 | Icons | UI only |
| **date-fns** | 3 | Date formatting | UI only |
| **ESLint** | - | Linting | Dev only |
| **Prettier** | - | Formatting | Dev only |

### Testing & Quality

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **pytest** | Backend unit/integration tests | All backend changes |
| **pytest-asyncio** | Async test support | Async backend tests |
| **npx tsc --noEmit** | TypeScript type checking | All frontend changes |
| **npm run build** | Production build verification | Pre-commit, CI |
| **python scripts/security_check.py** | Security scanning | Pre-commit, CI |
| **python scripts/healthcheck.py** | System health verification | Pre-deploy, debugging |
| **python scripts/coska_doctor.py** | Diagnostics | Troubleshooting |
| **python scripts/evaluate_coska.py** | Regression testing | Pre-release, CI |

### Scripts & Automation

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `scripts/coska.ps1` | PowerShell wrapper (all commands) | Daily operations |
| `scripts/run_demo.py` | End-to-end demo | Demo, validation |
| `scripts/evaluate_coska.py` | 24-check regression suite | Pre-release, CI |
| `scripts/healthcheck.py` | 8-system health check | Pre-deploy, monitoring |
| `scripts/coska_doctor.py` | 11-point diagnostics | Troubleshooting |
| `scripts/security_check.py` | 6-phase security audit | Pre-commit, CI |
| `scripts/seed_demo_data.py` | Demo data management | Demo setup, reset |
| `scripts/test_nebius.py` | Live Nebius integration test | Live integration only |
| `scripts/test_sandbox.py` | Sandbox verification | Sandbox changes |

### PowerShell Wrapper Commands
```powershell
.\scripts\coska.ps1 doctor      # Full diagnostics
.\scripts\coska.ps1 seed        # Seed demo data
.\scripts\coska.ps1 reset       # Reset database
.\scripts\coska.ps1 test        # Run tests
.\scripts\coska.ps1 build       # Build frontend
.\scripts\coska.ps1 backend     # Start backend
.\scripts\coska.ps1 frontend    # Start frontend dev
.\scripts\coska.ps1 dev         # Start both (dev mode)
.\scripts\coska.ps1 demo        # Run CLI demo
.\scripts\coska.ps1 judge       # Open Judge Mode
.\scripts\coska.ps1 security    # Security scan
.\scripts\coska.ps1 health      # Health check
.\scripts\coska.ps1 audit       # Dependency audit
.\scripts\coska.ps1 package     # Package for deployment
.\scripts\coska.ps1 final-check # Full validation
.\scripts\coska.ps1 stop        # Stop all services
```

---

## AI & LLM Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **MockAIProvider** | Deterministic offline AI | All development, testing, demo |
| **NebiusTokenFactoryProvider** | Live NVIDIA Nemotron via Nebius | Production AI reasoning |
| **TavilyClient** | Web research | Live external research only |

### Provider Configuration
```bash
# Development (default)
AI_PROVIDER=mock
TAVILY_ENABLED=false

# Live integration
export AI_PROVIDER=nebius
export NEBIUS_API_KEY=your_key
export NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
export NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b
export TAVILY_ENABLED=true
export TAVILY_API_KEY=your_key
```

---

## Monitoring & Observability

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **structlog** | Structured JSON logging | All backend logging |
| **Health endpoints** | `/api/health`, `/api/health/ai`, `/api/health/tavily`, `/api/health/sandbox` | Monitoring, load balancer |
| **structlog processors** | JSON output, timestamps, levels | Production logging |

---

## Security Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `scripts/security_check.py` | 6-phase security scan | Pre-commit, CI, pre-deploy |
| `pip-audit` | Python dependency vulnerabilities | Monthly, CI |
| `npm audit` | Node.js dependency vulnerabilities | Monthly, CI |
| `bandit` (optional) | Python static analysis | Pre-commit |

---

## Documentation Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **Markdown** | All documentation | All docs |
| **Mermaid** (in markdown) | Architecture diagrams | ARCHITECTURE.md, APP_FLOW.md |
| **OpenAPI/Swagger** | API docs | Auto-generated at `/docs` |

---

## Git & Version Control

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Git** | Version control | Conventional commits |
| **GitHub Actions** | CI/CD | `.github/workflows/ci.yml` |
| **GitHub** | Remote repository | Origin |

### .gitignore (Key Entries)
```gitignore
# Environment
.env
.env.local
.env.*.local

# Dependencies
node_modules/
__pycache__/
*.pyc
.pytest_cache/

# Build outputs
dist/
build/
*.egg-info/

# Database
*.db
*.db-wal
*.db-shm

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Coverage
.coverage
htmlcov/
```

---

## IDE Extensions (Recommended)

| Extension | Purpose |
|-----------|---------|
| **Python** (Microsoft) | Python language support |
| **Pylance** | Python type checking |
| **ESLint** | JavaScript/TypeScript linting |
| **Prettier** | Code formatting |
| **Tailwind CSS IntelliSense** | CSS utility classes (if used) |
| **GitLens** | Git integration |
| **REST Client** | API testing in editor |
| **SQLite Viewer** | Database inspection |

---

## Cloud/Deployment Tools (Future)

| Tool | Purpose | Status |
|------|---------|--------|
| **Docker** | Containerization | Ready (Dockerfile, docker-compose.yml) |
| **Docker Compose** | Local multi-container | Ready |
| **nginx** | Reverse proxy, SSL | Ready (nginx.conf) |
| **GitHub Actions** | CI/CD | Configured |
| **Render/Railway/Fly.io** | Backend hosting | Compatible |
| **Vercel/Netlify** | Frontend hosting | Compatible |

---

## Tool Selection Guidelines

### DO Use
- ✅ Tools that materially help: coding, testing, security, UI, deployment, documentation, AI integration
- ✅ Tools already installed in environment
- ✅ Tools with clear purpose and safe scope

### DO NOT Use
- ❌ Random tooling not vetted
- ❌ Tools that require additional installation without clear need
- ❌ Tools that could compromise security (arbitrary shell, unrestricted file access)
- ❌ Tools that duplicate existing functionality

---

## Environment Validation

### Required for Development
```bash
# Verify all tools available
python --version        # 3.12+
node --version          # 20+
npm --version           # 10+
uvicorn --version       # 0.32+
docker --version        # Optional (for Docker sandbox)
```

### Verify Setup
```bash
# Run doctor
python scripts/coska_doctor.py

# Expected: 9 PASS, 2 WARN (Docker)
```

---

## Tool Maintenance

| Task | Frequency | Owner |
|------|-----------|-------|
| `pip-audit` / `npm audit` | Monthly | Dev team |
| Dependency updates | Monthly | Dev team |
| Security scan | Pre-commit + CI | Automated |
| Documentation updates | Per feature | Feature owner |
| Tool evaluation | Quarterly | Tech lead |