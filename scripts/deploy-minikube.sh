#!/usr/bin/env bash
# Build images into Minikube's Docker daemon and deploy the platform via Helm.
#
# Prereqs: minikube, kubectl, helm, docker.
# Usage:   ./scripts/deploy-minikube.sh [dev|prod]   (default: dev)
set -euo pipefail

ENV="${1:-dev}"
RELEASE="platform"
NAMESPACE="agent-platform"
CHART="infrastructure/helm/ai-agent-platform"

echo "==> Ensuring Minikube is running"
minikube status >/dev/null 2>&1 || minikube start --memory=8g --cpus=4
minikube addons enable ingress

echo "==> Building images inside Minikube's Docker daemon"
eval "$(minikube docker-env)"
docker build -f docker/Dockerfile --target production -t agent-platform-api:latest .
docker build -f frontend/Dockerfile --target production -t agent-platform-frontend:latest frontend/

echo "==> Deploying Helm release '${RELEASE}' (${ENV})"
helm upgrade --install "${RELEASE}" "${CHART}" \
  --namespace "${NAMESPACE}" --create-namespace \
  -f "${CHART}/values-${ENV}.yaml" \
  --set-string secrets.secretKey="$(openssl rand -hex 32)" \
  --wait --timeout 10m

echo "==> Done. Pods:"
kubectl -n "${NAMESPACE}" get pods

echo ""
echo "Add the ingress host to /etc/hosts if you haven't:"
echo "  echo \"\$(minikube ip) agent-platform.local\" | sudo tee -a /etc/hosts"
echo "Then open http://agent-platform.local"
