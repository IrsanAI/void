#!/usr/bin/env python3
"""
VOID — Launcher
Wähle: Solo / Multiplayer Client / Server starten
"""
import sys, os, tty, termios, subprocess

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

BASE = os.path.dirname(os.path.abspath(__file__))

def clear(): print("\033[2J\033[H", end="", flush=True)
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

def main():
    clear()
    print(b(BANNER))
    print()
    print(b("  Psychologisches Survival · Termux Edition"))
    print()
    print(f"  {g('[1]')} Solo spielen         {d('(Du vs VOID-KI)')}")
    print(f"  {c('[2]')} Multiplayer joinen   {d('(Client, Server-IP eingeben)')}")
    print(f"  {y('[3]')} Server starten       {d('(Hoste ein Spiel im WLAN)')}")
    print()
    print(f"  {gray('[Q]')} Beenden")
    print()
    print("  Wähle: ", end="", flush=True)

    ch = getch()

    if ch == '1':
        clear()
        os.execv(sys.executable, [sys.executable, os.path.join(BASE, "void_solo.py")])

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
        os.execv(sys.executable, [sys.executable, os.path.join(BASE, "void_client.py"), ip])

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
        print()
        print(d("  Teile diese IP mit deinen Mitspielern."))
        print(d("  Sie starten: python3 void_launcher.py → [2] → diese IP"))
        print()
        input("  [Enter] zum Starten des Servers...")
        os.execv(sys.executable, [sys.executable, os.path.join(BASE, "void_server.py")])

    elif ch == 'q':
        clear()
        print("\033[?25h", end="")
        sys.exit(0)

    else:
        main()

if __name__ == "__main__":
    main()
