"""
Step 5: Tailscale setup.

Step-by-step guide to Tailscale setup, validates auth key format,
and walks through ACL tag setup with exact copy-paste snippets.
"""
from __future__ import annotations

import re

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich import print as rprint

from wizard import state as wstate
from wizard.diagrams.ascii import tailscale_mesh

console = Console()

STEP_NAME = "tailscale"
TOTAL_STEPS = 6

# Tailscale auth keys: tskey-auth-<base62string>-<base62string>
_TSKEY_RE = re.compile(r"^tskey-auth-[A-Za-z0-9]+-[A-Za-z0-9]+$")


def _header() -> None:
    console.print(Panel(
        "[bold]Tailscale gives you a private, encrypted network between your devices and your server.[/bold]\n\n"
        "Think of it as a [cyan]VPN that just works[/cyan] — your laptop, phone, and server all get "
        "private IP addresses on the same virtual network. You can SSH into your server from anywhere "
        "in the world without exposing it to the internet.\n\n"
        "Tailscale uses [bold]WireGuard[/bold] under the hood — military-grade encryption with zero configuration. "
        "The free tier supports up to [bold]100 devices[/bold], which is more than enough.",
        title="[bold blue]Step 5 of {}  —  Tailscale Private Network[/bold blue]".format(TOTAL_STEPS),
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


def _show_diagram() -> None:
    console.print(Panel(
        tailscale_mesh(),
        title="[bold]Your Private Mesh Network[/bold]",
        border_style="dim",
        padding=(0, 1),
    ))
    console.print()


def _show_acl_snippet() -> None:
    console.print(Panel(
        "[bold]ACL Tag for your server[/bold]\n\n"
        "Tailscale uses 'tags' to identify your server in access rules. "
        "We use the tag [yellow]tag:my-net-server[/yellow] to let your devices reach it.\n\n"
        "After creating your account, add this to your [bold]Tailscale ACL[/bold] "
        "(Dashboard → Access Controls → Edit ACL):",
        border_style="yellow",
        padding=(1, 2),
    ))

    acl_snippet = '''{
  "tagOwners": {
    "tag:my-net-server": ["autogroup:owner"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["autogroup:owner"],
      "dst": ["tag:my-net-server:*"]
    }
  ]
}'''
    console.print(Syntax(acl_snippet, "json", theme="monokai", line_numbers=False, padding=(1, 2)))
    console.print()
    console.print("[dim]You can merge this with your existing ACL — just add the tagOwners and acls entries.[/dim]")
    console.print()


def _show_instructions() -> None:
    console.print(Rule("[bold cyan]How to get your Tailscale Auth Key[/bold cyan]"))
    console.print()
    console.print("[bold]Follow these steps (takes about 5 minutes):[/bold]\n")

    steps = [
        (
            "Create a free Tailscale account",
            "Go to [link]https://tailscale.com[/link] and sign up.\n"
            "   You can use your Google or GitHub account — it's free.",
        ),
        (
            "Set up ACL tags (optional but recommended)",
            "In the Tailscale Admin Console, go to [bold]Access Controls[/bold].\n"
            "   Add the ACL snippet shown above — this lets you control which devices\n"
            "   can reach your server.",
        ),
        (
            "Generate an auth key",
            "Go to [bold]Settings → Keys[/bold] in the Tailscale Admin Console.\n"
            "   Click [bold]'Generate auth key'[/bold].\n"
            "   Settings to use:\n"
            "   • [yellow]Reusable:[/yellow] Yes (so the server can re-register if it reboots)\n"
            "   • [yellow]Ephemeral:[/yellow] No\n"
            "   • [yellow]Tags:[/yellow] [cyan]tag:my-net-server[/cyan] (if you set up ACL tags above)\n"
            "   Click [bold]'Generate key'[/bold].",
        ),
        (
            "Copy the key",
            "The key looks like: [yellow]tskey-auth-kBJa1CNTRL-EXAMPLE123[/yellow]\n"
            "   Copy it — [bold]you won't be able to see it again[/bold] after closing the dialog.",
        ),
        (
            "Install Tailscale on your devices (later)",
            "After setup, install Tailscale on your laptop/phone to access your server privately.\n"
            "   Download at [link]https://tailscale.com/download[/link]",
        ),
    ]

    for i, (title, detail) in enumerate(steps, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] [bold]{title}[/bold]")
        console.print(f"     {detail}")
        console.print()


def _validate_key(key: str) -> tuple[bool, str]:
    """Validate Tailscale auth key format."""
    key = key.strip()

    if not key:
        return False, "Auth key can't be blank."

    if not key.startswith("tskey-auth-"):
        return False, (
            "Tailscale auth keys start with [yellow]tskey-auth-[/yellow]\n"
            "Make sure you generated an [bold]auth key[/bold] (not an API key or OAuth key)."
        )

    if not _TSKEY_RE.match(key):
        return False, (
            "That doesn't look like a valid Tailscale auth key.\n"
            "Expected format: [yellow]tskey-auth-XXXXXXXXXX-YYYYYYYYYY[/yellow]"
        )

    return True, key


def _get_auth_key() -> str:
    while True:
        key = questionary.password(
            "Paste your Tailscale auth key:",
            instruction="(starts with tskey-auth-...)",
        ).ask()

        if key is None:
            raise SystemExit(0)

        valid, result = _validate_key(key)
        if valid:
            return result

        rprint(f"[red]That doesn't look right —[/red] {result}")
        console.print()


def run(wizard_state: dict) -> dict:
    """Run the Tailscale step. Returns updated state."""
    _header()
    _show_diagram()
    _show_acl_snippet()
    _show_instructions()

    # Resume check
    if wstate.is_step_complete(wizard_state, STEP_NAME):
        console.print("[green]✓ Tailscale auth key already configured[/green]")
        console.print()

        redo = questionary.confirm(
            "Do you want to update your Tailscale auth key?",
            default=False,
        ).ask()

        if not redo:
            # Key is sensitive — re-ask (not stored on disk)
            console.print("[yellow]We'll need your Tailscale auth key again to continue.[/yellow]")
            key = _get_auth_key()
            wizard_state["tailscale_auth_key"] = key
            return wizard_state

    console.print(Rule("[bold]Ready to enter your auth key?[/bold]"))
    console.print()
    console.print("[dim]If you haven't created your Tailscale account yet, do it now and come back.[/dim]")
    console.print("[dim]Press Ctrl+C to exit and re-run when ready.[/dim]")
    console.print()

    key = _get_auth_key()

    wizard_state["tailscale_auth_key"] = key
    wstate.mark_step_complete(wizard_state, STEP_NAME)

    console.print()
    console.print("[green]✓ Tailscale auth key saved![/green]")
    console.print()

    return wizard_state
