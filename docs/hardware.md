# Hardware Guide

## Recommended Builds

### Ultra-Low-Power Node (always-on, < 6W)
**Intel N100 Mini PC**
- CPU: Intel Alder Lake-N100, 4C/4T, fanless, 6W TDP
- RAM: 16GB DDR5
- Storage: 512GB NVMe SSD (high-endurance)
- Use case: Light PDS nodes, under 50 users
- Cost: ~$150-200 USD

Great for home community members who want to self-host. Silent, no maintenance.

### Mid-Range Node (multi-tenant, virtualization)
**AMD Ryzen 5 5500 or Ryzen 7 5800XT Mini PC**
- CPU: Ryzen 5 5500 (6C/12T, 65W) or Ryzen 7 5800XT (8C/16T)
- RAM: 32-64GB DDR4
- Storage: 1TB NVMe (OS + containers) + expansion slot
- Use case: Proxmox host, running 2-4 PDS VMs
- Cost: ~$300-500 USD

### NAS (blob storage)
**Synology or TrueNAS-compatible build**
- Storage: 4-8TB HDD for blob storage + 500GB NVMe for MinIO metadata
- Network: 2.5GbE preferred
- Use case: MinIO S3-compatible blob storage, Restic backup target
- Notes: MinIO runs well in Docker on any Linux NAS

## Proxmox Setup

```
Proxmox VE (bare metal)
  ├── Ubuntu Server 24.04 VM — PDS primary (4 vCPU, 8GB RAM, 100GB disk)
  ├── Ubuntu Server 24.04 VM — Monitoring (2 vCPU, 4GB RAM, 50GB disk)
  └── (optional) Ubuntu Server VM — PDS replica
```

**Proxmox storage recommendations:**
- OS disk → NVMe (fast boot, snapshots)
- VM disks → NVMe if possible (SQLite performance matters)
- Blob data → can go to HDD via NAS mount

## Tailscale on Proxmox Nodes

Install Tailscale on the Proxmox host itself for management access:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --advertise-routes=192.168.1.0/24   # expose LAN to Tailscale mesh if needed
```

Also install inside each Ubuntu VM — each node gets its own Tailscale IP.

## TPM 2.0 + LUKS Setup

Most modern mini PCs have TPM 2.0. Enable in BIOS/UEFI:

```bash
# Check TPM availability
ls /dev/tpm*

# Enable LUKS with TPM 2.0 unlock (Ubuntu 24.04)
apt install clevis-tpm2 clevis-luks
clevis luks bind -d /dev/nvme0n1p3 tpm2 '{"pcr_bank":"sha256","pcr_ids":"0,7"}'
```

PCR 0 = firmware, PCR 7 = Secure Boot state. If hardware is tampered with, TPM unsealing fails.

## Networking

```
Router (home/office)
  │
  ├── Mini PC (Proxmox/PDS)  ──── Tailscale (WireGuard)
  ├── NAS (MinIO)             ──── Tailscale
  └── Other nodes             ──── Tailscale

No ports need to be forwarded.
Cloudflare Tunnel: outbound-only from cloudflared daemon.
```
