# Hybrid Multi-Tenant AT Protocol Infrastructure
**Project:** AT Protocol / Bluesky self-hosted community infra
**Status:** Requirements captured — awaiting GitHub repo link
**Last updated:** 2026-03-25

---

## Overview

End-to-end architecture, deployment strategy, and operational documentation for a scalable, hybrid AT Protocol network. Hybrid edge-to-premise model: cloud edge for public feeds, on-premise for data sovereignty and storage. Supports a multi-tenant community.

---

## Phase 1: System Architecture & Hardware Design

### 1. Hardware Foundation

- **Compute Nodes (Mini PCs):**
  - Intel Alder Lake-N100 — fanless, 6W TDP, dedicated ultra-low-power node
  - AMD Ryzen 5 5500 (6C, 65W) or Ryzen 7 5800XT — multi-core virtualization for larger communities
  - RAM: 16GB–64GB DDR5 to handle container overhead

- **Storage (NAS):**
  - High-endurance NVMe SSDs for databases
  - High-capacity HDDs for media
  - Local Network Attached Storage device

- **Hypervisor:**
  - Proxmox VE on bare metal
  - Manages Ubuntu Server VMs
  - Features: snapshots, clustering, enterprise-grade VM management

### 2. Network Topology — The Hybrid Edge

| Layer | Tool | Purpose |
|---|---|---|
| Public Edge | **Cloudflare Tunnels** | Handles port 443 public traffic; CDN caching, SSL termination, DDoS protection. No local firewall ports opened. |
| Private Mesh | **Tailscale** | WireGuard-based management plane. DB sync, NAS access, SSH — exclusively over Tailscale. |

---

## Phase 2: Core Software Stack & Multi-Tenancy

**Base OS:** Ubuntu Server 24.04 LTS
**Container Runtime:** Docker + Docker Compose (isolated containers)

### 1. AT Protocol Stack

- **PDS (Personal Data Server):**
  - `bluesky-social/pds` — official Node.js reference implementation
  - Handles repositories and authentication

- **Admin Tools:**
  - `goat` CLI — built directly into the official PDS container
  - Replaces legacy scripts for account and invite management

### 2. Multi-Tenancy — Federated PDS Architecture

- Users can spin up their own lightweight Ubuntu/Docker PDS nodes on home networks
- Federation enables seamless cross-node communication
- Each node sets its own custom domain via `PDS_SERVICE_HANDLE_DOMAINS` (e.g., `.community.com`)
- Heavy media blobs → self-hosted S3-compatible gateway (**MinIO**) on central or personal NAS

---

## Phase 3: Deployment & Automation Strategy

### Infrastructure-as-Code (Ansible)

All deployment is automated via Ansible playbooks (eliminates manual config drift, maximizes compatibility).

**Playbooks must:**
- Provision Ubuntu Server VM
- Configure **UFW** — block all inbound except Tailscale interface
- Install Docker
- Deploy **Nginx Proxy Manager** or **Caddy** for local reverse proxying + internal SSL termination
- Template and deploy `compose.yaml` and `pds.env` for the PDS

---

## Phase 3 (cont.): Continuous Delivery

- **Watchtower** — monitors GitHub Container Registry, auto-pulls latest `bluesky-social/pds` images
- Keeps all nodes patched without manual intervention

---

## Phase 4: Security & Identity Management

### 1. Cryptographic Key Protection

- **Hardware Wallets (Ledger + Vanadium app):**
  - `PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX` is the master DID key
  - Generate and sign PLC operations **fully offline** via Ledger hardware wallet
  - Never expose rotation key to networked systems

- **Hardware Root of Trust:**
  - Enable **TPM 2.0** on mini PCs
  - Pair with **Full Disk Encryption (LUKS)** — Measured Boot
  - If hardware is stolen, SQLite DBs and signing keys cannot be extracted

### 2. Access Control

- **PDS Gatekeeper** — open-source microservice
  - Hardens PDS login with **2FA via email or TOTP**
  - Deployed as a sidecar/proxy in front of PDS

---

## Phase 5: Disaster Recovery & Observability

### 1. Real-Time SQLite Replication

- **Litestream** — real-time SQLite replication (avoids corruption from hot backups)
  - `pds.env`: set `PDS_SQLITE_DISABLE_WAL_AUTO_CHECKPOINT=true`
  - Keeps WAL open so Litestream streams changes continuously → MinIO NAS

- **Blob Backups:**
  - **Restic** or **BorgBackup** — encrypted, deduplicated backups
  - Targets: local NAS and/or offsite cloud (Backblaze B2)

### 2. Monitoring & Auto-Recovery

- **Prometheus + Node Exporter** — system, CPU, container metrics
- **Grafana** — visualization + alerts (e.g., PDS container down → Telegram bot)
- **Systemd Auto-Recovery Script:**
  - Pings `/xrpc/_health` health endpoint
  - On failure: triggers `docker compose restart`, logs the event

---

## Phase 6: Documentation & Onboarding

### User Onboarding
- Guide: connecting via Bluesky mobile app → "Custom Hosting Provider" → enter PDS domain

### Migration Guides
- **PDS MOOver** — community portability suite
  - Migrate accounts (posts, followers, blocks) to/from community servers safely

### Admin Handbooks
- Document: Ansible commands, Tailscale network maps
- Hardware wallet recovery phrases → stored **offline only**, secure physical location

---

## Open Items

- [ ] GitHub repo link from Paul (to wire up the project)
- [ ] Community size / number of expected nodes
- [ ] Domain(s) for `PDS_SERVICE_HANDLE_DOMAINS`
- [ ] NAS model / existing MinIO setup?
- [ ] Cloudflare account already set up?
- [ ] Tailscale network already running?

---

## Notes

- Architecture is more config/deployment/packaging than raw coding
- Priority: Ubuntu compatibility, automation, reproducibility
- Data sovereignty is a first-class concern — blobs stay on-prem
