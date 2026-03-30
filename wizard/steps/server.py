"""
Step 2: Server connection.

Asks for VPS IP + root password, tests SSH connection via paramiko,
and prints a diagram showing where the server fits in the architecture.
"""
from __future__ import annotations

import questionary
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from wizard import state as wstate
from wizard.validators.ssh import test_ssh_connection

console = Console()

STEP_NAME = "server"
TOTAL_STEPS = 6


def _header() -> None:
    console.print(Panel(
        "[bold]Your VPS is the heart of your sovereign cloud.[/bold]\n\n"
        "A VPS (Virtual Private Server) is a computer that lives in a data center and runs 24/7. "
        "You rent it from Hostinger — it's like having a computer in the cloud that you fully control.\n\n"
        "We need to connect to it via [cyan]SSH[/cyan] — that's just a secure way to run commands on a remote computer. "
        "Don't worry, we handle all the technical stuff.",
        title="[bold blue]Step 2 of {}  —  Connect to Your Server[/bold blue]".format(TOTAL_STEPS),
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


def _get_server_ip(current: str = "") -> str:
    prompt = "What is your VPS IP address?"
    if current:
        console.print(f"[dim]Current IP: {current}[/dim]")

    while True:
        ip = questionary.text(
            prompt,
            default=current or "",
            instruction="(e.g. 185.123.45.67)",
        ).ask()

        if not ip:
            rprint("[red]That doesn't look right — we need an IP address to connect.[/red]")
            continue

        # Basic sanity check: 4 octets, each 0-255
        parts = ip.strip().split(".")
        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return ip.strip()

        rprint(
            "[red]That doesn't look right — here's what we expect:[/red] "
            "[yellow]Four numbers separated by dots, like 185.123.45.67[/yellow]"
        )


def _get_server_password() -> str:
    while True:
        password = questionary.password(
            "What is the root password for your VPS?",
            instruction="(this is the password you set when creating the VPS on Hostinger)",
        ).ask()

        if password and len(password) >= 6:
            return password

        rprint("[red]Password seems too short — Hostinger passwords are usually at least 8 characters.[/red]")


def _test_connection(ip: str, password: str) -> bool:
    with console.status(f"[bold cyan]Connecting to {ip}...[/bold cyan]", spinner="dots"):
        ok, msg = test_ssh_connection(ip, password)

    if ok:
        console.print(f"[green]✓ {msg}[/green]")
        return True
    else:
        console.print(Panel(
            f"[red]Connection failed:[/red] {msg}\n\n"
            "[bold]Common fixes:[/bold]\n"
            "• Double-check the IP address in your Hostinger dashboard\n"
            "• Make sure the VPS is running (not suspended)\n"
            "• Try resetting the root password in Hostinger's panel\n"
            "• If you just created the VPS, wait 2-3 minutes for it to boot",
            border_style="red",
            title="[red]Connection Problem[/red]",
        ))
        return False


def run(wizard_state: dict) -> dict:
    """Run the server step. Returns updated state."""
    _header()

    # Resume check
    if wstate.is_step_complete(wizard_state, STEP_NAME):
        current_ip = wizard_state.get("server_ip", "")
        console.print(f"[green]✓ Already configured — server: [bold]{current_ip}[/bold][/green]")
        console.print()

        redo = questionary.confirm(
            "Do you want to change your server details?",
            default=False,
        ).ask()

        if not redo:
            # Still need the password (it's not stored on disk)
            console.print("[yellow]We'll need your server password again to continue.[/yellow]")
            password = _get_server_password()
            wizard_state["server_password"] = password
            return wizard_state

    while True:
        ip = _get_server_ip(wizard_state.get("server_ip", ""))
        password = _get_server_password()

        console.print()
        connected = _test_connection(ip, password)
        console.print()

        if connected:
            break

        retry = questionary.confirm("Try again with different credentials?", default=True).ask()
        if not retry:
            rprint("[yellow]No problem — you can re-run the wizard any time to retry.[/yellow]")
            raise SystemExit(0)

    wizard_state["server_ip"] = ip
    wizard_state["server_password"] = password  # memory only, not written to disk

    wstate.mark_step_complete(wizard_state, STEP_NAME)

    console.print("[green]✓ Server connection verified![/green]")
    console.print()

    return wizard_state
