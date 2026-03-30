# Chillpickle VPS Infrastructure

## Architecture Overview

```mermaid
graph TB
    subgraph Internet
        U[Users / Clients]
        CF[Cloudflare DNS<br/>*.tcom.chillpickle.org<br/>outline.chillpickle.org]
    end

    subgraph VPS ["VPS — <VPS_IP>"]
        subgraph Traefik ["Traefik v3.3 (Docker)"]
            EP80[":80 HTTP"]
            EP443[":443 HTTPS"]
            ACME[Let's Encrypt<br/>Certs]
        end

        subgraph Outline ["Outline Stack"]
            OL[Outline<br/>:8089 → :3000]
            OLPG[(PostgreSQL)]
            OLR[(Redis)]
        end
    end

    U -->|DNS lookup| CF
    CF -->|A record| EP80
    CF -->|A record| EP443
    EP80 -->|301 redirect| EP443
    EP443 -->|outline.*| OL
    EP443 -->|traefik.tcom| Traefik

    ACME -.->|DNS-01 challenge| CF

    OL --- OLPG
    OL --- OLR
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as Cloudflare DNS
    participant T as Traefik :443
    participant S as Backend Service

    C->>CF: outline.chillpickle.org
    CF-->>C: <VPS_IP>

    C->>T: HTTPS request (SNI: outline.chillpickle.org)
    Note over T: TLS termination<br/>Let's Encrypt cert
    T->>T: Match Host() rule → route to service
    T->>S: HTTP proxy to host.docker.internal:8089
    S-->>T: Response
    T-->>C: HTTPS response
```

## Services

| Service | URL | Internal Port | Docker Compose |
|---------|-----|---------------|----------------|
| Outline | https://outline.chillpickle.org | 8089 | `services/outline/` |
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
traefik/
├── docker-compose.yml          # Traefik container definition
├── .env.enc                    # CF_DNS_API_TOKEN (sops-encrypted)
├── traefik.yml                 # Static config: entrypoints, ACME, providers
└── dynamic/
    ├── routes.yml              # Routers + services (host rules → backends)
    └── middlewares.yml         # Dashboard basic auth
```

On the server, `acme/acme.json` (Let's Encrypt cert storage, chmod 600) is generated at runtime and not tracked in the repo.

### Adding a new service

1. Add a router + service block to `traefik/dynamic/routes.yml`:
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
3. The wildcard cert already covers `*.tcom.chillpickle.org`. For other domains, add them to `traefik.yml` TLS domains list.

## TLS / Certificates

- **Certs**: Wildcard `*.tcom.chillpickle.org` + `tcom.chillpickle.org` + `outline.chillpickle.org`
- **Issuer**: Let's Encrypt (production)
- **Challenge**: DNS-01 via Cloudflare API
- **Auto-renewal**: Traefik renews ~30 days before expiry
- **Token**: Stored in `services/traefik/.env.enc` (sops-encrypted) — has IP restriction (VPS only)

## DNS (Cloudflare)

- **Zone**: `chillpickle.org` (zone ID: `58990c231e0dc7ed163b086df437b4ab`)
- **Records**:

| Type | Name | Content | Proxied |
|------|------|---------|---------|
| A | `tcom.chillpickle.org` | <VPS_IP> | No |
| A | `*.tcom.chillpickle.org` | <VPS_IP> | No |
| A | `outline.chillpickle.org` | <VPS_IP> | No |

DNS-only (grey cloud) — Traefik handles TLS termination, not Cloudflare.

## Firewall (UFW)

| Port | Service |
|------|---------|
| 22 | SSH |
| 80 | Traefik HTTP (redirects to 443) |
| 443 | Traefik HTTPS |
| 40831 | aaPanel admin |

Direct service ports (8089) are closed. All traffic goes through Traefik.

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
        ON[outline_default]
    end

    T[traefik] --- TN
    OLS[outline + postgres + redis] --- ON

    T -.->|host.docker.internal| OLS
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
cd ~/outline && docker compose restart

# Check resources
free -h && docker stats --no-stream

# Manual deploy from local machine
./scripts/deploy.sh traefik
./scripts/deploy.sh outline
```
