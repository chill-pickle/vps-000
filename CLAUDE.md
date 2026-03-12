# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an ops/infrastructure reference repo for the **chillpickle** VPS. There is no application code — tasks here involve remote server administration via SSH.

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

- **IP**: (see `~/.ssh/config`)
- **Hostname**: chillpickles
- **OS**: Linux (Debian/Ubuntu — uses `ssh` service, not `sshd`)
- **SSH Port**: 22
- **Password login**: Disabled (key-only)

### SSH Config Aliases (`~/.ssh/config`)

| Alias | User | Usage |
|---|---|---|
| `chillpickle` | root | Admin access |
| `chillpickle-chill` | chill | Daily use (recommended) |

### User: chill

- Member of `root` group
- Passwordless sudo (`/etc/sudoers.d/chill`)
- SSH key auth configured
