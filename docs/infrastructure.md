# Chillpickle VPS Infrastructure

## Architecture Overview

```mermaid
graph TB
    subgraph Internet
        U[Users / Clients]
        CF[Cloudflare DNS<br/>*.tcom.chillpickle.org]
    end

    subgraph VPS ["VPS — 222.255.238.144"]
        subgraph Traefik ["Traefik v3.3 (Docker)"]
            EP80[":80 HTTP"]
            EP443[":443 HTTPS"]
            ACME[Let's Encrypt<br/>Wildcard Cert]
        end

        subgraph Docmost ["Docmost Stack"]
            DM[Docmost<br/>:8088 → :3000]
            DMPG[(PostgreSQL)]
            DMR[(Redis)]
        end
    end

    U -->|DNS lookup| CF
    CF -->|A record| EP80
    CF -->|A record| EP443
    EP80 -->|301 redirect| EP443
    EP443 -->|docmost.tcom| DM
    EP443 -->|traefik.tcom| Traefik

    ACME -.->|DNS-01 challenge| CF

    DM --- DMPG
    DM --- DMR
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as Cloudflare DNS
    participant T as Traefik :443
    participant S as Backend Service

    C->>CF: docmost.tcom.chillpickle.org
    CF-->>C: 222.255.238.144

    C->>T: HTTPS request (SNI: docmost.tcom.*)
    Note over T: TLS termination<br/>Wildcard cert *.tcom.chillpickle.org
    T->>T: Match Host() rule → route to service
    T->>S: HTTP proxy to host.docker.internal:8088
    S-->>T: Response
    T-->>C: HTTPS response
```

## Services

| Service | URL | Internal Port | Docker Compose |
|---------|-----|---------------|----------------|
| Docmost | https://docmost.tcom.chillpickle.org | 8088 | `services/docmost/` |
| Traefik Dashboard | https://traefik.tcom.chillpickle.org | -- | `services/traefik/` |

## Traefik Configuration

File-based config (no Docker labels, no Docker socket mount).

```mermaid
graph LR
    subgraph Static ["traefik.yml (static)"]
        EP[entryPoints<br/>:80, :443]
        CR[certificatesResolvers<br/>letsencrypt / DNS-01]
        FP[providers.file<br/>watch: true]
    end

    subgraph Dynamic ["dynamic/ (hot-reload)"]
        R[routes.yml<br/>routers + services]
        M[middlewares.yml<br/>dashboard basicAuth]
    end

    FP -->|watches| Dynamic
    EP --> R
    CR --> R
```

### Key files (in repo)

```
services/traefik/
├── docker-compose.yml          # Traefik container definition
├── .env.enc                    # CF_DNS_API_TOKEN (sops-encrypted)
├── traefik.yml                 # Static config: entrypoints, ACME, providers
└── dynamic/
    ├── routes.yml              # Routers + services (host rules → backends)
    └── middlewares.yml         # Dashboard basic auth
```

On the server, `acme/acme.json` (Let's Encrypt cert storage, chmod 600) is generated at runtime and not tracked in the repo.

### Adding a new service

1. Add a router + service block to `services/traefik/dynamic/routes.yml`:
   ```yaml
   http:
     routers:
       myapp:
         rule: "Host(`myapp.tcom.chillpickle.org`)"
         entryPoints: [websecure]
         service: myapp
     services:
       myapp:
         loadBalancer:
           servers:
             - url: "http://host.docker.internal:PORT"
   ```
2. Traefik picks it up automatically (file watcher). No restart needed.
3. The wildcard cert already covers `*.tcom.chillpickle.org`.

## TLS / Certificates

- **Cert**: Wildcard for `*.tcom.chillpickle.org` + `tcom.chillpickle.org`
- **Issuer**: Let's Encrypt (production)
- **Challenge**: DNS-01 via Cloudflare API
- **Auto-renewal**: Traefik renews ~30 days before expiry
- **Token**: Stored in `services/traefik/.env.enc` (sops-encrypted) — has IP restriction (VPS only)

## DNS (Cloudflare)

- **Zone**: `chillpickle.org` (zone ID: `58990c231e0dc7ed163b086df437b4ab`)
- **Records**:

| Type | Name | Content | Proxied |
|------|------|---------|---------|
| A | `tcom.chillpickle.org` | 222.255.238.144 | No |
| A | `*.tcom.chillpickle.org` | 222.255.238.144 | No |

DNS-only (grey cloud) — Traefik handles TLS termination, not Cloudflare.

## Firewall (UFW)

| Port | Service |
|------|---------|
| 22 | SSH |
| 80 | Traefik HTTP (redirects to 443) |
| 443 | Traefik HTTPS |
| 40831 | aaPanel admin |

Direct service ports (8088) are closed. All traffic goes through Traefik.

## Server Resources

- **RAM**: 3.8 GB + 4 GB swap (swappiness=10)
- **CPU**: 2 vCPUs
- **Disk**: 38 GB (aaPanel nginx stopped, not removed)
- **OS**: Ubuntu (Debian-based)

## Docker Stacks

```mermaid
graph LR
    subgraph Networks
        TN[traefik_default]
        DN[docmost_default]
    end

    T[traefik] --- TN
    DMS[docmost + postgres + redis] --- DN

    T -.->|host.docker.internal| DMS
```

Each stack has its own isolated Docker network. Traefik reaches services through `host.docker.internal` (mapped to the host's network via `extra_hosts`), not by joining their networks.

## Maintenance

```bash
# SSH access
ssh chillpickle-chill

# View all containers
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Traefik logs
cd ~/traefik && docker compose logs -f traefik

# Restart a stack
cd ~/traefik && docker compose restart
cd ~/docmost && docker compose restart

# Check resources
free -h && docker stats --no-stream

# Manual deploy from local machine
./scripts/deploy.sh traefik
./scripts/deploy.sh docmost
```
