# my-net Setup Wizard

A guided terminal wizard that hand-holds non-technical users through setting up a self-hosted Bluesky PDS on a Hostinger VPS.

Think of it like a router setup page — but in the terminal.

---

## What it sets up

| Service | What it does | Access |
|---|---|---|
| **Bluesky PDS** | Your personal Bluesky server | Public (via Cloudflare) |
| **Portainer CE** | Visual Docker management dashboard | Private (Tailscale only) |
| **MinIO** | S3-compatible blob storage for media | Internal |
| **Cloudflare Tunnel** | Secure public edge, free SSL, DDoS protection | Public edge |
| **Tailscale** | Encrypted private mesh for admin access | Private mesh |

---

## Quick start

```bash
curl -sSL https://raw.githubusercontent.com/paulgibeault/my-net/main/install.sh | bash
```

Or if you've already cloned the repo:

```bash
bash install.sh
```

---

## Platform support

| Platform | Supported |
|---|---|
| macOS | ✅ |
| Linux (Ubuntu, Debian, Fedora, etc.) | ✅ |
| WSL2 on Windows | ✅ |
| Native Windows | ❌ (installer prints WSL2 setup instructions) |

---

## Wizard steps

1. **Welcome** — explains what my-net is, pick deployment profile (cloud/onprem/hybrid)
2. **Server** — VPS IP + root password, SSH connection test
3. **Domain** — domain name entry + validation
4. **Cloudflare** — step-by-step tunnel setup guide + token entry
5. **Tailscale** — step-by-step mesh setup guide + auth key entry + ACL snippet
6. **Credentials** — admin password + auto-generated JWT secret + PLC rotation key
7. **Deploy** — review summary → generate Ansible files → ansible-vault encrypt → run playbook

---

## Resume / interrupted setups

Progress is saved to `~/.mynet/setup-state.json` after each step. Re-run the wizard to pick up where you left off.

**Note:** Sensitive fields (passwords, tokens, generated secrets) are **never written to disk**. You'll be asked for them again on resume — this is intentional.

---

## File structure

```
wizard/
├── main.py                  # Entry point — orchestrates steps
├── state.py                 # Reads/writes ~/.mynet/setup-state.json
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── steps/
│   ├── welcome.py           # Step 1: banner + profile selection
│   ├── server.py            # Step 2: VPS IP + SSH test
│   ├── domain.py            # Step 3: domain name
│   ├── cloudflare.py        # Step 4: Cloudflare tunnel setup
│   ├── tailscale.py         # Step 5: Tailscale mesh setup
│   ├── credentials.py       # Step 6: admin password + crypto key gen
│   └── deploy.py            # Step 7: review + generate configs + run playbook
├── diagrams/
│   └── ascii.py             # ASCII art diagrams used across steps
└── validators/
    └── ssh.py               # SSH connection tester (paramiko)
```

---

## Contributing

Each step is an independent module in `wizard/steps/`. To add a new step:

1. Create `wizard/steps/mystep.py` with a `run(wizard_state: dict) -> dict` function
2. Add it to the `STEPS` list in `wizard/main.py`
3. Use `rich` for all output (panels, rules, progress bars)
4. Always explain **why** before asking anything
5. Support resume: check `wstate.is_step_complete(state, STEP_NAME)` at the top

---

## Security notes

- Sensitive values (`server_password`, `admin_password`, `jwt_secret`, `plc_rotation_key`, `cloudflare_token`, `tailscale_auth_key`) are held in memory only
- `state.py` strips these fields before writing to disk
- Vault file is encrypted with `ansible-vault` using the admin password as the vault key
- Portainer is bound to port 9443 and protected by firewall rules (Tailscale interface only)

---

*Built by Geebs 🤙 — part of the [my-net](https://github.com/paulgibeault/my-net) project*
