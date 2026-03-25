# Architecture

## Overview

This is a hybrid edge-to-premise AT Protocol deployment. The goal is community-scale self-hosting with data sovereignty, without needing to manage public IP addresses or open firewall ports.

## Traffic Flow

```
User (Bluesky app / browser)
  │
  │  HTTPS / WebSocket
  ▼
Cloudflare (edge)
  ├─ CDN cache for media blobs
  ├─ DDoS protection
  └─ SSL termination → Cloudflare Tunnel (outbound-only, no inbound ports)
          │
          │  Tunnel (encrypted, Cloudflare-brokered)
          ▼
    Cloudflared daemon (running on your host)
          │
          ▼
    Nginx Proxy Manager / Caddy (local reverse proxy + internal TLS)
          │
          ├──▶ PDS (Personal Data Server) — handles AT Proto repos, auth
          └──▶ PDS Gatekeeper — 2FA proxy sitting in front of PDS login
```

**Private / admin traffic** flows only over Tailscale:
- SSH access to nodes
- DB sync between replicas
- MinIO blob access (Litestream + blob uploads)
- Prometheus scraping, Grafana dashboards

## Key Design Decisions

### Why Cloudflare Tunnels?
Eliminates the need to open any inbound firewall ports. The cloudflared daemon inside your network initiates an outbound connection to Cloudflare's edge. Simplifies ISP/home network constraints significantly.

### Why Tailscale?
Zero-configuration WireGuard mesh. Every node gets a stable `*.tailnet.ts.net` hostname. Removes need for internal DNS. ACLs can be configured to restrict which nodes talk to which.

### Why Proxmox?
Snapshot and rollback capability is essential when running community infrastructure. Proxmox gives you VM-level snapshots you can restore in minutes if an update goes wrong.

### Why Litestream over pg_dump backups?
PDS uses SQLite. Litestream streams WAL frames in real-time (1s interval) to MinIO — giving you a continuous backup rather than hourly snapshots. Recovery point objective is effectively sub-minute.

### Why a Ledger for the rotation key?
`PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX` is the master identity key for your PDS. If it's stolen, someone can take over every account's DID. Signing offline with a hardware wallet eliminates the attack surface entirely.

## Component Relationships

```
┌──────────────────────────────────────────────────────────┐
│ Proxmox Host                                             │
│                                                          │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐   │
│  │ Ubuntu VM   │   │ Ubuntu VM   │   │ Ubuntu VM    │   │
│  │ (PDS node)  │   │ (Monitoring)│   │ (NAS/MinIO)  │   │
│  │             │   │             │   │              │   │
│  │ PDS         │   │ Prometheus  │   │ MinIO        │   │
│  │ cloudflared │   │ Grafana     │   │              │   │
│  │ Gatekeeper  │   │ Node Exp.   │   │              │   │
│  │ Litestream──┼───┼─────────────┼──▶│ Buckets:     │   │
│  │             │   │             │   │  pds-blobs   │   │
│  └─────────────┘   └─────────────┘   │  pds-backups │   │
│                                      └──────────────┘   │
└──────────────────────────────────────────────────────────┘
         │                   │
         └──── Tailscale ────┘ (management plane)
         │
         ▼
   Cloudflare Tunnel ──▶ Internet
```

## Federation

Users on other home networks can run their own lightweight PDS nodes:

1. Ubuntu 24.04 LTS + Docker (any hardware — even a Pi 4 works for <10 users)
2. Run the `provision-node.yml` playbook (same Ansible, different inventory)
3. Set `PDS_SERVICE_HANDLE_DOMAINS` to their subdomain
4. Point their Cloudflare Tunnel at the community's domain
5. Blobs go to the community MinIO via Tailscale — no S3 costs for home nodes

This gives sovereignty at the personal level while sharing the storage/CDN infrastructure of the community.
