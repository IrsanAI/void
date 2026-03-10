#!/usr/bin/env python3
"""VOID doctor: quick runtime diagnostics."""

from __future__ import annotations

import os
import platform
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = [
    ROOT / "void_launcher.py",
    ROOT / "void_server.py",
    ROOT / "void_client.py",
    ROOT / "void_relay.py",
    ROOT / "void_netcheck.py",
]

OPTIONAL_COMMANDS = ["git", "python3", "python"]


def ok(msg: str) -> None:
    print(f"[ok] {msg}")


def warn(msg: str) -> None:
    print(f"[warn] {msg}")


def fail(msg: str) -> None:
    print(f"[fail] {msg}")


def check_python() -> bool:
    v = sys.version_info
    if v >= (3, 8):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    fail(f"Python {v.major}.{v.minor}.{v.micro} (>=3.8 required)")
    return False


def check_files() -> bool:
    missing = [p.name for p in REQUIRED_FILES if not p.exists()]
    if missing:
        fail("Missing core files: " + ", ".join(missing))
        return False
    ok("Core game files present")
    return True


def check_ports() -> bool:
    # binding test on loopback to detect obvious local conflicts
    targets = [7777, 8787]
    healthy = True
    for port in targets:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            ok(f"Loopback bind available on :{port}")
        except OSError as exc:
            warn(f"Port :{port} busy/unavailable ({exc})")
            healthy = False
        finally:
            s.close()
    return healthy


def check_env() -> None:
    sysname = platform.system().lower()
    if os.name == "nt":
        ok("Detected Windows environment")
    elif os.environ.get("TERMUX_VERSION"):
        ok("Detected Termux environment")
    elif "darwin" in sysname:
        ok("Detected Apple shell environment")
    else:
        warn(f"Unknown shell environment: {platform.platform()}")


def main() -> int:
    print("VOID doctor — quick diagnostics")
    print("=" * 36)

    checks = [check_python(), check_files(), check_ports()]
    check_env()

    if all(checks):
        ok("Doctor completed successfully")
        return 0

    warn("Doctor completed with warnings/failures")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
