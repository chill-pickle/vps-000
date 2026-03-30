# Outline

Wiki and knowledge base at **https://outline.chillpickle.org**.

## Stack

| Component | Image | Port |
|-----------|-------|------|
| Outline | `outlinewiki/outline:latest` | 8089:3000 |
| PostgreSQL | `postgres:18.3` | internal |
| Redis | `redis:8.6.1` | internal |

- **Auth**: Google OAuth
- **Storage**: Local file storage (Docker volume `outline_data`)
- **TLS**: Let's Encrypt via Traefik DNS-01 + Cloudflare

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) > APIs & Services > Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Authorized redirect URI: `https://outline.chillpickle.org/auth/google.callback`
4. Copy Client ID and Client Secret into `services/outline/.env.enc` (via sops)

## DNS

A record: `outline.chillpickle.org` -> `222.255.238.144` (Cloudflare, DNS-only)

## MCP Integration

Outline has an official MCP server for use with Claude and other AI tools:

```bash
# Install the Outline MCP server
npx @anthropic-ai/mcp-outline

# Required env vars
OUTLINE_API_URL=https://outline.chillpickle.org/api
OUTLINE_API_KEY=<generate from Outline Settings > API>
```

## Maintenance

```bash
# Check status
ssh chillpickle-chill "cd ~/outline && docker compose ps"

# View logs
ssh chillpickle-chill "cd ~/outline && docker compose logs -f outline"

# Manual restart
ssh chillpickle-chill "cd ~/outline && docker compose restart"

# Update
ssh chillpickle-chill "cd ~/outline && docker compose pull && docker compose up -d"
```
