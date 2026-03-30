#!/usr/bin/env bash
set -euo pipefail

SERVICE=${1:?Usage: ./scripts/deploy.sh <traefik|outline|chillang>}
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

case "$SERVICE" in
  traefik)
    echo "Decrypting traefik/.env.enc..."
    sops -d --input-type dotenv --output-type dotenv "${REPO_DIR}/traefik/.env.enc" > "${REPO_DIR}/traefik/.env"

    echo "Syncing traefik to server..."
    rsync -avz --exclude='acme/' --exclude='.env.enc' \
      "${REPO_DIR}/traefik/" "chillpickle-chill:~/traefik/"

    rm "${REPO_DIR}/traefik/.env"

    echo "Restarting traefik..."
    ssh chillpickle-chill "cd ~/traefik && docker compose up -d --force-recreate"
    ;;

  outline)
    echo "Decrypting outline/.env.enc..."
    sops -d --input-type dotenv --output-type dotenv "${REPO_DIR}/outline/.env.enc" > "${REPO_DIR}/outline/.env"

    echo "Syncing outline to server..."
    rsync -avz --exclude='data/' --exclude='.env.enc' \
      "${REPO_DIR}/outline/" "chillpickle-chill:~/outline/"

    rm "${REPO_DIR}/outline/.env"

    echo "Restarting outline..."
    ssh chillpickle-chill "cd ~/outline && docker compose pull && docker compose up -d"
    ;;

  chillang)
    echo "Decrypting chillang/.env.enc..."
    sops -d --input-type dotenv --output-type dotenv "${REPO_DIR}/chillang/.env.enc" > "${REPO_DIR}/chillang/.env"

    echo "Syncing chillang compose + env to server..."
    rsync -avz \
      "${REPO_DIR}/chillang/docker-compose.yml" \
      "${REPO_DIR}/chillang/.env" \
      "chillpickle-chill:~/chillang/"

    rm "${REPO_DIR}/chillang/.env"

    echo "Pulling and restarting chillang..."
    ssh chillpickle-chill "cd ~/chillang && docker compose pull && docker compose up -d"
    ;;

  *)
    echo "Unknown service: $SERVICE" >&2
    echo "Usage: ./scripts/deploy.sh <traefik|outline|chillang>" >&2
    exit 1
    ;;
esac

echo "Done."
