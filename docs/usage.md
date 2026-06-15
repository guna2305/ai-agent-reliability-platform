# Usage Guide

An end-to-end walkthrough of the platform — from spinning it up to seeing
evaluations and clustered failures in the dashboard. Everything runs locally
on Ollama, so no API keys or spend.

## 1. Start the stack

```bash
cp .env.example .env
ollama pull llama3.2 && ollama pull nomic-embed-text   # one-time, ~2.5GB
docker compose up -d db redis ollama
docker compose --profile migration up migrate
docker compose up -d api worker-evaluations worker-analytics frontend
```

- API docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Flower (Celery): http://localhost:5555

## 2. Seed demo data (optional but recommended)

Populates a demo org so the dashboard isn't empty:

```bash
python -m scripts.seed_demo
# Login:  demo@example.com  /  demodemo123
```

Re-run with `--reset` to rebuild from scratch.

## 3. The manual flow (what the seed script automates)

### Register & get a token
```bash
curl -X POST localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"supersecret","full_name":"Me"}'
# → returns access_token + refresh_token; a personal org is auto-created
```

Grab your org slug:
```bash
TOKEN=...   # access_token from above
curl localhost:8000/api/v1/organizations -H "Authorization: Bearer $TOKEN"
```

### Register an agent
```bash
curl -X POST localhost:8000/api/v1/organizations/<slug>/agents \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Support Bot","agent_type":"customer_support","framework":"langgraph"}'
```

### Record an execution
```bash
# create
curl -X POST localhost:8000/api/v1/organizations/<slug>/executions \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"agent_id":"<agent_id>","input":{"question":"How do I reset my password?"}}'

# start → complete (records tokens + cost; Ollama = $0)
curl -X POST localhost:8000/api/v1/organizations/<slug>/executions/<id>/start -H "Authorization: Bearer $TOKEN"
curl -X POST localhost:8000/api/v1/organizations/<slug>/executions/<id>/complete \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"output":{"answer":"Use the reset link on the login page."},"input_tokens":320,"output_tokens":80}'
```

### Upload a golden dataset & run an evaluation
```bash
# create dataset
curl -X POST localhost:8000/api/v1/organizations/<slug>/datasets \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Support QA","dataset_type":"golden"}'

# add items (see docs/demo-dataset/support_qa.json for a full example)
curl -X POST localhost:8000/api/v1/organizations/<slug>/datasets/<dataset_id>/items \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d @docs/demo-dataset/support_qa.json

# launch an LLM-judge evaluation (dispatched to Celery; Ollama judges it)
curl -X POST localhost:8000/api/v1/organizations/<slug>/evaluations/runs \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"agent_id":"<agent_id>","name":"Baseline","eval_type":"llm_judge","dataset_id":"<dataset_id>"}'

# poll results
curl localhost:8000/api/v1/organizations/<slug>/evaluations/runs/<run_id> -H "Authorization: Bearer $TOKEN"
```

### Check for hallucinations
```bash
curl -X POST localhost:8000/api/v1/organizations/<slug>/executions/<id>/hallucination-check \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"question":"...","response":"...","reference":"...","context_chunks":["..."]}'
```

### Cluster & explore failures
```bash
# embed (Ollama nomic-embed-text) + k-means cluster all failures
curl -X POST localhost:8000/api/v1/organizations/<slug>/failures/cluster -H "Authorization: Bearer $TOKEN"

# semantic search over failures
curl "localhost:8000/api/v1/organizations/<slug>/failures/search?q=timeout" -H "Authorization: Bearer $TOKEN"
```

## 4. Explore in the UI

Open the frontend, sign in, and the sidebar org switcher selects your org.
Pages: **Dashboard** (stats + trends), **Agents**, **Executions** → click a
row for the **Trace Viewer**, **Evaluations**, **Analytics** (cost/latency),
and **Failures** (cluster cards + "Re-cluster" button).

## 5. Deploy to Minikube

See [`infrastructure/helm/ai-agent-platform/README.md`](../infrastructure/helm/ai-agent-platform/README.md)
or just run `./scripts/deploy-minikube.sh dev`.
