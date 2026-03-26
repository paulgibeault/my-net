"""
Step 1: Welcome + deployment profile selection.

Prints a banner, explains what my-net is, and asks the user to pick
a deployment profile. Only 'cloud' (Hostinger VPS) is fully implemented.
"""
from __future__ import annotations

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from wizard import state as wstate
from wizard.diagrams.ascii import architecture

console = Console()

STEP_NAME = "welcome"
TOTAL_STEPS = 6


def _banner() -> None:
    title = Text()
    title.append("  my-net  ", style="bold white on blue")
    title.append("  sovereign cloud setup wizard", style="bold cyan")

    console.print()
    console.print(Panel(
        title,
        border_style="blue",
        padding=(1, 4),
    ))
    console.print()


def _intro() -> None:
    console.print(Panel(
        "[bold]What is my-net?[/bold]\n\n"
        "my-net turns a cheap VPS into your own personal cloud — a place where "
        "[cyan]your data lives under your control[/cyan], not inside some corporation's servers.\n\n"
        "Specifically, this wizard sets up a [bold]Bluesky PDS[/bold] (Personal Data Server). "
        "Bluesky is a new social network, but unlike Twitter or Facebook, you can [italic]host your own node[/italic]. "
        "Your posts, followers, and identity live on YOUR server.\n\n"
        "[dim]Think of it like running your own email server — but for social media.[/dim]",
        title="[bold blue]Step 1 of {}/{}  —  Welcome[/bold blue]".format(1, TOTAL_STEPS),
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


def _architecture_diagram() -> None:
    console.print(Panel(
        architecture(),
        title="[bold]Here's what we're building[/bold]",
        border_style="dim",
        padding=(0, 1),
    ))
    console.print()


def _pick_profile() -> str:
    console.print("[bold]Choose your deployment profile:[/bold]\n")
    console.print("  [cyan]cloud[/cyan]    — VPS on Hostinger (recommended for beginners)")
    console.print("  [dim]onprem[/dim]   — Your own hardware at home [dim](coming soon)[/dim]")
    console.print("  [dim]hybrid[/dim]   — Cloud + home hardware together [dim](coming soon)[/dim]")
    console.print()

    choice = questionary.select(
        "Which deployment profile would you like?",
        choices=[
            questionary.Choice("☁️  Cloud (Hostinger VPS) — recommended", value="cloud"),
            questionary.Choice("🏠  On-Premises (coming soon)", value="onprem"),
            questionary.Choice("🔀  Hybrid (coming soon)", value="hybrid"),
        ],
    ).ask()

    return choice or "cloud"


def run(wizard_state: dict) -> dict:
    """Run the welcome step. Returns updated state."""
    _banner()
    _intro()
    _architecture_diagram()

    # Resume check
    if wstate.is_step_complete(wizard_state, STEP_NAME):
        profile = wizard_state.get("deployment_profile", "cloud")
        console.print(f"[green]✓ Already completed — profile: [bold]{profile}[/bold][/green]")
        console.print()

        redo = questionary.confirm(
            "Do you want to change your deployment profile?",
            default=False,
        ).ask()

        if not redo:
            return wizard_state

    profile = _pick_profile()

    if profile in ("onprem", "hybrid"):
        console.print()
        console.print(Panel(
            f"[yellow]⚠  The [bold]{profile}[/bold] profile is coming soon!\n\n"
            "It's on the roadmap and we're actively building it. "
            "For now, only the [bold]cloud (Hostinger VPS)[/bold] profile is fully implemented.\n\n"
            "Switching you to cloud mode…[/yellow]",
            border_style="yellow",
        ))
        console.print()
        profile = "cloud"

    wizard_state["deployment_profile"] = profile
    wstate.mark_step_complete(wizard_state, STEP_NAME)

    console.print(f"[green]✓ Great! We'll set you up on a [bold]Hostinger VPS[/bold].[/green]")
    console.print()

    return wizard_state
