"""
Step 6a: Credentials setup.

Asks for admin password (min 16 chars, confirm), generates JWT secret
and PLC rotation key automatically. Sensitive values are NEVER written
to disk — only passed in memory until deploy time when they go into
an ansible-vault encrypted file.
"""
from __future__ import annotations

import secrets

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich import print as rprint

from wizard import state as wstate

console = Console()

STEP_NAME = "credentials"
TOTAL_STEPS = 6

_MIN_PASSWORD_LEN = 16
_SECRET_BYTES = 64  # for JWT secret and PLC key


def _generate_secret(nbytes: int = _SECRET_BYTES) -> str:
    """Generate a cryptographically secure hex secret."""
    return secrets.token_hex(nbytes)


def _header() -> None:
    console.print(Panel(
        "[bold]Now we'll set up your admin credentials.[/bold]\n\n"
        "You need one password: your [cyan]admin password[/cyan]. This is what you'll use to log into "
        "your Bluesky PDS admin panel.\n\n"
        "We'll automatically generate the other secrets (JWT signing key, PLC rotation key) — "
        "these are cryptographic keys that [bold]you never need to see or remember[/bold]. "
        "They'll be securely encrypted and stored on your server.\n\n"
        "[dim]Minimum password length: 16 characters. Use a password manager![/dim]",
        title="[bold blue]Step 6 of {}  —  Set Admin Credentials[/bold blue]".format(TOTAL_STEPS),
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


def _get_admin_password() -> str:
    """Prompt for admin password with confirmation."""
    console.print(Rule("[bold]Admin Password[/bold]"))
    console.print()
    console.print(
        "[bold]Requirements:[/bold]\n"
        "  • At least [cyan]16 characters[/cyan]\n"
        "  • Use a mix of letters, numbers, and symbols\n"
        "  • Store it in a password manager — [bold]you can't recover it[/bold] if lost\n"
    )

    while True:
        password = questionary.password(
            "Choose an admin password:",
            instruction=f"(minimum {_MIN_PASSWORD_LEN} characters)",
        ).ask()

        if password is None:
            raise SystemExit(0)

        if len(password) < _MIN_PASSWORD_LEN:
            rprint(
                f"[red]Password is too short[/red] — "
                f"got {len(password)} characters, need at least {_MIN_PASSWORD_LEN}."
            )
            console.print()
            continue

        # Check for some complexity
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_letter and has_digit):
            rprint(
                "[yellow]⚠  Weak password detected[/yellow] — "
                "we recommend mixing letters AND numbers (and symbols if you can)."
            )
            ok = questionary.confirm("Use this password anyway?", default=False).ask()
            if not ok:
                console.print()
                continue

        # Confirm
        confirm = questionary.password(
            "Confirm your admin password:",
        ).ask()

        if confirm != password:
            rprint("[red]Passwords don't match — try again.[/red]")
            console.print()
            continue

        return password


def run(wizard_state: dict) -> dict:
    """Run the credentials step. Returns updated state."""
    _header()

    # Resume check
    if wstate.is_step_complete(wizard_state, STEP_NAME):
        console.print("[green]✓ Credentials already configured[/green]")
        console.print()

        redo = questionary.confirm(
            "Do you want to set a new admin password?",
            default=False,
        ).ask()

        if not redo:
            # Sensitive — need to re-ask since not stored on disk
            if "admin_password" not in wizard_state:
                console.print("[yellow]We'll need your admin password again to continue.[/yellow]")
                admin_password = _get_admin_password()
                wizard_state["admin_password"] = admin_password
                # Regenerate secrets (they're deterministic enough, just regenerate)
                wizard_state["jwt_secret"] = _generate_secret()
                wizard_state["plc_rotation_key"] = _generate_secret()
            return wizard_state

    admin_password = _get_admin_password()

    console.print()
    console.print(Rule("[bold]Generating cryptographic secrets[/bold]"))
    console.print()

    with console.status("[bold cyan]Generating JWT signing key...[/bold cyan]", spinner="dots"):
        jwt_secret = _generate_secret()
    console.print("[green]✓ JWT signing key generated[/green]")

    with console.status("[bold cyan]Generating PLC rotation key...[/bold cyan]", spinner="dots"):
        plc_rotation_key = _generate_secret()
    console.print("[green]✓ PLC rotation key generated[/green]")

    console.print()
    console.print(Panel(
        "[dim]These secrets are stored only in memory and will be encrypted before "
        "being written to your server. You'll never need to see or type them.[/dim]",
        border_style="dim",
        padding=(0, 2),
    ))
    console.print()

    # Store in state (memory only — state.py strips these before writing to disk)
    wizard_state["admin_password"] = admin_password
    wizard_state["jwt_secret"] = jwt_secret
    wizard_state["plc_rotation_key"] = plc_rotation_key

    wstate.mark_step_complete(wizard_state, STEP_NAME)

    console.print("[green]✓ Credentials configured![/green]")
    console.print()

    return wizard_state
