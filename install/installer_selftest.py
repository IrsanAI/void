#!/usr/bin/env python3
"""VOID installer selftest.

Validates that core runtime files exist and are syntactically loadable.
Designed to be run by platform installers after clone/update.
"""

from __future__ import annotations

import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    ROOT / "game" / "void_launcher.py",
    ROOT / "game" / "void_server.py",
    ROOT / "game" / "void_client.py",
    ROOT / "game" / "void_relay.py",
    ROOT / "game" / "void_netcheck.py",
    ROOT / "game" / "void_doctor.py",
    ROOT / "game" / "void_smoke_test.py",
]


def main() -> int:
    missing = [p for p in REQUIRED if not p.exists()]
    if missing:
        print("[fail] missing files:")
        for p in missing:
            print(f" - {p}")
        return 1

    for p in REQUIRED:
        py_compile.compile(str(p), doraise=True)

    print("[ok] installer-selftest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
