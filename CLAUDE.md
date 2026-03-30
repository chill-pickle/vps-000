# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Infrastructure-as-code repo for the **chillpickle** VPS. Service configs, secrets (sops/age-encrypted), and CI/CD live here. See `docs/infrastructure.md` for architecture docs with Mermaid diagrams.

## Repo Structure

```
chillpickle/
├── CLAUDE.md
├── .gitignore
├── .sops.yaml
├── services/
│   ├── traefik/
│   │   ├── docker-compose.yml
│   │   ├── .env.enc
│   │   ├── traefik.yml
│   │   └── dynamic/
│   │       ├── routes.yml
│   │       └── middlewares.yml
│   └── outline/
│       ├── docker-compose.yml
│       └── .env.enc
├── scripts/
│   └── deploy.sh
├── docs/
│   ├── infrastructure.md
│   └── outline.md
└── .github/
    └── workflows/
        └── deploy.yml
```

## Deployment

- **All changes must be deployed via CI/CD** — commit to git, push to `main`, GitHub Actions handles the rest. Never SSH to make manual changes.
- **CI/CD**: GitHub Actions (`.github/workflows/deploy.yml`) — auto-deploys on push to `main` when `services/` changes.
- **Secrets**: Encrypted with sops/age (`.env.enc` files). Decrypted at deploy time.
- **GitHub Secrets needed**: `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SOPS_AGE_KEY`
- `./scripts/deploy.sh <traefik|outline>` is for local testing/emergency only

## Common Operations

```bash
# Run a command on the server
ssh chillpickle-chill "command here"

# Interactive session (preferred)
ssh chillpickle-chill

# Root access when needed
ssh chillpickle
```

## Server Access

- **IP**: 222.255.238.144
- **Hostname**: chillpickles
- **OS**: Ubuntu (Debian-based)
- **SSH Port**: 22
- **Password login**: Disabled (key-only)
- **Resources**: 3.8 GB RAM + 4 GB swap, 2 vCPUs, 38 GB disk

### SSH Config Aliases (`~/.ssh/config`)

| Alias | User | Usage |
|---|---|---|
| `chillpickle` | root | Admin access |
| `chillpickle-chill` | chill | Daily use (recommended) |

### User: chill

- Member of `root` group
- Passwordless sudo (`/etc/sudoers.d/chill`)
- SSH key auth configured

## Current Stack

### Reverse Proxy — Traefik v3.3

- **Config**: `services/traefik/` (file-based, no Docker labels/socket)
- **Ports**: 80 (-> 301 HTTPS), 443
- **TLS**: Wildcard cert `*.tcom.chillpickle.org` + `outline.chillpickle.org` via Let's Encrypt DNS-01 + Cloudflare
- **Cloudflare token**: stored in `services/traefik/.env.enc` (sops-encrypted, IP-restricted to VPS)
- **Dashboard**: https://traefik.tcom.chillpickle.org (basic auth: `admin` / `chillpickle2026`)
- Adding new service: edit `services/traefik/dynamic/routes.yml`, Traefik hot-reloads

### Services

| Service | URL | Compose Dir | Internal Port |
|---------|-----|-------------|---------------|
| Outline | https://outline.chillpickle.org | `services/outline/` | 8089 |

### DNS (Cloudflare)

- **Zone**: `chillpickle.org` (ID: `58990c231e0dc7ed163b086df437b4ab`)
- **Records**: `tcom.chillpickle.org` + `*.tcom.chillpickle.org` + `outline.chillpickle.org` → 222.255.238.144 (DNS-only)
- **API token**: IP-restricted to VPS — must run Cloudflare API calls via SSH, not locally

### Firewall (UFW)

Open ports: 22 (SSH), 80/443 (Traefik), 40831 (aaPanel admin). Direct service ports (8089) are closed.

### aaPanel

- Installed but nginx **stopped and disabled** (Traefik replaced it)
- Panel still accessible at port 40831 for server monitoring
