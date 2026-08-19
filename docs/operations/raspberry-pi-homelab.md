---
title: Raspberry Pi & HomeLab 24/7 Node Runbook
description: Deploying a low-power ARM64 Credence mesh node with systemd, automated
  SQLite maintenance, and dynamic DNS.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Raspberry Pi & HomeLab 24/7 Node Runbook

Running a persistent Credence node on a **Raspberry Pi 5 (8GB)** or low-power mini-PC contributes seed capacity to the Credence Mesh, seeds syndicated news attestations to peers, and provides a local 0-token caching proxy for home and office AI agents.

---

## 1. Hardware Requirements

- **Device**: Raspberry Pi 5 (4GB or 8GB RAM recommended) or any ARM64 / x86-64 mini-PC.
- **Storage**: High-endurance microSD (A2 rated) or NVMe SSD HAT (recommended for high SQLite write endurance).
- **Power**: 5V/5A USB-C power supply with UPS backup.
- **OS**: Ubuntu Server 24.04 LTS (64-bit) or Debian 12 (Bookworm).

---

## 2. Installation on ARM64

```bash
# 1. Update system packages
sudo apt update && sudo apt install -y python3-pip python3-venv git curl

# 2. Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 3. Clone and install Credence
git clone https://github.com/artibyrd/credence.git /opt/credence
cd /opt/credence
poetry install --only main
```

---

## 3. Configuring `systemd` Daemon (`credence-node.service`)

Create a systemd unit file at `/etc/systemd/system/credence-node.service`:

```ini
[Unit]
Description=Credence P2P Mesh & FastMCP Node
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/credence
ExecStart=/home/pi/.local/bin/poetry run credence mesh start --port 8765 --node-name "homelab-pi5-alpha"
Restart=always
RestartSec=10
LimitNOFILE=65536
Environment=CREDENCE_GEMINI_API_KEY=your-gemini-key
Environment=CREDENCE_PROFILE=BALANCED

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now credence-node
sudo systemctl status credence-node
```

---

## 4. Monitoring & Dynamic DNS

If hosting a public seed peer behind a residential ISP:
1. **Port Forwarding**: Forward TCP port `8765` from your router to your Raspberry Pi local IP.
2. **Dynamic DNS (DuckDNS / Cloudflare DDNS)**: Keep `pi-node.yourdomain.com` pointed to your residential IPv4/IPv6.
3. **Check Logs**:
   ```bash
   journalctl -u credence-node -f -n 50
   ```

---

## 5. Linux Administration & Hardware References

### 📚 Official Hardware & System Documentation
* **Raspberry Pi**: [Raspberry Pi 5 Hardware Specs & NVMe HAT Documentation](https://www.raspberrypi.com/documentation/)
* **Operating Systems**: [Ubuntu Server 24.04 LTS for ARM64](https://ubuntu.com/download/raspberry-pi) &bull; [Debian Bookworm on ARM](https://www.debian.org/ports/arm/)
* **Service Management**: [systemd Service Units & Resource Control](https://systemd.io/)
* **DNS & Dynamic IP**: [Cloudflare Dynamic DNS (DDNS) API Automation](https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-patch-dns-record)

### 🔗 Related Homelab Guides in Credence
* 🗄️ [Database Pruning & SQLite WAL Maintenance](database-pruning-wal.md)
* 🔒 [Tailscale & WireGuard Overlay Peering](tailscale-wireguard-mesh.md)
* 🔔 [Tutorial 13: Discord Alerting & Basement Monitoring](../tutorials/13-discord-alerting-and-basement-monitoring.md)
* 💡 [Blog: Testing 13-Node Swarms on a $35 Raspberry Pi](../../blog/testing-13-node-swarms-on-a-raspberry-pi.md)
* 🚀 [Tutorial 11: Autonomous Node Germination & Ignition](../tutorials/11-autonomous-node-germination-and-swarm-ignition.md)

