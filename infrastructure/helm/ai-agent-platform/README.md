# ai-agent-platform Helm chart

Deploys the full platform to Kubernetes (designed for **Minikube**):
FastAPI API, two Celery workers, React frontend, PostgreSQL (pgvector),
Redis, and Ollama — plus an Alembic migration hook and an nginx Ingress.

## Quick start (Minikube)

```bash
# One-shot helper (builds images into Minikube + helm install)
./scripts/deploy-minikube.sh dev

# …or manually:
minikube start --memory=8g --cpus=4
minikube addons enable ingress
eval $(minikube docker-env)
docker build -f docker/Dockerfile --target production -t agent-platform-api:latest .
docker build -f frontend/Dockerfile --target production -t agent-platform-frontend:latest frontend/

helm upgrade --install platform infrastructure/helm/ai-agent-platform \
  --namespace agent-platform --create-namespace \
  -f infrastructure/helm/ai-agent-platform/values-dev.yaml \
  --set-string secrets.secretKey="$(openssl rand -hex 32)"
```

## Components

| Workload | Kind | Notes |
|----------|------|-------|
| api | Deployment + Service | uvicorn, /health probes |
| worker-evaluations | Deployment | Celery `evaluations,critical` |
| worker-analytics | Deployment | Celery `analytics` |
| frontend | Deployment + Service | nginx static SPA |
| postgres | StatefulSet + headless Service | pgvector, PVC |
| redis | Deployment + Service | broker + cache |
| ollama | Deployment + Service + PVC | pulls models on start |
| db-migrate | Job (post-install/upgrade hook) | `alembic upgrade head` |
| ingress | Ingress | `/api`→api, `/`→frontend |

## Values

See `values.yaml` for the full set. Key overrides live in `values-dev.yaml`
(minimal footprint) and `values-prod.yaml` (scaled replicas, OTel on).

**Secrets:** `secrets.secretKey` and `secrets.postgresPassword` default to
dev values — always override them at install time in anything real:

```bash
helm upgrade --install platform infrastructure/helm/ai-agent-platform \
  -f .../values-prod.yaml \
  --set-string secrets.secretKey="$(openssl rand -hex 32)" \
  --set-string secrets.postgresPassword="$STRONG_PASSWORD"
```

## Notes / limitations

- **Single-node assumptions:** Postgres and Ollama use `ReadWriteOnce` PVCs
  and one replica each. Ollama uses a `Recreate` strategy so two pods never
  fight over the model volume.
- **Ollama model pull happens on pod start** via a `postStart` hook and can
  take several minutes on first deploy. The API will retry until it's ready.
- Validated in CI with `helm lint` + `helm template` (see
  `.github/workflows/cd.yml`). Not yet tested against a live cluster from CI.
