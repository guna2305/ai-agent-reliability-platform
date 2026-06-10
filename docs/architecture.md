# AI Agent Evaluation & Reliability Platform — Architecture

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                      │
│  React SPA (Vite)  │  Python SDK  │  REST API  │  Webhook Consumers │
└─────────┬─────────────────┬──────────────┬──────────────────────────┘
          │                 │              │
          ▼                 ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY  (Nginx / Kong)                      │
│               Rate Limiting  │  TLS Termination  │  Auth Proxy       │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
          ┌───────────┼───────────────────────┐
          ▼           ▼                       ▼
┌──────────────┐ ┌──────────────┐  ┌──────────────────────────────┐
│  FastAPI     │ │  Celery      │  │  OpenTelemetry Collector      │
│  (Backend)   │ │  Workers     │  │  → Prometheus → Grafana       │
│  :8000       │ │  (3 queues)  │  │  → Jaeger (traces)            │
└──────┬───────┘ └──────┬───────┘  └──────────────────────────────┘
       │                │
       ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                       │
│                                                                      │
│  ┌─────────────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  PostgreSQL 16       │  │  Redis 7     │  │  Object Storage   │  │
│  │  + pgvector          │  │  (cache +    │  │  Azure Blob /     │  │
│  │  (primary data)      │  │   broker)    │  │  S3 compatible    │  │
│  └─────────────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Service Boundaries

### Backend API (FastAPI)
- **Responsibility**: HTTP request handling, auth, business logic orchestration
- **Scales**: Horizontally behind load balancer
- **Owns**: All sync request/response operations
- **Does NOT own**: Long-running evaluation jobs, embedding computation

### Celery Workers (3 queues)
| Queue | Priority | Responsibilities |
|-------|----------|-----------------|
| `critical` | Highest | Agent execution callbacks, real-time status updates |
| `evaluations` | Medium | LLM-judge evaluations, RAGAS scoring, DeepEval runs |
| `analytics` | Low | Failure clustering, embedding generation, cost aggregation |

### PostgreSQL + pgvector
- **Primary database** for all relational data
- **pgvector** extension stores 1536-dim embeddings for failure clustering
- **HNSW index** on failure_reports.embedding_vector for fast similarity search
- **Read replica** recommended for analytics queries in production

### Redis
- **Message broker** for Celery task queue
- **Cache layer**: JWT blacklist, agent metadata, evaluation results
- **Rate limiting**: Sliding window counters per org/user

## 3. Domain Model (DDD Aggregates)

```
Organization (Aggregate Root)
├── Users (members with roles)
├── Agents (registered AI agents)
│   └── AgentVersions (immutable snapshots)
├── Datasets (evaluation datasets)
│   └── DatasetItems (test cases)
└── Experiments (A/B tests)
    └── ExperimentVariants

Execution (Aggregate Root)
├── ExecutionTraces (span tree)
│   └── ToolCalls (per-trace tool invocations)
└── HallucinationReports

EvaluationRun (Aggregate Root)
├── EvaluationResults (per-item scores)
└── FailureReports (clustered failures)
```

## 4. Database Schema — Entity Relationship

```
organizations ──< org_members >── users
      │                              │
      ├──< agents                    ├──< api_keys
      │       └──< agent_versions    │
      │                              └──< audit_logs
      ├──< datasets
      │       └──< dataset_items
      │
      └──< experiments
              └──< experiment_variants >── agent_versions

executions >── agents
executions >── agent_versions (nullable)
executions >── users (initiated_by, nullable)
executions ──< execution_traces (parent_trace_id self-ref)
executions ──< tool_calls
executions ──< hallucination_reports

evaluation_runs >── agents
evaluation_runs >── agent_versions (nullable)
evaluation_runs >── datasets (nullable)
evaluation_runs ──< evaluation_results
                          ├── >── executions (nullable)
                          └── >── dataset_items (nullable)

failure_reports >── executions
failure_reports >── evaluation_results (nullable)

metrics >── organizations
metrics >── agents (nullable)
```

## 5. Indexing Strategy

| Table | Index | Rationale |
|-------|-------|-----------|
| executions | (org_id, agent_id, started_at DESC) | Dashboard time-range queries |
| executions | (agent_id, status) | Status filtering per agent |
| execution_traces | (execution_id, sequence_order) | Trace reconstruction |
| evaluation_results | (eval_run_id, passed) | Pass-rate aggregation |
| failure_reports | HNSW(embedding_vector) | Vector similarity search |
| failure_reports | (org_id, failure_type, created_at) | Failure trend queries |
| metrics | (org_id, metric_name, recorded_at DESC) | Time-series analytics |
| metrics | (agent_id, metric_name, recorded_at DESC) | Per-agent metrics |
| audit_logs | (org_id, created_at DESC) | Audit trail queries |
| api_keys | (key_hash) UNIQUE | Auth key lookup |

## 6. API Design

### Versioning
All APIs are versioned under `/api/v1/`. Breaking changes introduce `/api/v2/`.

### Authentication
- **JWT Bearer tokens** for interactive users (15-min access + 7-day refresh)
- **API Keys** for programmatic access (SDK, CI integrations)
- **RBAC Roles**: `owner > admin > member > viewer`

### Key Endpoints
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

GET    /api/v1/organizations/{org_slug}/agents
POST   /api/v1/organizations/{org_slug}/agents
GET    /api/v1/organizations/{org_slug}/agents/{agent_id}/versions

POST   /api/v1/executions
GET    /api/v1/executions/{exec_id}
GET    /api/v1/executions/{exec_id}/traces

POST   /api/v1/evaluations/runs
GET    /api/v1/evaluations/runs/{run_id}/results

GET    /api/v1/analytics/{org_slug}/costs
GET    /api/v1/analytics/{org_slug}/performance

GET    /api/v1/failures/search
POST   /api/v1/failures/cluster
```

## 7. Observability Stack

```
Application → OpenTelemetry SDK → OTel Collector
                                        │
                    ┌───────────────────┼────────────────────┐
                    ▼                   ▼                    ▼
               Prometheus          Jaeger               CloudWatch
              (metrics)           (traces)               (Azure Monitor)
                    │
               Grafana
              (dashboards)
```

**Key Metrics Tracked:**
- `agent_execution_duration_ms` (histogram)
- `agent_execution_total` (counter, labeled by status)
- `eval_score_distribution` (histogram, labeled by metric)
- `token_usage_total` (counter, labeled by model/org)
- `cost_usd_total` (counter, labeled by org/agent)
- `hallucination_score_avg` (gauge, labeled by agent)

## 8. Security Architecture

```
Request Flow with Security:
─────────────────────────────
1. TLS termination at Nginx
2. Rate limiting (100 req/min per IP, 1000 req/min per org)
3. JWT / API-Key validation in FastAPI middleware
4. RBAC permission check per endpoint
5. Org-scoping: all DB queries filtered by org_id
6. Audit log written for all mutations
7. Secrets via Azure Key Vault / AWS Secrets Manager
```

## 9. Multi-Tenancy Model

- **Org-level isolation**: Every resource belongs to an org
- **Row-level queries**: All queries include `WHERE org_id = ?`
- **Future**: Row Level Security (RLS) in PostgreSQL for defense-in-depth

## 10. Development Roadmap

| Phase | Focus | ETA |
|-------|-------|-----|
| 1 | Architecture, Repository, Database | ✅ Done |
| 2 | Auth (JWT+RBAC), Agent Registry APIs | Week 2 |
| 3 | Execution Engine + Tracing | Week 3 |
| 4 | Evaluation Framework (LLM-judge, RAGAS) | Week 4-5 |
| 5 | Hallucination Detection | Week 6 |
| 6 | Failure Analytics + Clustering | Week 7 |
| 7 | React Dashboards + Trace Viewer | Week 8-9 |
| 8 | Kubernetes + Helm + GitHub Actions | Week 10 |
| 9 | Demo Dataset + Portfolio Polish | Week 11 |

## 11. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | SQLAlchemy 2.0 async | Industry standard, async-native, migration support |
| Task Queue | Celery + Redis | Proven at scale, rich ecosystem, easy to monitor |
| Vector Store | pgvector | Avoids separate vector DB for this scale; simpler ops |
| Frontend Build | Vite + React | Fastest DX, optimal bundle size |
| State Management | TanStack Query | Server-state focused; ideal for API-heavy dashboards |
| Containerization | Docker + K8s | Cloud-portable; Helm for parameterized deploys |
| Observability | OpenTelemetry | Vendor-neutral; works with Azure Monitor + Grafana |
