# AI Agent Evaluation & Reliability Platform

A platform I'm building to evaluate, monitor, debug, and improve AI agents running in production. Think of it as a self-hosted combination of LangSmith + Datadog, designed specifically for agentic AI systems, with everything running locally using free and open-source tools.

---

## Visitor guide: how the project works

This project helps developers inspect AI agent behavior: what ran, how long it took, which steps failed, and how outputs scored against evaluation criteria.

**Explore:** [Local setup](#running-it-locally) · [API walkthrough](docs/usage.md) · [Architecture](docs/architecture.md) · [Example evaluation data](docs/demo-dataset/support_qa.json)

**Viewing the application:** Follow the local setup below to open the React dashboard and interactive API documentation. No public hosted demo URL is provided here. The localhost links work after you start the stack on your own computer.

### The workflow

1. **Register an agent** in an organization and manage its versions.
2. **Record executions** with inputs, outputs, status, latency, token usage, and cost metadata.
3. **Inspect traces and tool calls** to understand the steps behind an execution.
4. **Evaluate outputs** using datasets and the available ground-truth, LLM-judge, or RAG evaluation paths.
5. **Investigate reliability** through hallucination reports, failure classification, clustering, and semantic failure search.
6. **Review the dashboard** to explore execution trends, evaluations, costs, and failures.

The React frontend communicates with FastAPI. PostgreSQL stores application records and vector data; Redis and Celery support background work; Ollama supplies local model inference for the configured AI workflows. Your application must submit execution and trace records through the API: starting this platform does not automatically instrument an external agent.

### Suggested first tour

After seeding the demo data, sign in with the local demo account and select **Demo Organization**. Visit **Dashboard → Agents → Executions → Trace Viewer → Evaluations → Analytics → Failures**. Then follow the [usage guide](docs/usage.md) to record your own execution and submit evaluation data.

The seed script creates **four agents and forty executions**, together with example traces, evaluation results, hallucination reports, and failures. These are synthetic demonstration records, including randomized scores and outcomes; they are not a benchmark or evidence of real agent quality.

### Working notes

- Run migrations before seeding or using the API.
- Download models into the **Docker Ollama service** used by the backend, as shown below.
- Local Ollama usage does not require a paid model API key, but it still uses your machine's memory, storage, and compute.
- Evaluation and detection scores are signals for investigation, not guarantees of correctness.
- The demo login is for local exploration. Configure your own credentials and deployment settings before sharing a hosted instance.
- These documentation steps were checked against repository source and configuration; a fresh end-to-end stack run has not been performed for this update.

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
- **Python 3.11+** + **FastAPI** — async API framework
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
| 4 | Evaluation framework (LLM-judge, ground-truth, RAG metrics, Celery pipeline) | ✅ Done |
| 5 | Hallucination detection (reference / retrieval / LLM-judge, signal fusion) | ✅ Done |
| 6 | Failure analytics — rule-based classifier + k-means embedding clustering | ✅ Done |
| 7 | React dashboard wired to live API (auth, org switcher, TanStack Query) | ✅ Done |
| 8 | Helm chart — full K8s stack (Postgres/Redis/Ollama/API/workers/frontend) | ✅ Done |
| 9 | Demo seed data, usage guide, golden dataset | ✅ Done |

All nine planned phases are complete. See the **[Usage Guide](docs/usage.md)** for an
end-to-end walkthrough and `python -m scripts.seed_demo` to populate a demo org.
Ongoing ideas live in the issues; this is an actively-tinkered personal project.

---

## Running It Locally

### Prerequisites

- Git
- Docker with Docker Compose available and running
- Internet access for container images and initial model downloads

The Docker route provides Python, Node.js, and Ollama inside containers.

### Quick Start

```bash
git clone https://github.com/guna2305/ai-agent-reliability-platform.git
cd ai-agent-reliability-platform
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` for the copy step. Review the environment settings, then run:

```bash
# Start supporting services
docker compose up -d db redis ollama

# Pull models into the Ollama container used by the backend
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull nomic-embed-text

# Apply the database schema; continue only if this exits successfully
docker compose --profile migration run --rm migrate

# Build and start the application
docker compose up -d --build api worker-evaluations worker-analytics frontend

# Populate the local demo using the API container's dependencies and DB settings
docker compose exec api python -m scripts.seed_demo
```

Open **http://localhost:5173** and sign in with `demo@example.com` / `demodemo123`. Interactive API documentation is at **http://localhost:8000/docs** with the default port configuration.

Check service status with `docker compose ps`. For startup errors, inspect `docker compose logs api frontend worker-evaluations`. If Ollama is still starting, wait for it to be ready and retry the model pull. A host Ollama process using port 11434 can conflict with the container port.

Stop the local stack with `docker compose down`; named database and model volumes are retained.

Full walkthrough (curl examples for every endpoint): **[docs/usage.md](docs/usage.md)**.

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

# Datasets (golden / benchmark / regression test sets)
POST   /organizations/{slug}/datasets                Create dataset
GET    /organizations/{slug}/datasets                List datasets
POST   /organizations/{slug}/datasets/{id}/items     Bulk-add test cases
GET    /organizations/{slug}/datasets/{id}/items     List test cases

# Evaluations (LLM-judge / ground-truth / RAG — all via Ollama)
POST   /organizations/{slug}/evaluations/runs                Launch eval (dispatched to Celery)
GET    /organizations/{slug}/evaluations/runs                List eval runs
GET    /organizations/{slug}/evaluations/runs/{id}           Run status + aggregate scores
GET    /organizations/{slug}/evaluations/runs/{id}/results   Per-item scores

# Hallucination detection (reference / retrieval-consistency / LLM-judge, fused)
POST   /organizations/{slug}/executions/{id}/hallucination-check  Detect + store report
GET    /organizations/{slug}/executions/{id}/hallucinations       Reports for an execution
GET    /organizations/{slug}/hallucinations?min_score=0.7         Org-wide flagged reports
POST   /organizations/{slug}/hallucinations/{id}/confirm          Mark human-confirmed (admin+)

# Failure analytics (rule-based classification + k-means embedding clusters)
GET    /organizations/{slug}/failures                  List (type/cluster/resolved filters)
GET    /organizations/{slug}/failures/breakdown        Count per failure type
GET    /organizations/{slug}/failures/clusters         Per-cluster size + dominant type
POST   /organizations/{slug}/failures/cluster          Embed (Ollama) + re-cluster (admin+)
GET    /organizations/{slug}/failures/search?q=        Semantic similarity search
POST   /organizations/{slug}/failures/{id}/resolve     Mark resolved with notes
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

