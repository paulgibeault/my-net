"""
Step 4: Cloudflare setup.

Step-by-step guide to setting up a Cloudflare tunnel, asks for the tunnel
token, and validates its format.
"""
from __future__ import annotations

import re

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich import print as rprint

from wizard import state as wstate
from wizard.diagrams.ascii import cloudflare_tunnel

console = Console()

STEP_NAME = "cloudflare"
TOTAL_STEPS = 6

# Cloudflare tunnel tokens are base64url-encoded JWT-like blobs, always long
# Real format: eyJ... (base64url, usually 100+ chars)
_TOKEN_MIN_LEN = 50


def _header() -> None:
    console.print(Panel(
        "[bold]Cloudflare acts as a secure shield between the internet and your server.[/bold]\n\n"
        "Instead of opening ports on your VPS (which exposes it to hackers), we use a "
        "[cyan]Cloudflare Tunnel[/cyan]. Your server connects [italic]out[/italic] to Cloudflare — "
        "no inbound connections needed. Cloudflare handles SSL certificates, DDoS protection, "
        "and routes traffic to your server automatically.\n\n"
        "The best part: [bold]it's completely free[/bold] for personal use.",
        title="[bold blue]Step 4 of {}  —  Cloudflare Tunnel[/bold blue]".format(TOTAL_STEPS),
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


def _show_diagram() -> None:
    console.print(Panel(
        cloudflare_tunnel(),
        title="[bold]How Cloudflare Tunnel Works[/bold]",
        border_style="dim",
        padding=(0, 1),
    ))
    console.print()


def _show_instructions(domain: str) -> None:
    console.print(Rule("[bold cyan]How to get your Cloudflare Tunnel Token[/bold cyan]"))
    console.print()
    console.print(
        "[bold]Follow these steps (takes about 5 minutes):[/bold]\n"
    )

    steps = [
        (
            "Create a free Cloudflare account",
            "Go to [link]https://dash.cloudflare.com/sign-up[/link] and sign up.\n"
            "   It's free — no credit card needed.",
        ),
        (
            "Add your domain to Cloudflare",
            f"In the Cloudflare dashboard, click [bold]'Add a site'[/bold] and enter [cyan]{domain or 'your-domain.com'}[/cyan].\n"
            "   Select the [bold]Free plan[/bold].\n"
            "   Cloudflare will give you two nameservers (like [dim]ns1.cloudflare.com[/dim]).\n"
            "   Log in to wherever you bought your domain and update the nameservers to Cloudflare's.",
        ),
        (
            "Wait for nameservers to update",
            "This usually takes [bold]5–30 minutes[/bold] (sometimes up to 24 hours).\n"
            "   Cloudflare will send you an email when it's ready.",
        ),
        (
            "Create a Tunnel",
            "In the Cloudflare dashboard, go to:\n"
            "   [bold]Zero Trust → Access → Tunnels[/bold]\n"
            "   (or search for 'Tunnels' in the sidebar)\n"
            "   Click [bold]'Create a tunnel'[/bold].",
        ),
        (
            "Configure the tunnel",
            "• Name it anything, e.g. [yellow]my-net-pds[/yellow]\n"
            "   • Select [bold]'Cloudflared'[/bold] as the connector\n"
            "   • Click [bold]'Save tunnel'[/bold]",
        ),
        (
            "Copy your tunnel token",
            "On the next screen, Cloudflare shows you an install command. Look for the token:\n"
            "   [dim]cloudflared service install eyJhGci...[/dim]\n"
            "   Copy the long string starting with [yellow]eyJ[/yellow] — that's your token.\n"
            "   [bold]Don't run that command[/bold] — we'll handle the installation automatically.",
        ),
        (
            "Add a public hostname",
            f"Back in the tunnel settings, add a [bold]Public Hostname[/bold]:\n"
            "   • Subdomain: leave blank (or use a subdomain like [yellow]pds[/yellow])\n"
            f"   • Domain: [cyan]{domain or 'your-domain.com'}[/cyan]\n"
            "   • Service Type: [yellow]HTTP[/yellow], URL: [yellow]localhost:3000[/yellow]",
        ),
    ]

    for i, (title, detail) in enumerate(steps, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] [bold]{title}[/bold]")
        console.print(f"     {detail}")
        console.print()


def _validate_token(token: str) -> tuple[bool, str]:
    """Basic format check for Cloudflare tunnel token."""
    token = token.strip()

    if not token:
        return False, "Token can't be blank."

    if len(token) < _TOKEN_MIN_LEN:
        return False, (
            f"That token looks too short (got {len(token)} chars, expected at least {_TOKEN_MIN_LEN}).\n"
            "Make sure you copied the full token — it's a long string starting with [yellow]eyJ[/yellow]."
        )

    # Cloudflare tokens are base64url encoded, no spaces
    if " " in token:
        return False, "Token shouldn't contain spaces — make sure you copied just the token, not the full command."

    # Most CF tokens start with eyJ (base64url for `{"`)
    if not token.startswith("eyJ") and not re.match(r"^[A-Za-z0-9\-_=+/]+$", token):
        return False, (
            "That doesn't look like a Cloudflare tunnel token.\n"
            "The token should start with [yellow]eyJ[/yellow] and contain only letters, numbers, and hyphens."
        )

    return True, token


def _get_token() -> str:
    while True:
        token = questionary.password(
            "Paste your Cloudflare tunnel token here:",
            instruction="(the long string from the Cloudflare dashboard)",
        ).ask()

        if token is None:
            raise SystemExit(0)

        valid, result = _validate_token(token)
        if valid:
            return result

        rprint(f"[red]That doesn't look right —[/red] {result}")
        console.print()


def run(wizard_state: dict) -> dict:
    """Run the Cloudflare step. Returns updated state."""
    _header()
    _show_diagram()

    domain = wizard_state.get("domain", "your-domain.com")
    _show_instructions(domain)

    # Resume check
    if wstate.is_step_complete(wizard_state, STEP_NAME):
        console.print("[green]✓ Cloudflare tunnel token already configured[/green]")
        console.print()

        redo = questionary.confirm(
            "Do you want to update your Cloudflare tunnel token?",
            default=False,
        ).ask()

        if not redo:
            # Token is sensitive — re-ask for it (not stored on disk)
            console.print("[yellow]We'll need your tunnel token again to continue.[/yellow]")
            token = _get_token()
            wizard_state["cloudflare_token"] = token
            return wizard_state

    console.print(Rule("[bold]Ready to enter your token?[/bold]"))
    console.print()
    console.print("[dim]If you haven't set up Cloudflare yet, do it now and come back.[/dim]")
    console.print("[dim]The wizard will wait. Press Ctrl+C to exit and re-run when ready.[/dim]")
    console.print()

    token = _get_token()

    wizard_state["cloudflare_token"] = token
    wstate.mark_step_complete(wizard_state, STEP_NAME)

    console.print()
    console.print("[green]✓ Cloudflare tunnel token saved![/green]")
    console.print()

    return wizard_state
