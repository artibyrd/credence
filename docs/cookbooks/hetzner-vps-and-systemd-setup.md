---
title: 'Cookbook: Sovereign Node on Hetzner VPS with Systemd'
description: Recipe for hosting a sovereign, cost-efficient Credence node on a $4/mo Hetzner Linux VPS using systemd and SQLite WAL.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Cookbook: Sovereign Node on Hetzner VPS with Systemd

Host a fast, reliable Credence node on a dedicated Linux VPS (Hetzner, DigitalOcean, Linode) for $4/mo.

---

## 1. Systemd Service Definition

Create `/etc/systemd/system/credence.service`:

```ini
[Unit]
Description=Credence Sovereign Epistemic Node
After=network.target

[Service]
Type=simple
User=credence
WorkingDirectory=/opt/credence
ExecStart=/opt/credence/.venv/bin/credence serve --transport sse --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=ENV=production
Environment=CREDENCE_PROFILE=economy
Environment=DATABASE_URL=sqlite+aiosqlite:///opt/credence/data/credence.db

[Install]
WantedBy=multi-user.target
```

---

## 2. Enable and Launch

```bash
systemctl daemon-reload
systemctl enable --now credence
```
