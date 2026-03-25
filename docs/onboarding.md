# Onboarding Guide — Setting Up a New PDS Node

## Prerequisites

- Ubuntu Server 24.04 LTS installed (bare metal or Proxmox VM)
- Tailscale installed and authenticated (`tailscale up`)
- A domain with Cloudflare DNS management
- Cloudflare Tunnel created (save the tunnel token)
- MinIO running on your NAS (see `compose/storage/`)
- Ansible installed on your management machine

## Step 1: Fill in your inventory

```bash
cp ansible/inventory/hosts.example.yml ansible/inventory/hosts.yml
# Edit hosts.yml — set ansible_host to your Tailscale hostname or IP
```

## Step 2: Create secrets file

Create `ansible/group_vars/vault.yml` (never commit this file):

```yaml
# ansible/group_vars/vault.yml — encrypt with ansible-vault
pds_jwt_secret: "<openssl rand -hex 32>"
pds_admin_password: "<strong random password>"
pds_plc_rotation_key: "<from Ledger — see docs/security.md>"
minio_access_key: "<minio access key>"
minio_secret_key: "<minio secret key>"
cloudflare_tunnel_token: "<tunnel token from Cloudflare dashboard>"
smtp_user: "<email smtp user>"
smtp_password: "<smtp app password>"
smtp_host: "<smtp.example.com>"
grafana_admin_password: "<strong password>"
```

Encrypt it:
```bash
ansible-vault encrypt ansible/group_vars/vault.yml
```

## Step 3: Set up Cloudflare Tunnel

In Cloudflare Zero Trust dashboard:
1. Create a new tunnel — name it after your PDS (e.g., `pds-primary`)
2. Copy the tunnel token — add to vault as `cloudflare_tunnel_token`
3. Add a Public Hostname route: `your-community.example.com` → `http://pds:3000`
4. Enable WebSocket support

## Step 4: Run provisioning

```bash
cd ansible
ansible-playbook playbooks/provision-node.yml -i inventory/hosts.yml --ask-vault-pass
```

This will:
- Harden the OS (UFW, fail2ban, unattended-upgrades)
- Install Docker
- Install Litestream
- Deploy PDS + cloudflared + Watchtower
- Deploy PDS Gatekeeper
- Set up health check timer

## Step 5: Create the first admin account

```bash
# SSH to the PDS node via Tailscale
ssh steve@pds-primary.tailnet.ts.net

# Use goat CLI (built into the PDS container)
docker exec -it pds goat account create --admin
```

## Step 6: Connect via Bluesky app

1. Open Bluesky → **Settings** → **Advanced** → **Change handle**
2. Enter your PDS domain: `your-community.example.com`
3. Create account — users get handles like `username.your-community.example.com`

## Connecting the Bluesky App to a Custom PDS

On initial setup:
- Tap **"Use a custom hosting provider"** on the sign-in screen
- Enter your PDS URL: `https://your-community.example.com`

---

## Adding a Federated Home Node

For community members who want to self-host:

```bash
# Their hosts.yml entry:
pds-home-node:
  ansible_host: <their Tailscale IP>
  pds_domain: alice.your-community.example.com

# Run the same playbook — it handles everything
ansible-playbook playbooks/provision-node.yml -i inventory/hosts.yml --limit pds-home-node
```

Their blob storage will point to the community MinIO via Tailscale — no separate S3 setup needed.
