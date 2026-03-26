"""
Wizard state management.

Reads and writes ~/.mynet/setup-state.json so interrupted setups can resume.
Sensitive fields are kept in memory only during the session and written to
vault.yml at deploy time — never stored in plain text on disk.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Fields that must NEVER be written to the state file (stored in memory only)
_SENSITIVE_FIELDS = {
    "server_password",
    "admin_password",
    "admin_password_confirm",
    "jwt_secret",
    "plc_rotation_key",
}

STATE_DIR = Path.home() / ".mynet"
STATE_FILE = STATE_DIR / "setup-state.json"


def _state_path() -> Path:
    return STATE_FILE


def load() -> dict[str, Any]:
    """Load state from disk. Returns empty dict if no state file exists."""
    path = _state_path()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save(state: dict[str, Any]) -> None:
    """Save state to disk, stripping sensitive fields."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in state.items() if k not in _SENSITIVE_FIELDS}
    path = _state_path()
    # Write atomically via temp file
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(safe, f, indent=2)
    tmp.replace(path)
    # Restrict permissions: owner read/write only
    os.chmod(path, 0o600)


def clear() -> None:
    """Delete the state file (fresh start)."""
    path = _state_path()
    if path.exists():
        path.unlink()


def mark_step_complete(state: dict[str, Any], step_name: str) -> None:
    """Mark a step as complete in the state dict and save to disk."""
    completed = state.setdefault("completed_steps", [])
    if step_name not in completed:
        completed.append(step_name)
    save(state)


def is_step_complete(state: dict[str, Any], step_name: str) -> bool:
    """Return True if the given step has been completed."""
    return step_name in state.get("completed_steps", [])
