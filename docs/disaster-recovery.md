# Disaster Recovery

## Recovery Point Objective (RPO)

| Data | Backup method | RPO |
|---|---|---|
| PDS SQLite DB | Litestream → MinIO (1s WAL streaming) | ~1 second |
| Blob storage | MinIO native replication + Restic | ~1 hour |
| Config | Git (this repo) + Ansible Vault | Point-in-time |
| VM state | Proxmox snapshots | Daily |

## Restore: SQLite from Litestream

If the PDS SQLite DB is corrupted or lost:

```bash
# Stop PDS
docker compose stop pds

# Restore latest snapshot from MinIO
litestream restore \
  -config /etc/litestream/litestream.yml \
  /pds/pds.sqlite

# Verify
litestream databases -config /etc/litestream/litestream.yml

# Restart PDS
docker compose start pds
```

To restore to a specific point in time:
```bash
litestream restore \
  -config /etc/litestream/litestream.yml \
  -timestamp "2025-01-15T10:00:00Z" \
  /pds/pds.sqlite
```

## Restore: Full Node from Scratch

If you lose the entire VM:

1. Provision a new Ubuntu 24.04 VM on Proxmox
2. Connect it to Tailscale
3. Update `ansible/inventory/hosts.yml` with the new IP
4. Run `provision-node.yml` playbook
5. Restore SQLite from Litestream (above)
6. Verify health endpoint responds

Total expected recovery time: **~20 minutes** (mostly Ansible + image pull time).

## Restore: From Proxmox Snapshot

If you need to roll back the entire VM state:

```
Proxmox UI → VM → Snapshots → [select snapshot] → Rollback
```

or via CLI:
```bash
qm rollback <vmid> <snapname>
```

## Blob Recovery

If MinIO data is lost:
```bash
# Restic restore from B2 or local backup
restic -r b2:your-bucket:/pds-blobs restore latest --target /mnt/nas/minio
```

## Key Rotation Recovery

If you need to rotate the PLC rotation key (e.g., suspected compromise):

1. Go air-gapped
2. Use Ledger + Vanadium to generate a new key pair
3. Sign a PLC rotation operation with the new key
4. Broadcast from a networked machine
5. Update `pds.env` with the new key via Ansible

**Reference:** https://github.com/bluesky-social/did-method-plc

## Contacts & Runbook Checklist

- [ ] PDS `_health` endpoint responding: `curl https://your-community.example.com/xrpc/_health`
- [ ] Litestream is replicating: `systemctl status litestream`
- [ ] MinIO accessible via Tailscale: `mc ls local/pds-blobs`
- [ ] Cloudflare Tunnel connected: check Cloudflare Zero Trust dashboard
- [ ] Prometheus scraping: Grafana → Explore → node metrics
