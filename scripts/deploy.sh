#!/bin/bash

# Script de déploiement pour MADAVOLA
# Usage: ./scripts/deploy.sh [dev|prod]

set -e

ENV=${1:-prod}
COMPOSE_FILE="infra/docker/compose.prod.yml"

if [ "$ENV" = "dev" ]; then
  COMPOSE_FILE="infra/docker/compose.yml"
fi

echo "🚀 Déploiement en mode: $ENV"
echo "📁 Fichier compose: $COMPOSE_FILE"

# Vérifier que le fichier .env existe
if [ ! -f .env ]; then
  echo "❌ Fichier .env non trouvé. Copiez env.example vers .env et configurez-le."
  exit 1
fi

# Construire et démarrer les services
echo "🔨 Construction des images..."
docker compose -f $COMPOSE_FILE build

echo "🚀 Démarrage des services..."
docker compose -f $COMPOSE_FILE up -d

echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérifier la santé des services
echo "🏥 Vérification de la santé des services..."
docker compose -f $COMPOSE_FILE ps

echo "✅ Déploiement terminé!"
echo ""
echo "📊 Services disponibles:"
echo "  - API: http://localhost:8000"
echo "  - Web: http://localhost:${WEB_PORT:-80}"
echo "  - Nginx: http://localhost:${NGINX_PORT:-8080}"
