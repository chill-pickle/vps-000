# vps-000

Monorepo for the **chillpickle** VPS — infrastructure, services, and CI/CD in one place.

## Services

| Service | URL | Stack |
|---------|-----|-------|
| [ChilLang](chillang/) | `api.chillang.chillpickle.org` | FastAPI + SQLite + OpenAI, Chrome extension (Svelte 5) |
| [Outline](outline/) | `outline.chillpickle.org` | Outline wiki + PostgreSQL + Redis |
| [Dashy](dashy/) | `dash.chillpickle.org` | Self-hosted dashboard for services & links |
| [Story API](story/) | `story.chillpickle.org` | FastAPI + SQLite story tracker |
| [Traefik](traefik/) | `traefik.tcom.chillpickle.org` | Reverse proxy, TLS via Let's Encrypt DNS-01 |

## Architecture

```
Internet → Cloudflare DNS → Traefik :443 (TLS termination)
                              ├─ api.chillang.chillpickle.org → ChilLang API
                              ├─ outline.chillpickle.org      → Outline wiki
                              ├─ dash.chillpickle.org         → Dashy dashboard
                              ├─ story.chillpickle.org          → Story API
                              └─ traefik.tcom.chillpickle.org  → Dashboard
```

## Deployment

All changes deploy via GitHub Actions on push to `main`. Path-based detection runs only the relevant jobs.

| Change in | What happens |
|-----------|-------------|
| `traefik/**` | Rsync config → restart Traefik |
| `outline/**` | Rsync config → pull + restart Outline |
| `dashy/**` | Rsync config → pull + restart Dashy |
| `chillang/backend/**` | Build Docker image → push to GHCR → pull on VPS |
| `chillang/extension/**` | Build → upload artifact (manual Chrome install) |
| `story/backend/**` | Build Docker image → push to GHCR → pull on VPS |

Secrets managed with [sops](https://github.com/getsops/sops) + age encryption.

## Security

- **TruffleHog** — scans git history for leaked secrets
- **Trivy** — scans dependencies, Dockerfiles, and configs for vulnerabilities
- **GitHub native** — Secret scanning, push protection, Dependabot, CodeQL

## License

Private infrastructure. Not intended for external use.
