#!/usr/bin/env python3
"""
VOID smoke tests (lightweight, no external dependencies).

Checks:
1) Syntax compile for core runtime files.
2) Relay JSON framing behavior for back-to-back control frames.
3) Relay argument parser for server/join options.
"""

from __future__ import annotations

import py_compile
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CHECK_FILES = [
    ROOT / "void_launcher.py",
    ROOT / "void_client.py",
    ROOT / "void_server.py",
    ROOT / "void_relay.py",
    ROOT / "void_netcheck.py",
    ROOT / "void_doctor.py",
]

INSTALLER_FILES = [
    ROOT.parent / "install" / "install.sh",
    ROOT.parent / "install" / "install_ios.sh",
    ROOT.parent / "install" / "install_windows.ps1",
    ROOT.parent / "install" / "installer_selftest.py",
]


def check_compile() -> None:
    for path in CHECK_FILES:
        py_compile.compile(str(path), doraise=True)


def check_relay_json_framing() -> None:
    import void_relay as relay

    a, b = socket.socketpair()
    try:
        a.sendall(b'{"one": 1}\n{"two": 2}\n')
        first = relay._recv_json_line(b, timeout=1)
        second = relay._recv_json_line(b, timeout=1)
        assert first == {"one": 1}, f"Unexpected first message: {first}"
        assert second == {"two": 2}, f"Unexpected second message: {second}"
    finally:
        a.close()
        b.close()


def check_relay_parser() -> None:
    import void_relay as relay

    parser = relay.build_parser()
    server_args = parser.parse_args(["server", "--listen-port", "8787", "--room-ttl", "120"])
    assert server_args.mode == "server"
    assert server_args.room_ttl == 120

    join_args = parser.parse_args([
        "join",
        "--relay-host",
        "127.0.0.1",
        "--room",
        "ABC42",
        "--retry-seconds",
        "10",
        "--retry-interval",
        "0.5",
    ])
    assert join_args.mode == "join"
    assert join_args.retry_seconds == 10
    assert abs(join_args.retry_interval - 0.5) < 1e-9


def check_server_error_payload() -> None:
    import void_server as server

    vs = server.VoidServer()
    captured = {}

    def fake_send(_conn, data):
        captured.update(data)

    vs._send = fake_send  # type: ignore[method-assign]
    vs._send_error(None, "NOT_ENOUGH_ENERGY", "Zu wenig Energie", needed=5, energy=2)
    assert captured.get("type") == "error"
    assert captured.get("code") == "NOT_ENOUGH_ENERGY"
    assert captured.get("needed") == 5
    assert captured.get("energy") == 2


def check_installers_present() -> None:
    missing = [str(p) for p in INSTALLER_FILES if not p.exists()]
    assert not missing, f"Missing installer files: {', '.join(missing)}"


def main() -> int:
    checks = [
        ("compile", check_compile),
        ("relay-json-framing", check_relay_json_framing),
        ("relay-parser", check_relay_parser),
        ("server-error-payload", check_server_error_payload),
        ("installer-files", check_installers_present),
    ]

    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"[ok] {name}")
        except Exception as exc:
            failed += 1
            print(f"[fail] {name}: {exc}")

    if failed:
        print(f"\nSmoke test failed: {failed} check(s).")
        return 1

    print("\nSmoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
