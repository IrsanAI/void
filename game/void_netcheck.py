#!/usr/bin/env python3
"""VOID Netzwerk-Check
Schnelle Diagnose für Multiplayer-Reachability (LAN/VPN/CGNAT/Port 7777).
"""

import ipaddress
import os
import socket
import subprocess
import sys
from typing import Optional

PORT = 7777


def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def info(text: str):
    print(c("96", text))


def warn(text: str):
    print(c("93", text))


def good(text: str):
    print(c("92", text))


def bad(text: str):
    print(c("91", text))


def classify_ip(ip_text: str) -> str:
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return "ungültig"

    if ip.is_loopback:
        return "loopback (nur lokal)"
    if ip in ipaddress.ip_network("100.64.0.0/10"):
        return "CGNAT (direkter Internet-Join meist nicht möglich)"
    if ip.is_private:
        return "private IP (LAN/VPN nötig)"
    if ip.is_link_local:
        return "link-local"
    return "öffentlich"


def local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def tailscale_ip() -> Optional[str]:
    if not shutil_which("tailscale"):
        return None
    try:
        out = subprocess.check_output(["tailscale", "ip", "-4"], stderr=subprocess.DEVNULL, timeout=2)
        lines = [x.strip() for x in out.decode().splitlines() if x.strip()]
        return lines[0] if lines else None
    except Exception:
        return None


def shutil_which(cmd: str) -> bool:
    return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def check_port(host: str, port: int, timeout_s: float = 4.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_s)
    try:
        sock.connect((host, port))
        return True, "OK"
    except Exception as e:
        return False, str(e)
    finally:
        sock.close()


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else ""

    print(c("1", "\nVOID NETCHECK"))
    print("=" * 40)

    lip = local_ip()
    info(f"Lokale IP: {lip} ({classify_ip(lip)})")

    tip = tailscale_ip()
    if tip:
        good(f"Tailscale-IP erkannt: {tip} ({classify_ip(tip)})")
    else:
        warn("Keine Tailscale-IP erkannt (CLI fehlt oder nicht verbunden).")

    if target:
        info(f"\nPort-Check auf Ziel {target}:{PORT} ...")
        ok, msg = check_port(target, PORT)
        if ok:
            good("Verbindung zu Port 7777 erfolgreich.")
        else:
            bad(f"Port 7777 nicht erreichbar: {msg}")
            warn("Hinweis: Bei CGNAT/private IP ist direkter Internet-Join oft blockiert.")
    else:
        warn("\nKein Ziel angegeben: nur lokale/VPN Diagnose ausgeführt.")

    print("\nEmpfehlung:")
    print("- Für Internet-Multiplayer: beide Geräte in Tailscale/Zerotier.")
    print("- Danach mit VPN-IP joinen (nicht mit Mobilfunk/Router-LAN-IP).")
    print()


if __name__ == "__main__":
    main()
