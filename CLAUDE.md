# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Monorepo for the **chillpickle** VPS (<VPS_IP>). All services, infrastructure configs, secrets (sops/age), and CI/CD in one repo.

## Rules

- **All changes deployed via CI/CD.** Commit to git, push to `main`, GitHub Actions handles deployment. Never SSH to make manual changes.
- **Secrets in `.env.enc` only.** Never commit plain `.env` files. Use `sops` to edit encrypted files.
- `scripts/deploy.sh` is for emergency/testing only.

## Architecture

```
Internet → Cloudflare DNS → Traefik v3.3 (:443, TLS termination)
                              ├─ api.chillang.chillpickle.org → host:8091 (ChilLang API)
                              ├─ outline.chillpickle.org      → host:8089 (Outline wiki)
                              └─ traefik.tcom.chillpickle.org  → dashboard
```

Traefik uses **file-based routing** (no Docker socket). Services reached via `host.docker.internal`. Each Docker stack runs in its own network.

## Repo Structure

```
traefik/          → rsync to ~/traefik/ (reverse proxy config)
outline/          → rsync to ~/outline/ (wiki docker-compose + env)
chillang/
  ├── docker-compose.yml   → rsync to ~/chillang/ (production, uses GHCR image)
  ├── .env.enc             → decrypted + rsync to ~/chillang/.env
  ├── backend/             → CI builds Docker image (NOT deployed to server)
  └── extension/           → CI builds artifact (manual Chrome install)
```

## ChilLang Backend

**Deployment**: CI builds Docker image → pushes to `ghcr.io/chill-pickle/chillang-api` → pulls on VPS. No source code on the server.

**Local development**:
```bash
cd chillang/backend
uv sync
uv run uvicorn app.main:app --reload    # http://localhost:8000
```

**API**: POST `/api/v1/words`, GET `/api/v1/words/{id}/answers`, POST `/api/v1/words/{id}/answers/{id}/vote`, GET `/health`

## ChilLang Extension

```bash
cd chillang/extension
npm install
npm run build    # two-pass: main (ES) + content script (IIFE)
npm run dev      # watch mode
# Load extension/dist/ as unpacked in chrome://extensions
```

**Build quirk**: Vite runs twice — first for service-worker + wordbank (ES modules), then `BUILD_TARGET=content` for content.js as IIFE (Chrome content scripts can't use ES imports).

## Secrets Management

```bash
# Edit an encrypted env file
sops traefik/.env.enc
sops outline/.env.enc
sops chillang/.env.enc

# Decrypt to stdout (for debugging)
sops -d --input-type dotenv --output-type dotenv chillang/.env.enc
```

All `.env.enc` files encrypted with age key `age1xf2gpz8tssl6jthpa4z3j9703qnd9phl5xzk4lm6wzfng7fe532qxq2v6f`.

## CI/CD (GitHub Actions)

Single workflow (`.github/workflows/deploy.yml`) with path-based detection:

| Change in | Job | What happens |
|-----------|-----|-------------|
| `traefik/**` | deploy-traefik | sops decrypt → rsync → docker compose up → verify → rollback |
| `outline/**` | deploy-outline | sops decrypt → rsync → docker compose pull+up → verify → rollback |
| `chillang/backend/**` | deploy-chillang-backend | Docker build+push to GHCR → rsync compose+env → pull+up → health check → rollback |
| `chillang/extension/**` | build-chillang-extension | npm build → upload artifact (no deploy) |

Manual trigger: `workflow_dispatch` with service selector.

**GitHub Secrets**: `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SOPS_AGE_KEY`

## Adding a New Service

1. Create `<service>/docker-compose.yml` + `.env.enc`
2. Add router+service to `traefik/dynamic/routes.yml` (hot-reloaded, no restart)
3. Add deploy job to `.github/workflows/deploy.yml`
4. Wildcard cert covers `*.tcom.chillpickle.org`; other domains need entry in `traefik/traefik.yml`

## Server Access

```bash
ssh chillpickle-chill    # daily use (user: chill, passwordless sudo)
ssh chillpickle          # root access
```

VPS: Ubuntu, 3.8 GB RAM + 4 GB swap, 2 vCPUs, 38 GB disk. UFW open: 22, 80, 443, 40831 (aaPanel).
