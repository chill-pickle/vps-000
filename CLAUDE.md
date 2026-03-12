# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an ops/infrastructure reference repo for the **chillpickle** VPS. There is no application code — tasks here involve remote server administration via SSH. See `docs/infrastructure.md` for full architecture docs with Mermaid diagrams.

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

- **Config**: `~/traefik/` (file-based, no Docker labels/socket)
- **Ports**: 80 (→ 301 HTTPS), 443
- **TLS**: Wildcard cert `*.tcom.chillpickle.org` via Let's Encrypt DNS-01 + Cloudflare
- **Cloudflare token**: stored in `~/traefik/.env` (has IP restriction — VPS only)
- **Dashboard**: https://traefik.tcom.chillpickle.org (basic auth: `admin` / `chillpickle2026`)
- Adding new service: edit `~/traefik/dynamic/routes.yml`, Traefik hot-reloads

### Services

| Service | URL | Compose Dir | Internal Port |
|---------|-----|-------------|---------------|
| Wiki.js | https://wiki.tcom.chillpickle.org | `~/wikijs/` | 8086 |
| XWiki | https://xwiki.tcom.chillpickle.org | `~/xwiki/` | 8085 |
| AppFlowy Cloud | https://appflowy.tcom.chillpickle.org | `~/appflowy/` | 8087 |
| Docmost | https://docmost.tcom.chillpickle.org | `~/docmost/` | 8088 |

### AppFlowy Cloud — Known Issues

- **SMTP not configured**: Magic link login fails (SMTP creds are placeholder). Password login works via nginx redirect (`/login` → `action=enterPassword`). Needs a real Gmail app password or SMTP provider.
- **AI container disabled**: Requires `OPENAI_API_KEY` or `AZURE_OPENAI_API_KEY`. Stopped to avoid restart loops. Enable with `cd ~/appflowy && docker compose up -d ai`.
- **Custom nginx.conf**: `~/appflowy/nginx/nginx.conf` has a custom `/login` location block that redirects to password login flow.
- **Default admin**: `admin@example.com` / `password` — change after first login.

### DNS (Cloudflare)

- **Zone**: `chillpickle.org` (ID: `58990c231e0dc7ed163b086df437b4ab`)
- **Records**: `tcom.chillpickle.org` + `*.tcom.chillpickle.org` → 222.255.238.144 (DNS-only)
- **API token**: IP-restricted to VPS — must run Cloudflare API calls via SSH, not locally

### Firewall (UFW)

Open ports: 22 (SSH), 80/443 (Traefik), 40831 (aaPanel admin). Direct service ports (8085/8086/8087) are closed.

### aaPanel

- Installed but nginx **stopped and disabled** (Traefik replaced it)
- Panel still accessible at port 40831 for server monitoring
