#!/usr/bin/env bash
set -euo pipefail
alembic upgrade head
echo "Migrations applied."
