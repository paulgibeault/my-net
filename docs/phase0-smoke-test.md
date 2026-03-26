# Phase 0 Smoke Test — Provisioning a Fresh Hostinger VPS

This runbook walks you through running the `provision-node.yml` Ansible playbook
against a fresh Ubuntu 24.04 LTS VPS. It assumes you're comfortable with SSH and
the command line, but not necessarily familiar with Ansible.

---

## Prerequisites

### On your local machine

```bash
# Python 3.10+ required
python3 --version

# Install Ansible
pip3 install --user ansible

# Verify
ansible --version   # should show 2.14+

# Install required Ansible collections
ansible-galaxy collection install community.docker
```

### What you'll need before starting

| Item | Where to get it |
|------|----------------|
| Hostinger VPS IP address | Hostinger dashboard after creating VPS |
| SSH key pair | `ssh-keygen -t ed25519` if you don't have one |
| Tailscale auth key | Tailscale admin console → Settings → Keys |
| Cloudflare Tunnel token | Zero Trust dashboard → Networks → Tunnels |
| MinIO endpoint + credentials | Your NAS MinIO admin panel |
| SMTP credentials | Your email provider (e.g. Fastmail, Mailgun) |
| PDS domain | A domain you control, pointing to Cloudflare |

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/paulgibeault/my-net.git
cd my-net/ansible
```

---

## Step 2 — Copy and fill in your inventory

```bash
cp inventory/hosts.example.yml inventory/hosts.yml
```

Edit `inventory/hosts.yml`:

```yaml
all:
  vars:
    ansible_user: root          # Hostinger default on fresh VPS
    ansible_ssh_private_key_file: ~/.ssh/id_ed25519

  children:
    pds_nodes:
      hosts:
        pds-primary:
          ansible_host: 123.456.789.0   # your VPS IP
          pds_domain: pds.yourfamily.net
```

**Note:** Hostinger VPS ships with root SSH access. The playbook will work as root.
After first run, Tailscale SSH (`--ssh` flag) lets you drop password-based access.

Test connectivity:
```bash
ansible -i inventory/hosts.yml pds_nodes -m ping
```

Expected output:
```
pds-primary | SUCCESS => { "ping": "pong" }
```

---

## Step 3 — Set up ansible-vault for secrets

```bash
# Create and encrypt your vault file
cp group_vars/vault.example.yml group_vars/vault.yml
ansible-vault encrypt group_vars/vault.yml
```

You'll be prompted to set a vault password. **Don't lose it** — there's no recovery.

Edit the vault with real values:
```bash
ansible-vault edit group_vars/vault.yml
```

Replace every `REPLACE_WITH_...` placeholder. See `vault.example.yml` for generation
instructions for each secret (e.g., the PLC rotation key needs `openssl ecparam`).

**Key generation cheatsheet:**
```bash
# JWT secret
openssl rand -hex 32

# PLC rotation key (secp256k1)
openssl ecparam -name secp256k1 -genkey -noout \
  | openssl ec -text -noout 2>/dev/null \
  | grep priv -A 3 | tail -3 | tr -d ' \n:'

# Admin password (just make it long and random)
openssl rand -base64 24
```

---

## Step 4 — Set your domain

In `group_vars/all.yml`, the `pds_domain` is left blank as a default — set it
per-host in `inventory/hosts.yml` as shown in Step 2, or set a global default:

```yaml
# group_vars/all.yml
pds_domain: pds.yourfamily.net
```

Make sure your domain has a Cloudflare DNS record and an active tunnel configured.

---

## Step 5 — Run the playbook

```bash
# Dry run first (check mode — no changes made)
ansible-playbook playbooks/provision-node.yml \
  -i inventory/hosts.yml \
  --ask-vault-pass \
  --check

# Real run
ansible-playbook playbooks/provision-node.yml \
  -i inventory/hosts.yml \
  --ask-vault-pass
```

Enter your vault password when prompted.

The playbook runs these roles in order:
1. **base** — installs packages, Tailscale, Docker, UFW
2. **litestream** — installs Litestream + systemd service for SQLite replication
3. **pds** — deploys PDS + Cloudflare Tunnel via Docker Compose, installs health-check timer
4. **gatekeeper** — Phase 0 stub (logs a skip message)

Then runs a post-task that hits `https://<pds_domain>/xrpc/_health` and confirms
the PDS is up. This is the green flag.

---

## Step 6 — Verify PDS health

After the playbook completes, verify manually:

```bash
# From your local machine
curl -s https://pds.yourfamily.net/xrpc/_health | jq .
```

Expected:
```json
{ "version": "0.4.x" }
```

SSH into the VPS via Tailscale and check containers:
```bash
# Connect via Tailscale (after first run, tailscale ssh works)
ssh root@pds-primary.tailnet.ts.net

# Check containers
docker compose -f /opt/pds/compose.yml -f /opt/pds/watchtower.yml ps

# Check Litestream
systemctl status litestream

# Check health check timer
systemctl status pds-health-check.timer
systemctl list-timers pds-health-check.timer

# View recent health check logs
journalctl -u pds-health-check.service -n 20
```

---

## Troubleshooting

### Playbook fails at "Assert Ubuntu 24.04"
Your VPS isn't running Ubuntu 24.04. Rebuild it in the Hostinger dashboard.

### Playbook fails at Tailscale join
- Check your auth key — it may be expired or exhausted
- Auth keys from the admin console have a limited lifetime (default 90 days)
- Make sure you used a **reusable** key if running against multiple hosts

### PDS health check times out
The Cloudflare Tunnel might not be ready yet. Possible causes:
- Tunnel token is wrong (re-copy from Cloudflare dashboard)
- DNS hasn't propagated yet (wait up to 5 minutes)
- PDS container failed to start — check: `docker compose -f /opt/pds/compose.yml logs pds`

### "community.docker not found" error
```bash
ansible-galaxy collection install community.docker
```

### Vault password prompt appears but nothing was encrypted
You didn't encrypt vault.yml. Run:
```bash
ansible-vault encrypt group_vars/vault.yml
```

---

## What Phase 0 does NOT include

These are planned for later phases:

- **Gatekeeper** — 2FA proxy in front of PDS admin endpoints (Phase 1)
- **Monitoring** — Grafana + Prometheus stack (`deploy-monitoring.yml` playbook)
- **NAS/storage** — MinIO provisioning (assumes it's already running)
- **Invite flow** — PDS is deployed in invite-required mode; invites via admin API

---

## Quick reference

```bash
# Re-run just the pds role after changes
ansible-playbook playbooks/provision-node.yml \
  -i inventory/hosts.yml \
  --ask-vault-pass \
  --tags pds

# Run in verbose mode to debug
ansible-playbook playbooks/provision-node.yml \
  -i inventory/hosts.yml \
  --ask-vault-pass \
  -vvv
```
