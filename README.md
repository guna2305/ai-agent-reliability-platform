# AI Agent Evaluation & Reliability Platform

A platform I'm building to evaluate, monitor, debug, and improve AI agents running in production. Think of it as a self-hosted combination of LangSmith + Datadog, designed specifically for agentic AI systems, with everything running locally using free and open-source tools.

---

## Why I'm Building This

When you deploy AI agents, you quickly run into questions that are hard to answer:

- Why did the agent fail on that specific input?
- Which prompt changes improved quality?
- How much did last week's agent runs actually cost?
- Which tool calls are causing the most failures?
- Is this new model version actually better than the old one?

I couldn't find a single tool that answered all of these well (especially for free), so I'm building one.

---

## What It Does

| Feature | Description |
|---------|-------------|
| **Agent Registry** | Register agents with versioning. Promote a version to production. Compare versions side by side. |
| **Execution Engine** | Track every agent run end-to-end — input, output, latency, token usage, cost. |
| **Distributed Tracing** | Record a full span tree: planner decisions → retrieval → LLM calls → tool calls → final output. |
| **Evaluation Framework** | Run LLM-as-judge, ground-truth, and RAG evaluations against golden datasets. |
| **Hallucination Detection** | Reference-based + retrieval consistency + LLM judge scoring. |
| **Failure Analysis** | Auto-cluster failures using embeddings. Find related failures across agents. |
| **Cost Analytics** | Track token usage and cost per execution, per agent, per day. Ollama runs are always free. |
| **Experiment Tracking** | A/B test prompt changes and model swaps. See which one wins. |
| **Dashboard** | Success rates, latency trends, eval scores, hallucination trends, cost breakdowns. |

---

## Tech Stack

### Backend
- **Python 3.12** + **FastAPI** — async API framework
- **PostgreSQL 16** + **pgvector** — main database + vector similarity search for failure clustering
- **SQLAlchemy 2.0** async — ORM with typed mapped columns
- **Alembic** — database migrations
- **Redis 7** — JWT blacklist, rate limiting, Celery broker
- **Celery** — async task queue for evaluation jobs and embedding generation

### AI Layer
- **Ollama** — default local LLM provider (free, no API keys)
  - Default model: `llama3.2`
  - Embedding model: `nomic-embed-text`
- **OpenAI** — optional, only used if `OPENAI_API_KEY` is set
- **Anthropic** — optional, only used if `ANTHROPIC_API_KEY` is set

### Frontend
- **React 18** + **TypeScript** — component-based UI
- **Vite** — build tooling
- **Tailwind CSS** — utility-first styling
- **TanStack Query** — server state management
- **Recharts** — analytics charts

### Infrastructure
- **Docker** + **Docker Compose** — local dev stack
- **Kubernetes** + **Minikube** — local cluster deployment
- **Prometheus** + **Grafana** — metrics and dashboards
- **OpenTelemetry** — distributed tracing (optional, configure via `OTEL_ENABLED=true`)

### Architecture
Clean Architecture with four layers:
```
domain/          ← pure Python entities, value objects, business logic
application/     ← use cases, repository interfaces, DTOs
infrastructure/  ← DB models, Postgres repos, Redis, Celery, AI providers
presentation/    ← FastAPI routers, Pydantic schemas, DI wiring
```

---

## Project Status

| Phase | What | Status |
|-------|------|--------|
| 1 | Architecture, database schema (20 tables), React scaffold, Docker, CI/CD | ✅ Done |
| 2 | Auth (JWT + RBAC), org management, agent registry v2, API keys | ✅ Done |
| 3 | Execution engine, span tracing, cost calculator, analytics, Minikube K8s | ✅ Done |
| 4 | Evaluation framework (LLM-judge + RAGAS + DeepEval) | 🔨 Next |
| 5 | Hallucination detection | Planned |
| 6 | Failure clustering with embeddings | Planned |
| 7 | React dashboard with live charts | Planned |
| 8 | Full K8s deployment with Helm | Planned |
| 9 | Demo dataset + documentation | Planned |

---

## Running It Locally

### Prerequisites
- Docker + Docker Compose
- [Ollama](https://ollama.ai) installed locally
- Python 3.12+

### Quick Start
```bash
# 1. Clone and configure
git clone https://github.com/guna2305/ai-agent-reliability-platform
cd ai-agent-reliability-platform
cp .env.example .env

# 2. Pull the default LLM (free, ~2GB)
ollama pull llama3.2
ollama pull nomic-embed-text   # for embeddings

# 3. Start the full stack
docker compose up -d db redis
docker compose --profile migration up migrate
docker compose up api frontend

# 4. Open the UI
# Frontend:  http://localhost:5173
# API docs:  http://localhost:8000/docs
# Flower:    http://localhost:5555  (Celery task monitor)
```

### With GPU (faster inference)
Uncomment the `deploy.resources` block in `docker-compose.yml` for the Ollama service if you have an NVIDIA GPU and `nvidia-container-toolkit` installed.

### Minikube (local Kubernetes)
```bash
# Install minikube: https://minikube.sigs.k8s.io
minikube start --memory=6g --cpus=4

# Enable ingress
minikube addons enable ingress

# Build and load images into minikube
eval $(minikube docker-env)
docker build -f docker/Dockerfile --target production -t agent-platform-api:latest .
docker build -f frontend/Dockerfile --target production -t agent-platform-frontend:latest frontend/

# Deploy
kubectl apply -f infrastructure/kubernetes/base/namespace.yaml
kubectl apply -f infrastructure/kubernetes/base/

# Create secrets (replace placeholders)
kubectl create secret generic agent-platform-secrets \
  --namespace=agent-platform \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgres-service:5432/agent_reliability" \
  --from-literal=DATABASE_URL_SYNC="postgresql://postgres:postgres@postgres-service:5432/agent_reliability" \
  --from-literal=REDIS_URL="redis://redis-service:6379/0" \
  --from-literal=CELERY_BROKER_URL="redis://redis-service:6379/1" \
  --from-literal=CELERY_RESULT_BACKEND="redis://redis-service:6379/2"

# Access the app
echo "$(minikube ip) agent-platform.local" | sudo tee -a /etc/hosts
# Open: http://agent-platform.local
```

---

## API Overview

All endpoints under `/api/v1`. Interactive docs at `/docs`.

```
# Auth
POST   /auth/register          Create account (auto-creates personal org)
POST   /auth/login             Get JWT access + refresh tokens
POST   /auth/refresh           Refresh access token
POST   /auth/logout            Revoke tokens
GET    /auth/me                Current user info

# Organizations & members
POST   /organizations                     Create org
GET    /organizations                     List my orgs
GET    /organizations/{slug}              Get org
POST   /organizations/{slug}/members     Invite member (admin+)

# Agent registry (org-scoped, versioned)
POST   /organizations/{slug}/agents                          Register agent
GET    /organizations/{slug}/agents                          List agents
PATCH  /organizations/{slug}/agents/{id}                     Update agent
POST   /organizations/{slug}/agents/{id}/versions            Create version
POST   /organizations/{slug}/agents/{id}/versions/{v}/promote  Promote to production

# Execution engine
POST   /organizations/{slug}/executions              Start execution
GET    /organizations/{slug}/executions              List executions
POST   /organizations/{slug}/executions/{id}/start      Mark running
POST   /organizations/{slug}/executions/{id}/complete   Record output + cost
POST   /organizations/{slug}/executions/{id}/fail       Record failure

# Tracing
POST   /organizations/{slug}/executions/{id}/spans            Open span
POST   /organizations/{slug}/executions/{id}/spans/{sid}/complete
GET    /organizations/{slug}/executions/{id}/traces           Full span tree
POST   /organizations/{slug}/executions/{id}/tool-calls       Record tool call
GET    /organizations/{slug}/executions/{id}/tool-calls

# Analytics
GET    /organizations/{slug}/analytics/executions    Stats + success rate
GET    /organizations/{slug}/analytics/costs         Cost by model + daily
GET    /organizations/{slug}/analytics/models        Supported models + pricing
```

---

## No API Keys Required

Ollama runs everything locally — zero cost, zero API keys. You can swap in OpenAI or Anthropic later by setting their keys in `.env`, but it's completely optional.

| Provider | Cost | Key Required |
|----------|------|-------------|
| Ollama   | Free | No |
| OpenAI   | Pay-per-token | Yes (optional) |
| Anthropic | Pay-per-token | Yes (optional) |

---

## Testing

```bash
pip install -e ".[dev]"
pytest tests/unit/ -v        # 62 unit tests, no DB required
pytest tests/integration/ -v  # requires running DB + Redis
```

---

## Repository Structure

```
├── src/
│   ├── domain/          # Entities, value objects, domain logic
│   ├── application/     # Use cases, repository interfaces
│   ├── infrastructure/  # DB, Redis, Celery, AI providers
│   └── presentation/    # FastAPI routes, schemas
├── frontend/            # React + TypeScript SPA
├── alembic/             # Database migrations
├── tests/               # Unit + integration tests
├── infrastructure/
│   ├── kubernetes/      # Minikube manifests
│   ├── monitoring/      # Prometheus + Grafana configs
│   └── docker/          # DB init scripts
├── docs/
│   └── architecture.md  # System design, ER diagram, decisions
└── docker-compose.yml
```
