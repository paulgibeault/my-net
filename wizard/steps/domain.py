"""
Step 3: Domain name.

Asks for the domain name, validates format, and explains what a domain is.
"""
from __future__ import annotations

import re

import questionary
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from wizard import state as wstate

console = Console()

STEP_NAME = "domain"
TOTAL_STEPS = 6

# Reasonable domain regex: something.tld or sub.something.tld
_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"\.)+"
    r"[a-zA-Z]{2,}$"
)


def _header() -> None:
    console.print(Panel(
        "[bold]A domain name is your server's address on the internet.[/bold]\n\n"
        "Just like your home has a street address, your Bluesky server needs a name like "
        "[cyan]bsky.myname.com[/cyan] or [cyan]social.myfamily.net[/cyan].\n\n"
        "You'll need to own a domain name for this. If you don't have one yet, "
        "you can buy one at [link]https://www.namecheap.com[/link] for about [bold]$10–15/year[/bold]. "
        "Then we'll connect it to Cloudflare in the next step.\n\n"
        "[dim]Note: This will be your Bluesky handle's root domain. "
        "If your domain is [italic]myname.com[/italic], your handle will be [italic]@myname.com[/italic].[/dim]",
        title="[bold blue]Step 3 of {}  —  Your Domain Name[/bold blue]".format(TOTAL_STEPS),
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


def _validate_domain(domain: str) -> tuple[bool, str]:
    """Return (valid, error_message)."""
    domain = domain.strip().lower()

    if not domain:
        return False, "Domain name can't be blank."

    # Strip leading http(s):// if user pasted a URL
    if domain.startswith("http://"):
        domain = domain[7:]
    if domain.startswith("https://"):
        domain = domain[8:]
    # Strip trailing slashes
    domain = domain.rstrip("/")

    if not _DOMAIN_RE.match(domain):
        return False, (
            "That doesn't look like a valid domain name.\n"
            "Expected something like: [yellow]myname.com[/yellow] or [yellow]bsky.myname.net[/yellow]\n"
            "No spaces, no special characters, must have at least one dot."
        )

    if len(domain) > 253:
        return False, "Domain name is too long (max 253 characters)."

    return True, domain  # second value is cleaned domain on success


def _get_domain(current: str = "") -> str:
    while True:
        domain = questionary.text(
            "What domain name will you use for your Bluesky server?",
            default=current or "",
            instruction="(e.g. bsky.myname.com or social.myfamily.net)",
        ).ask()

        if domain is None:
            raise SystemExit(0)

        valid, result = _validate_domain(domain)
        if valid:
            return result
        else:
            rprint(f"[red]That doesn't look right —[/red] {result}")
            console.print()


def run(wizard_state: dict) -> dict:
    """Run the domain step. Returns updated state."""
    _header()

    # Resume check
    if wstate.is_step_complete(wizard_state, STEP_NAME):
        current_domain = wizard_state.get("domain", "")
        console.print(f"[green]✓ Already configured — domain: [bold]{current_domain}[/bold][/green]")
        console.print()

        redo = questionary.confirm(
            "Do you want to change your domain?",
            default=False,
        ).ask()

        if not redo:
            return wizard_state

    domain = _get_domain(wizard_state.get("domain", ""))

    wizard_state["domain"] = domain
    wstate.mark_step_complete(wizard_state, STEP_NAME)

    console.print()
    console.print(f"[green]✓ Domain set to [bold]{domain}[/bold][/green]")
    console.print(
        f"[dim]Your Bluesky handle will be [italic]@{domain}[/italic][/dim]"
    )
    console.print()

    return wizard_state
