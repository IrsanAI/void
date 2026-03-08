#!/usr/bin/env python3
"""
VOID - Client
Termux Android Terminal UI | Psychologisches Multiplayer-Survival
"""

import socket
import threading
import json
import time
import sys
import os
import ipaddress
import tty
import termios
import select

# ── Terminal-Steuerung ───────────────────────────────────────────
class Terminal:
    ESC = "\033["

    @staticmethod
    def clear():
        print("\033[2J\033[H", end="", flush=True)

    @staticmethod
    def goto(row, col):
        print(f"\033[{row};{col}H", end="", flush=True)

    @staticmethod
    def hide_cursor():
        print("\033[?25l", end="", flush=True)

    @staticmethod
    def show_cursor():
        print("\033[?25h", end="", flush=True)

    @staticmethod
    def color(text, code):
        return f"\033[{code}m{text}\033[0m"

    @staticmethod
    def bold(text):
        return f"\033[1m{text}\033[0m"

    @staticmethod
    def dim(text):
        return f"\033[2m{text}\033[0m"

    # Farben
    RED    = lambda _, t: f"\033[91m{t}\033[0m"
    GREEN  = lambda _, t: f"\033[92m{t}\033[0m"
    YELLOW = lambda _, t: f"\033[93m{t}\033[0m"
    CYAN   = lambda _, t: f"\033[96m{t}\033[0m"
    WHITE  = lambda _, t: f"\033[97m{t}\033[0m"
    GRAY   = lambda _, t: f"\033[90m{t}\033[0m"
    MAGENTA= lambda _, t: f"\033[95m{t}\033[0m"

T = Terminal()

# ── Spielzustand (Client-Seite) ──────────────────────────────────
class GameState:
    def __init__(self):
        self.player_id = None
        self.player_name = "Fragment_?"
        self.x = 0
        self.y = 0
        self.energy = 100
        self.score = 0
        self.alive = True
        self.game_active = False
        self.grid_size = 12
        self.signals = []
        self.others = []
        self.void_x = None
        self.void_y = None
        self.void_visible = False
        self.void_reveal_timer = 0
        self.time_left = 0
        self.messages = []       # Letzte N Nachrichten
        self.max_messages = 8
        self.lobby_count = 0
        self.lobby_needed = 2
        self.game_over = False
        self.final_scores = []
        self.phase = "connecting"  # connecting / lobby / game / over
        self.last_void_msg = ""
        self.void_aggression = 0.0
        self.revealed = False

    def add_message(self, msg: str, style: str = "normal"):
        ts = time.strftime("%H:%M:%S")
        self.messages.append((ts, msg, style))
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def update_from_state(self, data: dict):
        you = data.get("you", {})
        self.x = you.get("x", self.x)
        self.y = you.get("y", self.y)
        self.energy = you.get("energy", self.energy)
        self.score = you.get("score", self.score)
        self.alive = you.get("alive", self.alive)
        self.revealed = you.get("revealed", self.revealed)
        self.others = data.get("others", [])
        self.signals = data.get("signals", [])
        self.time_left = data.get("time_left", self.time_left)


GS = GameState()


# ── Renderer ─────────────────────────────────────────────────────
def render():
    T.clear()
    if GS.phase == "connecting":
        _render_connecting()
    elif GS.phase == "lobby":
        _render_lobby()
    elif GS.phase == "game":
        _render_game()
    elif GS.phase == "over":
        _render_game_over()

def _render_connecting():
    print()
    print(T.bold(T.color("  Verbinde mit VOID-Server...", "96")))
    print()

def _render_lobby():
    print(_void_banner_small())
    print()
    print(T.bold(T.color(f"  Du bist: {GS.player_name}", "93")))
    print(T.color(f"  Spieler im Raum: {GS.lobby_count}", "97"))
    if GS.lobby_needed > 0:
        print(T.color(f"  Warte auf {GS.lobby_needed} weiteren Spieler...", "90"))
    else:
        print(T.bold(T.color("  ► Spiel startet gleich!", "92")))
    print()
    _render_messages()
    print()
    print(T.dim("  [N] Name ändern    [Q] Beenden"))

def _render_game():
    cols = _get_term_width()
    _render_header()
    print()
    _render_grid()
    print()
    _render_stats()
    print()
    _render_messages()
    print()
    _render_controls()

def _render_header():
    w = _get_term_width()
    time_str = f"⏱ {GS.time_left}s"
    if GS.time_left <= 30:
        time_str = T.color(time_str, "91")
    else:
        time_str = T.color(time_str, "93")

    void_bar = _void_aggression_bar(GS.void_aggression)
    status = T.color("● LEBT", "92") if GS.alive else T.color("✖ TOT", "91")
    energy_bar = _energy_bar(GS.energy)

    print(T.bold(T.color(" ╔══ VOID ════════════════════════════╗", "90")))
    print(f"  {T.color('AGGRESSION', '91')} {void_bar}  {time_str}")
    print(f"  {T.bold(GS.player_name)} {status}  {T.color('⚡', '93')} {energy_bar}  {T.color('◈ '+str(GS.score), '96')}")
    if GS.last_void_msg:
        print(f"  {T.color('VOID:', '91')} {T.dim(GS.last_void_msg)}")
    print(T.color(" ╚════════════════════════════════════╝", "90"))

def _render_grid():
    size = GS.grid_size

    # Erstelle Grid
    grid = [['·'] * size for _ in range(size)]

    # Signale
    for sx, sy in GS.signals:
        if 0 <= sx < size and 0 <= sy < size:
            grid[sy][sx] = T.color('◈', '93')

    # VOID Position (wenn sichtbar)
    if GS.void_visible and time.time() < GS.void_reveal_timer:
        vx, vy = GS.void_x, GS.void_y
        if vx is not None and 0 <= vx < size and 0 <= vy < size:
            grid[vy][vx] = T.bold(T.color('▓', '91'))
    else:
        GS.void_visible = False

    # Andere Spieler
    for other in GS.others:
        ox = other.get('x')
        oy = other.get('y')
        if ox is not None and oy is not None and 0 <= ox < size and 0 <= oy < size:
            char = T.color('○', '96')
            if not other.get('alive', True):
                char = T.color('×', '90')
            grid[oy][ox] = char

    # Eigene Position
    if GS.alive:
        px, py = GS.x, GS.y
        if 0 <= px < size and 0 <= py < size:
            grid[py][px] = T.bold(T.color('◉', '92'))
    else:
        grid[GS.y][GS.x] = T.color('†', '90')

    # Render
    top = T.color("  ┌" + "──" * size + "┐", "90")
    bot = T.color("  └" + "──" * size + "┘", "90")
    print(top)
    for row in grid:
        line = T.color("  │", "90")
        for cell in row:
            line += cell + " "
        line += T.color("│", "90")
        print(line)
    print(bot)

    # Legende
    print(f"  {T.color('◉','92')} Du  "
          f"{T.color('○','96')} Andere  "
          f"{T.color('◈','93')} Signal  "
          f"{T.color('▓','91')} VOID  "
          f"{T.color('·','90')} Leer")

def _render_stats():
    alive_others = [o for o in GS.others if o.get('alive', True)]
    dead_others  = [o for o in GS.others if not o.get('alive', True)]

    print(T.color("  ── FRAGMENTE ────────────────────────", "90"))
    if alive_others:
        for o in alive_others:
            sc = o.get('score', 0)
            nm = o.get('name', '?')
            rev = T.color(" [EXPOSED]", "91") if o.get('revealed') else ""
            print(f"  {T.color('●', '96')} {nm}  {T.color('◈ '+str(sc), '90')}{rev}")
    if dead_others:
        for o in dead_others:
            print(f"  {T.color('×', '90')} {T.dim(o.get('name','?'))} {T.color('[verschluckt]','90')}")
    if not alive_others and not dead_others:
        print(T.dim("  Keine anderen Spieler."))

def _render_messages():
    if not GS.messages:
        return
    print(T.color("  ── LOG ──────────────────────────────", "90"))
    for ts, msg, style in GS.messages[-6:]:
        if style == "void":
            print(f"  {T.dim(ts)} {T.color(msg, '91')}")
        elif style == "good":
            print(f"  {T.dim(ts)} {T.color(msg, '92')}")
        elif style == "warn":
            print(f"  {T.dim(ts)} {T.color(msg, '93')}")
        else:
            print(f"  {T.dim(ts)} {T.dim(msg)}")

def _render_controls():
    print(T.color("  ── AKTIONEN ─────────────────────────", "90"))
    print(f"  {T.bold('W/A/S/D')} Bewegen  "
          f"{T.bold('E')} Scannen({GS.energy}≥15)  "
          f"{T.bold('P')} Ping  "
          f"{T.bold('R')} Rasten  "
          f"{T.bold('Q')} Quit")

def _render_game_over():
    T.clear()
    print()
    print(T.bold(T.color("  ╔══════════════════════════════╗", "91")))
    print(T.bold(T.color("  ║        SPIEL BEENDET         ║", "91")))
    print(T.bold(T.color("  ╚══════════════════════════════╝", "91")))
    print()
    print(T.bold("  ENDERGEBNIS:"))
    print()
    for i, entry in enumerate(GS.final_scores):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "  "
        alive_str = T.color(" (ÜBERLEBT)", "92") if entry.get("alive") else T.color(" (TOT)", "90")
        name = T.bold(entry["name"]) if i == 0 else entry["name"]
        print(f"  {medal} {name}  {T.color('◈ '+str(entry['score']), '93')}{alive_str}")
    print()
    print(T.dim("  [Drücke Q zum Beenden]"))

def _void_aggression_bar(level: float) -> str:
    filled = int(level * 10)
    bar = "█" * filled + "░" * (10 - filled)
    if level > 0.7:
        return T.color(f"[{bar}]", "91")
    elif level > 0.4:
        return T.color(f"[{bar}]", "93")
    return T.color(f"[{bar}]", "90")

def _energy_bar(energy: int) -> str:
    filled = int(energy / 10)
    bar = "█" * filled + "░" * (10 - filled)
    if energy > 60:
        return T.color(f"[{bar}] {energy}", "92")
    elif energy > 30:
        return T.color(f"[{bar}] {energy}", "93")
    return T.color(f"[{bar}] {energy}", "91")

def _void_banner_small():
    return T.bold(T.color("""
  ██╗   ██╗ ██████╗ ██╗██████╗
  ██║   ██║██╔═══██╗██║██╔══██╗
  ╚██╗ ██╔╝██║   ██║██║██║  ██║
   ╚████╔╝ ╚██████╔╝██║██████╔╝
    ╚═══╝   ╚═════╝ ╚═╝╚═════╝ """, "90"))

def _get_term_width():
    try:
        return os.get_terminal_size().columns
    except:
        return 60


# ── Netzwerk-Thread ──────────────────────────────────────────────


def _network_hint_for_host(host: str, exc: Exception) -> str:
    msg = str(exc).lower()
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return ("  Prüfe die IP/Domain. Falls ihr nicht im selben WLAN seid, "
                "nutzt VPN (z. B. Tailscale/Zerotier) oder Port-Forwarding.")

    if ip.is_loopback:
        return "  127.0.0.1 funktioniert nur lokal auf demselben Gerät."

    if ip.is_private or ip.is_link_local:
        return ("  Ziel-IP ist privat (LAN/Carrier-NAT). Verbindung klappt meist nur im gleichen Netzwerk "
                "oder über VPN-Tunnel (Tailscale/Zerotier).")

    if ip in ipaddress.ip_network('100.64.0.0/10'):
        return ("  Ziel-IP liegt in CGNAT-Bereich (100.64.0.0/10). "
                "Direkte Internet-Verbindungen sind dort typischerweise blockiert.")

    if 'timed out' in msg:
        return "  Timeout: Server nicht erreichbar (Firewall, NAT oder falsches Netz)."
    return "  Prüfe Port 7777, Firewall und ob der Server wirklich läuft."

class NetworkHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.send_queue = []
        self.send_lock = threading.Lock()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(8.0)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(None)
        self.connected = True

    def send(self, data: dict):
        if not self.connected:
            return
        try:
            msg = json.dumps(data) + "\n"
            self.sock.sendall(msg.encode())
        except:
            self.connected = False

    def recv_loop(self):
        buffer = ""
        while self.connected:
            try:
                data = self.sock.recv(2048).decode('utf-8', errors='ignore')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            _handle_server_message(msg)
                            render()
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                break
        self.connected = False
        GS.add_message("Verbindung zum Server verloren.", "warn")
        render()


def _handle_server_message(msg: dict):
    mtype = msg.get("type")

    if mtype == "welcome":
        GS.player_id = msg.get("id")
        GS.player_name = msg.get("name", GS.player_name)
        GS.grid_size = msg.get("grid_size", 12)
        GS.phase = "lobby"
        GS.add_message(msg.get("msg", "Verbunden."), "void")

    elif mtype in ("lobby", "lobby_status"):
        GS.lobby_count = msg.get("count", GS.lobby_count)
        GS.lobby_needed = msg.get("needed", GS.lobby_needed)
        GS.add_message(msg.get("msg", ""), "normal")

    elif mtype == "game_start":
        GS.phase = "game"
        GS.game_active = True
        GS.grid_size = msg.get("grid_size", GS.grid_size)
        GS.time_left = msg.get("duration", 180)
        GS.messages = []
        GS.add_message(msg.get("msg", "Spiel gestartet!"), "void")

    elif mtype == "state":
        GS.update_from_state(msg)

    elif mtype == "void_speaks":
        GS.last_void_msg = msg.get("msg", "")
        GS.void_aggression = msg.get("aggression", GS.void_aggression)
        if msg.get("reveal"):
            GS.void_x = msg.get("void_x")
            GS.void_y = msg.get("void_y")
            GS.void_visible = True
            GS.void_reveal_timer = time.time() + 4
        GS.add_message(f"VOID: {GS.last_void_msg}", "void")

    elif mtype == "scan_result":
        style = "warn" if msg.get("void_detected") else "normal"
        GS.add_message(msg.get("msg", ""), style)
        if msg.get("void_detected"):
            GS.void_x = msg.get("void_x")
            GS.void_y = msg.get("void_y")
            GS.void_visible = True
            GS.void_reveal_timer = time.time() + 6

    elif mtype == "signal_collected":
        GS.add_message(msg.get("msg", ""), "good")

    elif mtype == "signal_spawned":
        GS.add_message(msg.get("msg", ""), "warn")
        sx, sy = msg.get("x"), msg.get("y")
        if sx is not None and (sx, sy) not in GS.signals:
            GS.signals.append((sx, sy))

    elif mtype == "player_eliminated":
        GS.add_message(msg.get("msg", ""), "void")

    elif mtype == "ping_signal":
        GS.add_message(msg.get("msg", ""), "warn")

    elif mtype == "rest_result":
        GS.energy = msg.get("energy", GS.energy)
        GS.add_message(f"Regeneriert: +{msg.get('regen', 0)} Energie.", "good")

    elif mtype == "warning":
        GS.add_message(msg.get("msg", ""), "warn")
        GS.time_left = msg.get("remaining", GS.time_left)

    elif mtype == "game_end":
        GS.game_active = False
        GS.phase = "over"
        GS.final_scores = msg.get("scores", [])
        GS.add_message(msg.get("msg", "Spiel vorbei."), "void")

    elif mtype == "disconnect":
        GS.add_message(msg.get("msg", "Spieler getrennt."), "void")

    elif mtype == "rename":
        GS.add_message(f"Fragment_{msg.get('id')} heißt jetzt {msg.get('name')}.", "normal")

    elif mtype == "error":
        GS.add_message(f"FEHLER: {msg.get('msg')}", "warn")


# ── Input-Handler ────────────────────────────────────────────────
def get_char():
    """Liest ein Zeichen ohne Enter. Termux-kompatibel."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

def input_loop(net: NetworkHandler):
    """Verarbeitet Tastatureingaben."""
    global running
    while running:
        try:
            ch = get_char().lower()
        except:
            continue

        if ch == 'q':
            running = False
            break

        if GS.phase == "lobby":
            if ch == 'n':
                T.show_cursor()
                print("\n  Neuer Name: ", end="", flush=True)
                try:
                    name = input().strip()[:16]
                    if name:
                        GS.player_name = name
                        net.send({"type": "set_name", "name": name})
                except:
                    pass
                T.hide_cursor()
                render()
            continue

        if GS.phase == "over":
            continue

        if GS.phase != "game" or not GS.alive:
            continue

        # Bewegung
        if ch == 'w':
            net.send({"type": "move", "dx": 0, "dy": -1})
            GS.y = max(0, GS.y - 1)
        elif ch == 's':
            net.send({"type": "move", "dx": 0, "dy": 1})
            GS.y = min(GS.grid_size - 1, GS.y + 1)
        elif ch == 'a':
            net.send({"type": "move", "dx": -1, "dy": 0})
            GS.x = max(0, GS.x - 1)
        elif ch == 'd':
            net.send({"type": "move", "dx": 1, "dy": 0})
            GS.x = min(GS.grid_size - 1, GS.x + 1)
        elif ch == 'e':
            net.send({"type": "scan"})
            GS.add_message("Scanne Umgebung...", "normal")
        elif ch == 'p':
            net.send({"type": "ping"})
            GS.add_message("Notsignal gesendet! Position enthüllt.", "warn")
        elif ch == 'r':
            net.send({"type": "rest"})
            GS.add_message("Regeneriere Energie...", "normal")

        render()


# ── Einstiegspunkt ───────────────────────────────────────────────
running = True

def main():
    global running

    T.clear()
    print(_void_banner_small())
    print()

    # Server-Adresse
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    else:
        print(T.bold("  Server-IP eingeben (oder Enter für localhost):"), end=" ")
        T.show_cursor()
        raw = input().strip()
        host = raw if raw else "127.0.0.1"

    T.hide_cursor()

    print(T.color(f"\n  Verbinde mit {host}:{7777}...", "96"))

    net = NetworkHandler(host, 7777)
    try:
        net.connect()
    except Exception as e:
        T.show_cursor()
        print(T.color(f"\n  FEHLER: Konnte nicht verbinden. ({e})", "91"))
        print("  Stelle sicher, dass void_server.py läuft.")
        print(_network_hint_for_host(host, e))
        print("\n  Tipp: Für Internet-Multiplayer meist VPN (Tailscale/Zerotier) nutzen.")
        print("  Optional: python3 ~/games/void/game/void_netcheck.py <IP>\n")
        sys.exit(1)

    GS.phase = "connecting"
    render()

    # Netzwerk-Thread starten
    recv_thread = threading.Thread(target=net.recv_loop, daemon=True)
    recv_thread.start()

    # Timer-Thread (aktualisiert Anzeige jede Sekunde)
    def ticker():
        while running and net.connected:
            time.sleep(1)
            if GS.phase == "game" and GS.time_left > 0:
                GS.time_left = max(0, GS.time_left - 1)
            render()
    threading.Thread(target=ticker, daemon=True).start()

    # Input-Loop (blockiert Main-Thread)
    try:
        input_loop(net)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        T.show_cursor()
        T.clear()
        print(T.bold(T.color("\n  Bis zum nächsten Mal. Die VOID erinnert sich.\n", "90")))
        try:
            net.sock.close()
        except:
            pass


if __name__ == "__main__":
    main()
