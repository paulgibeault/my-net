"""SSH connection validator using paramiko."""
from __future__ import annotations

import socket
from typing import Tuple


def test_ssh_connection(host: str, password: str, port: int = 22, username: str = "root", timeout: int = 15) -> Tuple[bool, str]:
    """
    Test an SSH connection to the given host.

    Returns:
        (success: bool, message: str)
    """
    try:
        import paramiko
    except ImportError:
        return False, "paramiko is not installed — run: pip install paramiko"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        # Run a quick sanity check
        _, stdout, _ = client.exec_command("echo ok")
        result = stdout.read().decode().strip()
        client.close()

        if result == "ok":
            return True, f"Connected to {host} as {username} ✓"
        else:
            return False, f"Connected but got unexpected response: {result!r}"

    except paramiko.AuthenticationException:
        return False, "Authentication failed — wrong password? Double-check and try again."
    except paramiko.SSHException as e:
        return False, f"SSH error: {e}"
    except socket.timeout:
        return False, f"Connection timed out after {timeout}s — is the IP correct? Is the server running?"
    except socket.gaierror as e:
        return False, f"Could not resolve host '{host}': {e}"
    except ConnectionRefusedError:
        return False, f"Connection refused on port {port} — SSH might not be running on the server."
    except OSError as e:
        return False, f"Network error: {e}"
    finally:
        try:
            client.close()
        except Exception:
            pass
