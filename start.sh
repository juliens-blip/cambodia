#!/bin/sh
# Script de démarrage pour Railway
# Utilise le port de Railway ou 8000 par défaut

PORT="${PORT:-8000}"
echo "Starting uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
