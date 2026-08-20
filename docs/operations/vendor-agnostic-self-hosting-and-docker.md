---
title: 'Operational Guide: Vendor-Agnostic Self-Hosting and Docker'
description: Comprehensive operational guide for running sovereign Credence nodes
  across Docker Compose, Bare-Metal Linux, VPS, Kubernetes, and non-GCP clouds.
since_version: v1.18.0
verified_version: v1.18.2
last_verified: '2026-08-19'
---

# Operational Guide: Vendor-Agnostic Self-Hosting and Docker

Credence is engineered as a **sovereign, vendor-agnostic system**. It interfaces exclusively via standard open protocols, ensuring zero vendor lock-in and complete portability across bare-metal servers, VPS providers (Hetzner, OVH, Linode, AWS EC2), and self-hosted homelabs.

---

## 1. Universal Standard Storage & State Contracts

Credence requires zero proprietary cloud services. All subsystems interact through standard open interfaces:

1. **Database Contract**: Standard async SQLAlchemy 2.0 (`DATABASE_URL`). Seamlessly supports embedded SQLite WAL, PostgreSQL 14+, Neon, AWS Aurora, or Supabase.
2. **CAS Blob Storage Contract**: Standard S3-compatible API (`S3_ENDPOINT_URL`, `S3_BUCKET_NAME`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`). Works with Cloudflare R2, MinIO, Wasabi, AWS S3, or local POSIX disk storage (`STORAGE_BACKEND=local`).
3. **Distributed State Contract**: Standard Redis RESP Protocol (`VALKEY_URL` / `REDIS_URL`). Works with Valkey 7+, Redis 7+, Dragonfly, Upstash, or in-memory Python fallback.

---

## 2. Docker Compose Deployments

### 2.1 Basic Sovereign Node ($0 Idle / Embedded SQLite)
Ideal for individual researchers, local agents, and air-gapped homelabs:

```yaml
# docker-compose.yml
services:
  credence:
    image: ghcr.io/artibyrd/credence:latest
    container_name: credence-node
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "8765:8765"
    environment:
      - ENV=production
      - CREDENCE_PROFILE=economy
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - STORAGE_BACKEND=local
      - SNAPSHOT_DIR=/app/data/snapshots
    volumes:
      - credence-data:/app/data

volumes:
  credence-data:
```

Launch with:
```bash
docker compose up -d
```

### 2.2 Planetary Sovereign Cluster (Postgres + MinIO + Valkey)
Ideal for high-throughput teams and enterprise swarms:

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## 3. Bare-Metal Linux VPS Deployment (Hetzner, OVH, Linode, AWS)

### Step 1: System Package Installation & User Creation
```bash
# Update and install Python 3.12 and build tools
sudo apt update && sudo apt install -y python3.12 python3.12-venv python3-pip git curl ufw

# Create dedicated system user
sudo useradd -r -s /bin/false -d /opt/credence -m credence
```

### Step 2: Clone Repository and Install Dependencies
```bash
sudo git clone https://github.com/artibyrd/credence.git /opt/credence
cd /opt/credence

# Create virtualenv and install with Poetry
sudo python3.12 -m venv .venv
sudo /opt/credence/.venv/bin/pip install --upgrade pip poetry
sudo /opt/credence/.venv/bin/poetry install --without dev --no-root
sudo /opt/credence/.venv/bin/poetry install --without dev
sudo chown -R credence:credence /opt/credence
```

### Step 3: Configure Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Caddy/Nginx TLS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8765/tcp  # P2P Mesh Gossip Relay
sudo ufw enable
```

### Step 4: Configure Reverse Proxy (Caddy with Automated HTTPS)
Install Caddy and create `/etc/caddy/Caddyfile`:

```caddy
credence.yourdomain.com {
    reverse_proxy 127.0.0.1:8000 {
        header_up X-Forwarded-Proto https
    }
}

relay.credence.yourdomain.com {
    reverse_proxy 127.0.0.1:8765
}
```

Restart Caddy:
```bash
sudo systemctl restart caddy
```

---

## 4. Disaster Recovery & Snapshot Portability

To back up and restore a self-hosted node:

```bash
# 1. Back up SQLite database (WAL safe backup)
sqlite3 /opt/credence/data/credence.db ".backup '/opt/credence/backups/credence-$(date +%Y%m%d).db'"

# 2. Back up snapshot CAS blobs
tar -czvf /opt/credence/backups/snapshots-$(date +%Y%m%d).tar.gz /opt/credence/data/snapshots/

# 3. Verify backup integrity
ls -lh /opt/credence/backups/
```
