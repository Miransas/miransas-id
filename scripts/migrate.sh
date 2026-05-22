#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ACTION="${1:-up}"

case "$ACTION" in
  up)
    echo "Running pending migrations..."
    alembic upgrade head
    ;;
  current)
    alembic current
    ;;
  history)
    alembic history
    ;;
  down)
    echo "WARNING: Rolling back ONE migration. Are you sure? [y/N]"
    read -r confirm
    if [[ "$confirm" == "y" ]]; then
      alembic downgrade -1
    else
      echo "Aborted."
      exit 1
    fi
    ;;
  *)
    echo "Unknown action: $ACTION"
    echo "Usage: $0 [up|down|current|history]"
    exit 1
    ;;
esac
