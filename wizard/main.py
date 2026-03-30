#!/usr/bin/env python3
"""
my-net setup wizard — entry point.

Orchestrates the setup steps in order and handles resume from state file.
Run via: python wizard/main.py
Or via:  bash install.sh (which runs this automatically)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the wizard's parent directory is on sys.path so `from wizard import ...` works
# regardless of the working directory the script is launched from.
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Python version guard (friendly message before any imports that might fail)
if sys.version_info < (3, 10):
    print(f"\n✗  Python 3.10+ is required (you have {sys.version})")
    print("   Please upgrade Python and re-run install.sh\n")
    sys.exit(1)

import signal  # noqa: E402

import questionary  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich import print as rprint  # noqa: E402

from wizard import state as wstate  # noqa: E402

console = Console()


def _handle_interrupt(sig, frame):
    """Graceful Ctrl+C handler."""
    console.print()
    console.print(Panel(
        "[yellow]Setup paused.[/yellow]\n\n"
        "Your progress has been saved to [cyan]~/.mynet/setup-state.json[/cyan]\n"
        "Re-run the wizard any time to pick up where you left off:\n\n"
        "  [bold]bash install.sh[/bold]  (re-downloads and relaunches)\n"
        "  [bold]python ~/.mynet/wizard/main.py[/bold]  (faster if already installed)",
        border_style="yellow",
        padding=(1, 2),
    ))
    console.print()
    sys.exit(0)


signal.signal(signal.SIGINT, _handle_interrupt)


STEPS = [
    ("welcome",     "wizard.steps.welcome"),
    ("server",      "wizard.steps.server"),
    ("domain",      "wizard.steps.domain"),
    ("cloudflare",  "wizard.steps.cloudflare"),
    ("tailscale",   "wizard.steps.tailscale"),
    ("credentials", "wizard.steps.credentials"),
    ("deploy",      "wizard.steps.deploy"),
]


def _import_step(module_path: str):
    """Dynamically import a step module and return it."""
    import importlib
    return importlib.import_module(module_path)


def _check_resume(state: dict) -> bool:
    """If there's existing state, ask whether to resume or start fresh."""
    completed = state.get("completed_steps", [])
    if not completed:
        return True  # Nothing to resume

    last = completed[-1]
    console.print()
    console.print(Panel(
        f"[yellow]Found an existing setup session.[/yellow]\n\n"
        f"Completed steps: {', '.join(completed)}\n"
        f"Last completed: [bold]{last}[/bold]",
        border_style="yellow",
        padding=(1, 2),
    ))
    console.print()

    choice = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("▶  Resume from where I left off", value="resume"),
            questionary.Choice("🔄  Start fresh (clear saved state)", value="fresh"),
        ],
    ).ask()

    if choice == "fresh":
        wstate.clear()
        return True

    return True  # resume — state is already loaded


def main() -> None:
    wizard_state = wstate.load()
    _check_resume(wizard_state)

    for step_name, module_path in STEPS:
        try:
            step_module = _import_step(module_path)
            wizard_state = step_module.run(wizard_state)
        except SystemExit:
            # Steps call SystemExit(0) for graceful exits (user bails out)
            raise
        except KeyboardInterrupt:
            _handle_interrupt(None, None)
        except ImportError as e:
            console.print(Panel(
                f"[red]Failed to load step '{step_name}':[/red] {e}\n\n"
                "Make sure all wizard dependencies are installed:\n"
                "  [bold]pip install -r ~/.mynet/wizard/requirements.txt[/bold]",
                border_style="red",
                title="[red]Import Error[/red]",
            ))
            sys.exit(1)
        except Exception as e:
            console.print(Panel(
                f"[red]Unexpected error in step '{step_name}':[/red]\n\n{e}\n\n"
                "[dim]Your progress has been saved. Re-run the wizard to retry this step.[/dim]",
                border_style="red",
                title="[red]Error[/red]",
            ))
            console.print_exception()
            sys.exit(1)

    # If we get here all steps passed (deploy step handles its own success/fail messaging)


if __name__ == "__main__":
    main()
