"""ASCII art diagrams used across wizard steps."""


def architecture() -> str:
    return """
    ┌─────────────────────────────────────────────────────────────┐
    │                     YOUR SOVEREIGN CLOUD                    │
    │                                                             │
    │   Public Internet                                           │
    │         │                                                   │
    │         ▼                                                   │
    │   ┌──────────────┐                                          │
    │   │  Cloudflare  │  ← DDoS protection, CDN, free SSL       │
    │   │    Tunnel    │                                          │
    │   └──────┬───────┘                                          │
    │          │  encrypted tunnel (no open ports!)              │
    │          ▼                                                   │
    │   ┌──────────────────────────────────────┐                 │
    │   │         YOUR VPS (Hostinger)         │                 │
    │   │                                      │                 │
    │   │  ┌─────────────┐  ┌───────────────┐ │                 │
    │   │  │     PDS     │  │     MinIO     │ │                 │
    │   │  │  (Bluesky)  │  │ (blob storage)│ │                 │
    │   │  └─────────────┘  └───────────────┘ │                 │
    │   │                                      │                 │
    │   └──────────────────────────────────────┘                 │
    │          │                                                   │
    │          ▼  (private mesh)                                  │
    │   ┌──────────────┐                                          │
    │   │  Tailscale   │  ← secure access from YOUR devices only │
    │   │  (WireGuard) │                                          │
    │   └──────────────┘                                          │
    └─────────────────────────────────────────────────────────────┘
    """


def cloudflare_tunnel() -> str:
    return """
    ┌──────────────────────────────────────────────────────────┐
    │                   HOW CLOUDFLARE WORKS                   │
    │                                                          │
    │   Your Followers          You / Your Users              │
    │        │                         │                      │
    │        ▼                         ▼                      │
    │   ┌─────────────────────────────────────┐               │
    │   │         Cloudflare Network          │               │
    │   │   (free SSL, DDoS protection, CDN)  │               │
    │   └────────────────┬────────────────────┘               │
    │                    │                                     │
    │                    │  ← encrypted tunnel                 │
    │                    │  ← NO inbound ports needed!         │
    │                    │                                     │
    │                    ▼                                     │
    │   ┌────────────────────────────────────┐                │
    │   │        YOUR VPS (Hostinger)        │                │
    │   │   cloudflared daemon running here  │                │
    │   │   connects OUT to Cloudflare       │                │
    │   └────────────────────────────────────┘                │
    │                                                          │
    │  ✓ No firewall rules needed   ✓ Free SSL certificate    │
    │  ✓ DDoS protection included   ✓ Your IP stays hidden    │
    └──────────────────────────────────────────────────────────┘
    """


def tailscale_mesh() -> str:
    return """
    ┌──────────────────────────────────────────────────────────┐
    │                  YOUR PRIVATE MESH NETWORK               │
    │                                                          │
    │   ┌──────────────┐         ┌──────────────┐             │
    │   │  Your Laptop │         │  Your Phone  │             │
    │   │  (Tailscale) │         │  (Tailscale) │             │
    │   └──────┬───────┘         └──────┬───────┘             │
    │          │                         │                     │
    │          │    WireGuard encrypted  │                     │
    │          │◄───────────────────────►│                     │
    │          │                         │                     │
    │          └───────────┬─────────────┘                     │
    │                      │                                   │
    │                      ▼                                   │
    │          ┌───────────────────────┐                       │
    │          │    YOUR VPS           │                       │
    │          │    (Tailscale node)   │                       │
    │          │                       │                       │
    │          │  SSH: ssh root@<ip>   │                       │
    │          │  Admin: :8080         │                       │
    │          └───────────────────────┘                       │
    │                                                          │
    │  ✓ Only YOUR devices can connect  ✓ No passwords needed  │
    │  ✓ Works from anywhere            ✓ Military-grade crypto│
    └──────────────────────────────────────────────────────────┘
    """


def deployment_flow() -> str:
    return """
    ┌──────────────────────────────────────────────────────────┐
    │                    WHAT WE'RE DOING NOW                  │
    │                                                          │
    │   1. ✅ Write configuration files (Ansible)              │
    │                  │                                       │
    │                  ▼                                       │
    │   2. 🔄 Connect to your VPS via SSH                     │
    │                  │                                       │
    │                  ▼                                       │
    │   3. 🔄 Install Docker + dependencies                   │
    │                  │                                       │
    │                  ▼                                       │
    │   4. 🔄 Configure Cloudflare tunnel                     │
    │                  │                                       │
    │                  ▼                                       │
    │   5. 🔄 Configure Tailscale mesh                        │
    │                  │                                       │
    │                  ▼                                       │
    │   6. 🔄 Start Bluesky PDS server                        │
    │                  │                                       │
    │                  ▼                                       │
    │   7. 🔄 Verify everything is healthy                    │
    │                  │                                       │
    │                  ▼                                       │
    │   8. 🎉 Your server is live!                            │
    └──────────────────────────────────────────────────────────┘
    """
