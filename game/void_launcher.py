#!/usr/bin/env python3
"""
VOID — Launcher
Wähle: Solo / Multiplayer Client / Server starten
"""
import sys, os
import ipaddress
import subprocess
import platform

IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    import msvcrt
else:
    import tty
    import termios

def getch():
    if IS_WINDOWS:
        ch = msvcrt.getch()
        try:
            return ch.decode("utf-8", errors="ignore").lower()
        except Exception:
            return ""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

BASE = os.path.dirname(os.path.abspath(__file__))


def _platform_edition_label() -> str:
    if IS_WINDOWS:
        return "Windows Edition"
    if os.environ.get("TERMUX_VERSION"):
        return "Termux Edition"
    sysname = platform.system().lower()
    if "darwin" in sysname:
        return "Apple Shell Edition"
    return "Terminal Edition"


def _server_reachability_hint(ip_text: str) -> str:
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return d("  Hinweis: IP konnte nicht klassifiziert werden.")

    if ip.is_loopback:
        return y("  Achtung: Loopback-IP ist nur lokal erreichbar.")

    # CGNAT-Bereich explizit
    if ip in ipaddress.ip_network("100.64.0.0/10"):
        return y("  Hinweis: CGNAT-IP erkannt. Direkter Internet-Join oft nicht möglich.")

    if ip.is_private:
        return d("  Private IP: Join klappt i.d.R. nur im gleichen LAN oder via VPN (Tailscale/Zerotier).")

    return g("  Öffentliche IP erkannt. Prüfe trotzdem Firewall/Portfreigabe für 7777.")


def _require_file(path, label):
    if os.path.exists(path):
        return True
    clear()
    print(r(f"\n  Fehler: {label} nicht gefunden."))
    print(d("  Bitte Installation reparieren/neu ausführen."))
    print(d(f"  Erwartet: {path}"))
    input("\n  [Enter] zurück...")
    return False

def clear(): print("\033[2J\033[H", end="", flush=True)


def _run_netcheck(target_ip: str = ""):
    netcheck_path = os.path.join(BASE, "void_netcheck.py")
    if not _require_file(netcheck_path, "Netcheck-Datei"):
        return
    clear()
    print(b("\n  VPN / NETZ-CHECK"))
    print(d("  Prüfe VPN, IP-Typ und Erreichbarkeit von Port 7777."))
    print()
    args = [sys.executable, netcheck_path]
    if target_ip:
        args.append(target_ip)
    subprocess.run(args)
    print()
    input("  [Enter] zurück zum Launcher...")


def _vpn_checklist_block() -> str:
    return (
        "\n"
        "  QUICK-CHECK:\n"
        "  1) VPN aktiv? (Tailscale/Zerotier auf beiden Geräten)\n"
        "  2) Beide Geräte im selben VPN-Netz?\n"
        "  3) Host-Port 7777 erreichbar?\n"
        "  4) Bei Mobilfunk oft CGNAT: direkte IP-Join meist blockiert.\n"
    )
def b(s):    return f"\033[1m{s}\033[0m"
def g(s):    return f"\033[92m{s}\033[0m"
def r(s):    return f"\033[91m{s}\033[0m"
def y(s):    return f"\033[93m{s}\033[0m"
def d(s):    return f"\033[2m{s}\033[0m"
def c(s):    return f"\033[96m{s}\033[0m"
def gray(s): return f"\033[90m{s}\033[0m"

BANNER = gray("""
  ██╗   ██╗ ██████╗ ██╗██████╗
  ██║   ██║██╔═══██╗██║██╔══██╗
  ╚██╗ ██╔╝██║   ██║██║██║  ██║
   ╚████╔╝ ╚██████╔╝██║██████╔╝
    ╚═══╝   ╚═════╝ ╚═╝╚═════╝""")



def _start_relay_mode():
    relay_path = os.path.join(BASE, "void_relay.py")
    client_path = os.path.join(BASE, "void_client.py")
    server_path = os.path.join(BASE, "void_server.py")

    if not _require_file(relay_path, "Relay-Datei"):
        return

    clear()
    print(b("\n  RELAY BETA (Room-Code)"))
    print(d("  [1] Host-Bridge + lokalen Server starten"))
    print(d("  [2] Join-Bridge starten und lokal verbinden"))
    print()
    print("  Modus: ", end="", flush=True)
    ch = getch()

    if ch not in ('1', '2'):
        return

    clear()
    print(b("\n  Relay-Parameter"))
    print(d("  Relay-Host (z.B. VPS oder Tailscale-IP)"))
    print("  Relay-Host: ", end="", flush=True)
    print("\033[?25h", end="", flush=True)
    relay_host = input().strip()
    if not relay_host:
        relay_host = "127.0.0.1"

    print("  Relay-Port [8787]: ", end="", flush=True)
    raw_port = input().strip()
    try:
        relay_port = int(raw_port) if raw_port else 8787
    except ValueError:
        relay_port = 8787

    print("  Room-Code (z.B. VOID42): ", end="", flush=True)
    room = input().strip().upper()
    if not room:
        room = "VOID42"

    print("\033[?25l", end="", flush=True)

    if ch == '1':
        if not _require_file(server_path, "Server-Datei"):
            return
        cmd = [
            sys.executable, relay_path, "host",
            "--relay-host", relay_host,
            "--relay-port", str(relay_port),
            "--room", room,
            "--target-host", "127.0.0.1",
            "--target-port", "7777",
        ]
        subprocess.Popen(cmd, start_new_session=True)
        clear()
        print(g(f"\n  Relay-Host-Bridge gestartet (Room {room})."))
        print(d("  Starte jetzt den lokalen VOID-Server ..."))
        time.sleep(0.8)
        os.execv(sys.executable, [sys.executable, server_path])

    if ch == '2':
        if not _require_file(client_path, "Client-Datei"):
            return
        local_port = 17777
        cmd = [
            sys.executable, relay_path, "join",
            "--relay-host", relay_host,
            "--relay-port", str(relay_port),
            "--room", room,
            "--listen-host", "127.0.0.1",
            "--listen-port", str(local_port),
        ]
        proc = subprocess.Popen(cmd, start_new_session=True)
        time.sleep(0.7)
        if proc.poll() is not None:
            clear()
            print(r("\n  Relay-Join-Bridge konnte nicht gestartet werden."))
            input("  [Enter] zurück...")
            return
        clear()
        print(g(f"\n  Relay-Join-Bridge aktiv (Room {room})."))
        print(d("  Verbinde Client jetzt gegen localhost-Tunnel ..."))
        time.sleep(0.8)
        os.execv(sys.executable, [sys.executable, client_path, "127.0.0.1", str(local_port)])

def main():
    if IS_WINDOWS:
        os.system("")  # Aktiviert ANSI-Sequenzen in moderner Windows-Konsole

    clear()
    print(b(BANNER))
    print()
    print(b(f"  Psychologisches Survival · {_platform_edition_label()}"))
    print()
    print(f"  {g('[1]')} Solo spielen         {d('(Du vs VOID-KI)')}")
    print(f"  {c('[2]')} Multiplayer joinen   {d('(Client, Server-IP eingeben)')}")
    print(f"  {y('[3]')} Server starten       {d('(Hoste ein Spiel im WLAN)')}")
    print(f"  {gray('[4]')} VPN/Netz-Check       {d('(Tailscale/Zerotier Diagnose)')}")
    print(f"  {gray('[5]')} Relay (Beta)        {d('(Room-Code über Relay-Server)')}")
    print()
    print(f"  {gray('[Q]')} Beenden")
    print()
    print("  Wähle: ", end="", flush=True)

    ch = getch()

    if ch == '1':
        clear()
        solo_target = "void_solo_enhanced.py" if os.path.exists(os.path.join(BASE, "void_solo_enhanced.py")) else "void_solo.py"
        solo_path = os.path.join(BASE, solo_target)
        if not _require_file(solo_path, "Solo-Datei"):
            return main()
        os.execv(sys.executable, [sys.executable, solo_path])

    elif ch == '2':
        clear()
        print(b("\n  MULTIPLAYER — Client"))
        print(d("  Gib die IP des Servers ein (z.B. 192.168.1.42)"))
        print()
        print("  Server-IP: ", end="", flush=True)
        print("\033[?25h", end="", flush=True)  # Cursor zeigen
        try:
            ip = input().strip()
        except:
            ip = "127.0.0.1"
        if not ip:
            ip = "127.0.0.1"
        client_path = os.path.join(BASE, "void_client.py")
        if not _require_file(client_path, "Client-Datei"):
            return main()
        os.execv(sys.executable, [sys.executable, client_path, ip])

    elif ch == '3':
        clear()
        print(b("\n  MULTIPLAYER — Server starten"))
        print()
        # IP anzeigen
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            my_ip = s.getsockname()[0]
            s.close()
        except:
            my_ip = "127.0.0.1"

        print(f"  {b('Deine IP:')} {g(my_ip)}")
        print(f"  {b('Port:')}     7777")
        print(_server_reachability_hint(my_ip))
        print()
        print(d("  Teile diese IP mit deinen Mitspielern."))
        print(d("  Sie starten: python3 void_launcher.py → [2] → diese IP"))
        print()
        input("  [Enter] zum Starten des Servers...")
        server_path = os.path.join(BASE, "void_server.py")
        if not _require_file(server_path, "Server-Datei"):
            return main()
        os.execv(sys.executable, [sys.executable, server_path])


    elif ch == '4':
        clear()
        print(b("\n  VPN / NETZ-CHECK"))
        print(d("  Optional: Ziel-IP für Port-Check eingeben (Enter = nur lokaler Check)."))
        print(d(_vpn_checklist_block()))
        print("\n  Ziel-IP: ", end="", flush=True)
        print("\033[?25h", end="", flush=True)
        try:
            target = input().strip()
        except Exception:
            target = ""
        print("\033[?25l", end="", flush=True)
        _run_netcheck(target)
        return main()

    elif ch == '5':
        _start_relay_mode()
        return main()

    elif ch == 'q':
        clear()
        print("\033[?25h", end="")
        sys.exit(0)

    else:
        main()

if __name__ == "__main__":
    main()
