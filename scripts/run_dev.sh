#!/usr/bin/env bash
set -euo pipefail

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env created from .env.example"
fi

uvicorn src.presentation.main:app --host 0.0.0.0 --port 8000 --reload
