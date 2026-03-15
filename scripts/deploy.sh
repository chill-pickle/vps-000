#!/usr/bin/env bash
set -euo pipefail

SERVICE=${1:?Usage: ./scripts/deploy.sh <traefik|docmost>}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_DIR="${REPO_DIR}/services/${SERVICE}"

if [[ ! -d "$SERVICE_DIR" ]]; then
  echo "Error: service directory not found: $SERVICE_DIR" >&2
  exit 1
fi

echo "Decrypting ${SERVICE}/.env.enc..."
sops -d --input-type dotenv --output-type dotenv "${SERVICE_DIR}/.env.enc" > "${SERVICE_DIR}/.env"

echo "Syncing ${SERVICE} to server..."
rsync -avz --exclude='acme/' --exclude='data/' --exclude='.env.enc' \
  "${SERVICE_DIR}/" "chillpickle-chill:~/${SERVICE}/"

rm "${SERVICE_DIR}/.env"

echo "Restarting ${SERVICE} on server..."
ssh chillpickle-chill "cd ~/${SERVICE} && docker compose up -d"

echo "Done."
