#!/usr/bin/env bash
# Lancer l'API en local (sans Docker pour l'API).
# Prérequis : base PostgreSQL (Docker : docker compose -f infra/docker/compose.dev-db-only.yml up -d)
# Puis : cd apps/web && npm run dev (autre terminal)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="${SCRIPT_DIR}/../services/api"

if [ ! -f "${API_DIR}/.env" ]; then
  if [ -f "${API_DIR}/env.example.local" ]; then
    cp "${API_DIR}/env.example.local" "${API_DIR}/.env"
    echo "Fichier .env créé depuis env.example.local."
  else
    echo "Créez services/api/.env avec DATABASE_URL et JWT_SECRET (voir README)."
    exit 1
  fi
fi

cd "${API_DIR}"
echo "Démarrage API sur http://localhost:8000"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
