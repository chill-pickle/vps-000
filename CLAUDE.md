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
                              ├─ dash.chillpickle.org         → host:8092 (Dashy dashboard)
                              ├─ story.chillpickle.org        → host:8093 (Story API)
                              └─ traefik.tcom.chillpickle.org → dashboard (auth-protected)
```

Traefik uses **file-based routing** (no Docker socket) via `traefik/dynamic/routes.yml` (hot-reloaded, no restart needed). Services reached via `host.docker.internal`. Each Docker stack runs in its own network.

## Repo Structure

```
traefik/          → rsync to ~/traefik/ (reverse proxy config)
outline/          → rsync to ~/outline/ (wiki docker-compose + env)
dashy/            → rsync to ~/dashy/ (dashboard config + docker-compose)
chillang/
  ├── docker-compose.yml   → rsync to ~/chillang/ (production, uses GHCR image)
  ├── .env.enc             → decrypted + rsync to ~/chillang/.env
  ├── backend/             → CI builds Docker image (NOT deployed to server)
  └── extension/           → CI builds artifact (manual Chrome install)
story/
  ├── docker-compose.yml   → rsync to ~/story/ (production, uses GHCR image)
  └── backend/             → CI builds Docker image (NOT deployed to server)
```

## ChilLang Backend

**Deployment**: CI builds Docker image → pushes to `ghcr.io/chill-pickle/chillang-api` → pulls on VPS (port 8091:8000). No source code on the server.

**Local development**:
```bash
cd chillang/backend
uv sync
uv run uvicorn app.main:app --reload    # http://localhost:8000
```

**DB migrations** (SQLite via SQLAlchemy async + Alembic):
```bash
cd chillang/backend
uv run alembic upgrade head             # apply migrations
uv run alembic revision --autogenerate -m "description"  # new migration
```

**API**: POST `/api/v1/words`, GET `/api/v1/words/{id}/answers`, POST `/api/v1/words/{id}/answers/{id}/vote`, GET `/health`

**LLM providers** — Gemini is primary, OpenAI is automatic fallback (no config needed):
| Provider | Env vars | Default model |
|----------|----------|---------------|
| Gemini (primary) | `GEMINI_API_KEY`, `GEMINI_MODEL` | `gemini-2.5-flash` |
| OpenAI (fallback) | `OPENAI_API_KEY`, `OPENAI_MODEL` | `gpt-4.1-nano` |

## ChilLang Extension

Built with **Svelte 5** + Vite.

```bash
cd chillang/extension
npm install
npm run build    # two-pass: main (ES) + content script (IIFE)
npm run dev      # watch mode
# Load extension/dist/ as unpacked in chrome://extensions
```

**Build quirk**: Vite runs twice — first for service-worker + wordbank (ES modules), then `BUILD_TARGET=content` for content.js as IIFE (Chrome content scripts can't use ES imports).

## Story API

**Deployment**: CI builds Docker image → pushes to `ghcr.io/chill-pickle/story-api` → pulls on VPS (port 8093:8093). No source code on the server.

**Local development**:
```bash
cd story/backend
uv sync
uv run fastapi dev main.py    # http://localhost:8093
```

**Stack**: FastAPI + SQLModel + SQLite (WAL mode). DB auto-created at `data/todo.db` on startup — no migration tool, schema managed via `SQLModel.metadata.create_all`.

**API**: GET/POST `/stories`, PATCH/DELETE `/stories/{id}`, GET `/health`. Filterable by `status`, `priority`, `assignee`, `requested_by`.

## Dashy

Config-only service — no secrets, no build step. Edit `dashy/conf.yml` and push; CI rsyncs and restarts the container.

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

Three workflows in `.github/workflows/`:

**`deploy.yml`** — path-based, runs on push to `main`, PRs, and `workflow_dispatch`:
- **On PRs**: only validate/build jobs run (no deployment)
- **On push to main**: validate/build jobs run first, then deploy jobs (gated by `production` environment)

| Change in | Validate/Build | Deploy |
|-----------|---------------|--------|
| `traefik/**` | sops decrypt + config check | rsync → docker compose up → verify → rollback |
| `outline/**` | sops decrypt + config check | rsync → docker compose pull+up → verify → rollback |
| `dashy/**` | (none) | rsync → docker compose pull+up → verify → rollback |
| `chillang/backend/**` | Docker build+push to GHCR | rsync compose+env → pull+up → health check → rollback |
| `chillang/extension/**` | npm build → upload artifact | (no deploy) |
| `story/backend/**` | Docker build+push to GHCR | rsync compose → pull+up → health check → rollback |

**`security.yml`** — runs on push/PR to main + weekly (Mondays 06:00 UTC):
- TruffleHog: scans git history for leaked secrets
- Trivy: filesystem scan (deps, Dockerfiles, misconfigs) + Docker image scan for CVEs (CRITICAL/HIGH only)

**`notify.yml`** — triggers on Deploy or Security workflow completion; sends Telegram message.

**GitHub Secrets**: `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SOPS_AGE_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Adding a New Service

1. Create `<service>/docker-compose.yml` + `.env.enc` (if secrets needed)
2. Add router+service to `traefik/dynamic/routes.yml` (hot-reloaded, no restart needed)
3. Add deploy job to `.github/workflows/deploy.yml`
4. New domains (non-`*.chillang.chillpickle.org`) need a cert entry in `traefik/traefik.yml` under `entryPoints.websecure.http.tls.domains`

## Server Access

```bash
ssh chillpickle-chill    # daily use (user: chill, passwordless sudo)
ssh chillpickle          # root access
```

VPS: Ubuntu, 3.8 GB RAM + 4 GB swap, 2 vCPUs, 38 GB disk. UFW open: 22, 80, 443, 40831 (aaPanel).
