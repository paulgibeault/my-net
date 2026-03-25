# AT Protocol Community Infrastructure

Self-hosted, multi-tenant [AT Protocol](https://atproto.com/) network. Hybrid edge-to-premise model: Cloudflare handles the public edge, your own hardware handles data sovereignty.

---

## Architecture at a Glance

```
Public Internet
      │
      ▼
 Cloudflare Tunnel (port 443, CDN, DDoS)
      │
      ▼
 Nginx Proxy Manager / Caddy (local TLS termination)
      │
      ├──▶ PDS (Personal Data Server) ──▶ SQLite (Litestream → MinIO backup)
      ├──▶ PDS Gatekeeper (2FA proxy)
      └──▶ MinIO (blob storage, S3-compatible)

Private Mesh (Tailscale / WireGuard)
  ├── Management access (SSH, DB sync)
  ├── Grafana / Prometheus monitoring
  └── Federated PDS nodes (home networks)
```

**Hardware:** Mini PCs (N100 or Ryzen 5/7) + NAS  
**Hypervisor:** Proxmox VE → Ubuntu Server 24.04 LTS VMs  
**Automation:** Ansible playbooks (no config drift)  
**Key security:** Ledger hardware wallet for PLC rotation key  

---

## Repository Structure

```
atproto-infra/
├── ansible/                  # Automation playbooks
│   ├── inventory/            # Host definitions
│   ├── playbooks/            # Provisioning playbooks
│   ├── roles/                # Reusable roles
│   └── group_vars/           # Shared variables
├── compose/                  # Docker Compose stacks
│   ├── pds/                  # PDS + gatekeeper
│   ├── monitoring/           # Prometheus + Grafana
│   └── storage/              # MinIO
├── config/                   # Config templates (no secrets)
│   ├── nginx/
│   ├── caddy/
│   └── litestream/
├── docs/                     # Architecture docs, runbooks
│   ├── architecture.md
│   ├── onboarding.md
│   ├── hardware.md
│   ├── disaster-recovery.md
│   └── security.md
├── scripts/                  # Utility scripts
└── REQUIREMENTS.md           # Full requirements spec
```

---

## Quick Start

> See [docs/onboarding.md](docs/onboarding.md) for the full setup guide.

```bash
# 1. Clone this repo onto your management machine
git clone <this-repo> atproto-infra
cd atproto-infra

# 2. Copy and fill in your inventory
cp ansible/inventory/hosts.example.yml ansible/inventory/hosts.yml
# edit hosts.yml with your node IPs / Tailscale hostnames

# 3. Bootstrap a new PDS node
ansible-playbook ansible/playbooks/provision-node.yml -i ansible/inventory/hosts.yml

# 4. Verify PDS health
curl https://your-pds-domain.com/xrpc/_health
```

---

## Security Model

- **Public edge:** Cloudflare Tunnels — no local ports exposed
- **Private mesh:** Tailscale — WireGuard-based, zero-trust
- **Rotation key:** Never touches network — signed offline via Ledger hardware wallet
- **Disk encryption:** LUKS + TPM 2.0 measured boot
- **2FA:** PDS Gatekeeper sidecar (email or TOTP)
- **Backups:** Litestream → MinIO (SQLite), Restic/BorgBackup (blobs)

---

## Status

| Component | Status |
|---|---|
| Requirements | ✅ Complete |
| Ansible skeleton | ✅ Scaffolded |
| Compose stacks | ✅ Scaffolded |
| Litestream config | ✅ Templated |
| Docs | 🔄 In progress |
| GitHub repo | ⏳ Awaiting link from Paul |

---

*Built by Geebs 🤙 — [AT Protocol](https://atproto.com/) | [Bluesky PDS](https://github.com/bluesky-social/pds)*
