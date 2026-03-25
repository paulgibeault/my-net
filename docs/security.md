# Security Model

## Threat Model

| Threat | Mitigation |
|---|---|
| Public internet exposure | Cloudflare Tunnels — zero inbound ports |
| SSH brute force | UFW allows SSH on Tailscale interface only |
| Stolen hardware (HD theft) | LUKS + TPM 2.0 measured boot |
| Rotation key compromise | Ledger hardware wallet — key never touches network |
| Account takeover via login | PDS Gatekeeper — 2FA (email or TOTP) |
| SQLite DB theft | Encrypted disk + Litestream blob encryption |
| Container escape | Non-root containers, no docker socket exposed |
| Stale software | Watchtower (PDS) + unattended-upgrades (OS) |

## Rotation Key Handling

The `PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX` is the master DID key. If compromised, an attacker can take over every DID on your PDS.

**Procedure:**
1. Install [Vanadium](https://github.com/nymtech/vanadium) app on Ledger
2. Generate key pair **fully offline** (air-gapped machine or the Ledger itself)
3. Export only the **public key** — store the private key hex in Ledger's secure enclave
4. When signing PLC operations (rare — only for initial setup or key rotation):
   - Disconnect from network
   - Use the Ledger to sign
   - Broadcast the signed operation from a different machine

The private key hex should never appear in any file, environment variable, or cloud system.

## UFW Rules

```
# Default: deny all inbound
ufw default deny incoming
ufw default allow outgoing

# Allow SSH only on Tailscale interface
ufw allow in on tailscale0 to any port 22 proto tcp

# Everything else: blocked at the kernel level
```

Cloudflare Tunnels only need **outbound** connectivity — the cloudflared daemon calls home. No `ufw allow` needed for port 443.

## Secrets Management

Secrets live in two places:
1. `pds.env` on the server (chmod 600, owned by deploy user, not in git)
2. Ansible Vault for deployment (encrypt with `ansible-vault encrypt_string`)

**Never store in git:**
- `*.env` files
- Private keys (`.key`, `.pem`)
- MinIO credentials
- JWT secrets

## TLS

- **Public edge:** Cloudflare manages certificates automatically
- **Internal:** Nginx Proxy Manager or Caddy generates Let's Encrypt certs for the local reverse proxy
- **Tailscale:** WireGuard encryption end-to-end for all management traffic

## Incident Response

If you suspect a key compromise:
1. Take the PDS offline immediately (`docker compose stop pds`)
2. Use `goat` CLI to rotate the PLC rotation key from an offline machine
3. Rekey MinIO credentials
4. Review Grafana logs for anomalous access patterns
5. Notify users if account data may be affected
