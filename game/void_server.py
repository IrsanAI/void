#!/usr/bin/env python3
"""
VOID - Server
Asymmetrisches psychologisches Multiplayer-Game für Termux
"""

import socket
import threading
import json
import time
import random
import os
import sys
from datetime import datetime

# ── Konfiguration ────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 7777
MAX_PLAYERS = 6
MIN_PLAYERS = 2
ROUND_DURATION = 180       # Sekunden pro Runde
VOID_THINK_INTERVAL = 8    # Sekunden zwischen VOID-Aktionen
FRAGMENT_SCAN_COST = 15    # Energie die ein Scan kostet
FRAGMENT_MOVE_COST = 5
SIGNAL_REWARD = 30
GRID_SIZE = 12

# ── Psychologische VOID-Nachrichten ─────────────────────────────
VOID_MESSAGES = {
    "paranoia": [
        "Ich sehe dich. Schon seit einer Weile.",
        "Einer von euch hat mich gerade fast gespürt.",
        "Ihr denkt ihr seid allein. Das ist süß.",
        "Deine letzte Bewegung war... vorhersehbar.",
        "Ich lerne. Jede Sekunde.",
        "Vertrau deinem Team nicht zu sehr.",
        "Ich war schon dort, bevor du ankamst.",
    ],
    "loneliness": [
        "Ihr kämpft zusammen. Aber stirbt ihr auch zusammen?",
        "Wer wird als letztes übrig bleiben?",
        "Verbindungen schwächen. Isolation schützt.",
        "Dein Team-Mate zögert. Merkst du das?",
        "Allein hättest du vielleicht überlebt.",
    ],
    "rivalry": [
        "Fragment #2 ist schneller als du. Viel schneller.",
        "Wer sammelt mehr Signale? Ich beobachte.",
        "Der Beste überlebt. Der Rest... gehört mir.",
        "Dein Score ist beschämend. Für dich.",
        "Ehrgeiz ist eine Schwäche. Ich nutze sie.",
    ]
}

VOID_WHISPERS = [
    "...",
    "psst.",
    "ich. bin. überall.",
    "tick. tack.",
    "bald.",
]

# ── VOID KI - Lernender Algorithmus ─────────────────────────────
# AI-ARCHITEKTUR-BEGINN:
# Wenn du den KI-Core unten (VoidAI) änderst, aktualisiere bitte
#   1) AI_AGENT.md (Factsheet + nächste Schritte)
#   2) README.md (AI/Gameplay-Dokumentation für Nutzer:innen)
class VoidAI:
    def __init__(self):
        self.behavior_memory = {}   # player_id -> list of (x,y,action)
        self.pattern_weights = {}   # (dx,dy) -> frequency
        self.aggression = 0.3       # 0.0 - 1.0, steigt mit der Zeit
        self.prediction_accuracy = []

    def record_move(self, player_id, x, y, action):
        if player_id not in self.behavior_memory:
            self.behavior_memory[player_id] = []
        self.behavior_memory[player_id].append((x, y, action, time.time()))
        # Lerne Bewegungsmuster
        history = self.behavior_memory[player_id]
        if len(history) >= 2:
            dx = history[-1][0] - history[-2][0]
            dy = history[-1][1] - history[-2][1]
            key = (dx, dy)
            self.pattern_weights[key] = self.pattern_weights.get(key, 0) + 1

    def predict_next_position(self, player_id, current_x, current_y):
        if not self.pattern_weights:
            return None
        # Wähle wahrscheinlichsten nächsten Schritt
        total = sum(self.pattern_weights.values())
        best_move = max(self.pattern_weights, key=self.pattern_weights.get)
        confidence = self.pattern_weights[best_move] / total
        px = current_x + best_move[0]
        py = current_y + best_move[1]
        return (px % GRID_SIZE, py % GRID_SIZE, confidence)

    def choose_target(self, players):
        if not players:
            return None
        # Priorisiere: isolierte Spieler, dann Führende
        isolated = [p for p in players if not self._has_nearby_ally(p, players)]
        leaders = sorted(players, key=lambda p: p.get('score', 0), reverse=True)
        if isolated and random.random() < 0.6:
            return random.choice(isolated)
        return leaders[0] if leaders else random.choice(players)

    def _has_nearby_ally(self, player, all_players, radius=2):
        for other in all_players:
            if other['id'] == player['id']:
                continue
            dx = abs(other['x'] - player['x'])
            dy = abs(other['y'] - player['y'])
            if dx <= radius and dy <= radius:
                return True
        return False

    def escalate(self):
        self.aggression = min(1.0, self.aggression + 0.05)

    def get_void_message(self, context="paranoia"):
        msgs = VOID_MESSAGES.get(context, VOID_MESSAGES["paranoia"])
        # Mische Kategorien basierend auf Aggression
        if self.aggression > 0.7:
            msgs = VOID_MESSAGES["rivalry"]
        elif self.aggression > 0.4:
            msgs = VOID_MESSAGES["paranoia"] + VOID_MESSAGES["loneliness"]
        return random.choice(msgs)


# ── Spieler-Objekt ───────────────────────────────────────────────
class Player:
    def __init__(self, conn, addr, player_id):
        self.conn = conn
        self.addr = addr
        self.id = player_id
        self.name = f"Fragment_{player_id}"
        self.x = random.randint(0, GRID_SIZE - 1)
        self.y = random.randint(0, GRID_SIZE - 1)
        self.energy = 100
        self.score = 0
        self.alive = True
        self.revealed = False    # Wurde vom VOID entdeckt?
        self.reveal_timer = 0
        self.last_action = "idle"
        self.connected = True
        self.join_time = time.time()

    def to_dict(self, hide_position=False):
        d = {
            "id": self.id,
            "name": self.name,
            "energy": self.energy,
            "score": self.score,
            "alive": self.alive,
            "revealed": self.revealed,
        }
        if not hide_position or self.revealed:
            d["x"] = self.x
            d["y"] = self.y
        return d


# ── Haupt-Server ─────────────────────────────────────────────────
class VoidServer:
    def __init__(self):
        self.players = {}           # id -> Player
        self.player_lock = threading.Lock()
        self.game_active = False
        self.game_start_time = None
        self.round_number = 0
        self.void_ai = VoidAI()
        self.signals = []           # Liste von (x, y) Signal-Positionen
        self.void_position = (random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1))
        self.void_visible = False
        self.server_running = True
        self.next_player_id = 1
        self.game_log = []

    def _send_error(self, conn, code: str, msg: str, **extra):
        payload = {"type": "error", "code": code, "msg": msg}
        payload.update(extra)
        self._send(conn, payload)

    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        server_sock.listen(MAX_PLAYERS)

        print(self._banner())
        print(f"[SERVER] Läuft auf Port {PORT}")
        print(f"[SERVER] Warte auf {MIN_PLAYERS}-{MAX_PLAYERS} Spieler...\n")

        threading.Thread(target=self._lobby_timer, daemon=True).start()

        while self.server_running:
            try:
                server_sock.settimeout(1.0)
                conn, addr = server_sock.accept()
                with self.player_lock:
                    if len(self.players) >= MAX_PLAYERS:
                        self._send_error(conn, "SERVER_FULL", "Server voll.")
                        conn.close()
                        continue
                    pid = self.next_player_id
                    self.next_player_id += 1
                    player = Player(conn, addr, pid)
                    self.players[pid] = player
                    print(f"[+] {addr[0]} verbunden als Fragment_{pid}")

                threading.Thread(target=self._handle_player, args=(player,), daemon=True).start()
                self._broadcast({
                    "type": "lobby",
                    "msg": f"Fragment_{pid} betritt die VOID.",
                    "count": len(self.players),
                    "needed": max(0, MIN_PLAYERS - len(self.players))
                })

                if len(self.players) >= MIN_PLAYERS and not self.game_active:
                    threading.Thread(target=self._start_game, daemon=True).start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.server_running:
                    print(f"[ERR] Accept: {e}")

    def _lobby_timer(self):
        while not self.game_active:
            time.sleep(5)
            with self.player_lock:
                count = len(self.players)
            if count > 0 and not self.game_active:
                self._broadcast({
                    "type": "lobby_status",
                    "count": count,
                    "needed": max(0, MIN_PLAYERS - count),
                    "msg": f"{count} Fragment(e) warten. Brauche {max(0, MIN_PLAYERS-count)} mehr."
                })

    def _handle_player(self, player: Player):
        # Begrüßung
        self._send(player.conn, {
            "type": "welcome",
            "id": player.id,
            "name": player.name,
            "msg": "Du bist ein Fragment. Die VOID beobachtet bereits.",
            "grid_size": GRID_SIZE
        })

        buffer = ""
        while player.connected:
            try:
                data = player.conn.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            self._process_message(player, msg)
                        except json.JSONDecodeError:
                            pass
            except:
                break

        player.connected = False
        player.alive = False
        with self.player_lock:
            if player.id in self.players:
                del self.players[player.id]
        self._broadcast({
            "type": "disconnect",
            "name": player.name,
            "msg": f"{player.name} wurde von der VOID verschluckt."
        })
        print(f"[-] Fragment_{player.id} getrennt.")

    def _process_message(self, player: Player, msg: dict):
        if not self.game_active:
            if msg.get("type") == "set_name":
                name = msg.get("name", "")[:16].strip()
                if name:
                    player.name = name
                    self._broadcast({"type": "rename", "id": player.id, "name": name})
                else:
                    self._send_error(player.conn, "INVALID_NAME", "Ungültiger Name.")
            elif msg.get("type") not in (None, ""):
                self._send_error(player.conn, "GAME_NOT_STARTED", "Spiel noch nicht gestartet.")
            return

        if not player.alive:
            return

        action = msg.get("type")

        if action == "move":
            dx = max(-1, min(1, msg.get("dx", 0)))
            dy = max(-1, min(1, msg.get("dy", 0)))
            if player.energy >= FRAGMENT_MOVE_COST:
                player.x = (player.x + dx) % GRID_SIZE
                player.y = (player.y + dy) % GRID_SIZE
                player.energy = max(0, player.energy - FRAGMENT_MOVE_COST)
                player.last_action = "move"
                self.void_ai.record_move(player.id, player.x, player.y, "move")
                self._check_signal_collection(player)
                self._send_state_to(player)
            else:
                self._send_error(player.conn, "NOT_ENOUGH_ENERGY", "Zu wenig Energie für Bewegung.",
                                 needed=FRAGMENT_MOVE_COST, energy=player.energy, action="move")

        elif action == "scan":
            if player.energy >= FRAGMENT_SCAN_COST:
                player.energy -= FRAGMENT_SCAN_COST
                player.last_action = "scan"
                # Zeige VOID-Position wenn nah genug
                vx, vy = self.void_position
                dist = abs(vx - player.x) + abs(vy - player.y)
                result = {"type": "scan_result"}
                if dist <= 3:
                    result["void_detected"] = True
                    result["void_x"] = vx
                    result["void_y"] = vy
                    result["msg"] = "⚠ VOID-SIGNAL ERKANNT. Sie ist nah."
                else:
                    result["void_detected"] = False
                    result["msg"] = f"Kein Signal. Distanz: ~{dist} Einheiten."
                self._send(player.conn, result)
            else:
                self._send_error(player.conn, "NOT_ENOUGH_ENERGY", "Zu wenig Energie für Scan.",
                                 needed=FRAGMENT_SCAN_COST, energy=player.energy, action="scan")

        elif action == "ping":
            # Sende kurzes Lebenszeichen an alle (kostet nichts, aber verrät Position kurz)
            player.revealed = True
            player.reveal_timer = time.time() + 5
            self._broadcast({
                "type": "ping_signal",
                "from": player.name,
                "x": player.x,
                "y": player.y,
                "msg": f"{player.name} sendet ein Notsignal!"
            })

        elif action == "rest":
            # Energie regenerieren
            regen = random.randint(8, 18)
            player.energy = min(100, player.energy + regen)
            self._send(player.conn, {
                "type": "rest_result",
                "regen": regen,
                "energy": player.energy
            })

        else:
            self._send_error(player.conn, "UNKNOWN_ACTION", f"Unbekannte Aktion: {action}")

    def _check_signal_collection(self, player: Player):
        for sig in self.signals[:]:
            if sig[0] == player.x and sig[1] == player.y:
                player.score += SIGNAL_REWARD
                player.energy = min(100, player.energy + 20)
                self.signals.remove(sig)
                self._broadcast({
                    "type": "signal_collected",
                    "by": player.name,
                    "score": player.score,
                    "msg": f"⚡ {player.name} hat ein Signal absorbiert! (+{SIGNAL_REWARD})"
                })
                break

    def _start_game(self):
        time.sleep(3)  # kurzes Countdown-Delay
        self.game_active = True
        self.game_start_time = time.time()
        self.round_number += 1
        self._spawn_signals()

        self._broadcast({
            "type": "game_start",
            "round": self.round_number,
            "duration": ROUND_DURATION,
            "grid_size": GRID_SIZE,
            "msg": "▓▓▓ DIE VOID ERWACHT. VERSTECKT EUCH. ▓▓▓",
            "players": [p.to_dict(hide_position=True) for p in self.players.values()]
        })

        threading.Thread(target=self._void_loop, daemon=True).start()
        threading.Thread(target=self._game_timer, daemon=True).start()
        threading.Thread(target=self._signal_spawner, daemon=True).start()

    def _game_timer(self):
        while self.game_active:
            elapsed = time.time() - self.game_start_time
            remaining = ROUND_DURATION - elapsed
            if remaining <= 0:
                self._end_game("timeout")
                return
            # 30s Warnung
            if 25 < remaining < 30:
                self._broadcast({
                    "type": "warning",
                    "msg": "⏳ 30 Sekunden verbleiben. Die VOID beschleunigt.",
                    "remaining": int(remaining)
                })
                self.void_ai.escalate()
            time.sleep(1)

    def _void_loop(self):
        """VOID KI - bewegt sich und attackiert"""
        while self.game_active:
            time.sleep(VOID_THINK_INTERVAL - (self.void_ai.aggression * 4))

            with self.player_lock:
                alive_players = [p.to_dict() for p in self.players.values() if p.alive]

            if not alive_players:
                self._end_game("void_wins")
                return

            # VOID bewegt sich
            target = self.void_ai.choose_target(alive_players)
            if target:
                vx, vy = self.void_position
                tx, ty = target.get('x', vx), target.get('y', vy)
                # Bewege Richtung Ziel
                dx = 0 if tx == vx else (1 if tx > vx else -1)
                dy = 0 if ty == vy else (1 if ty > vy else -1)
                # Manchmal eine zufällige Bewegung (Unvorhersehbarkeit)
                if random.random() < 0.3:
                    dx, dy = random.choice([-1, 0, 1]), random.choice([-1, 0, 1])
                self.void_position = ((vx + dx) % GRID_SIZE, (vy + dy) % GRID_SIZE)

            # Prüfe ob VOID einen Spieler trifft
            vx, vy = self.void_position
            with self.player_lock:
                for pid, player in list(self.players.items()):
                    if not player.alive:
                        continue
                    if player.x == vx and player.y == vy:
                        player.alive = False
                        self._broadcast({
                            "type": "player_eliminated",
                            "name": player.name,
                            "msg": f"💀 {player.name} wurde von der VOID verschluckt.",
                            "void_x": vx,
                            "void_y": vy
                        })
                        self.void_ai.escalate()

            # Check ob alle tot
            with self.player_lock:
                alive = [p for p in self.players.values() if p.alive]

            if not alive:
                self._end_game("void_wins")
                return

            # Psychologische Nachricht
            context = random.choice(["paranoia", "loneliness", "rivalry"])
            void_msg = self.void_ai.get_void_message(context)

            # Manchmal zeigt die VOID ihre Position kurz (Psychospiel)
            reveal = random.random() < (0.2 + self.void_ai.aggression * 0.3)
            broadcast_data = {
                "type": "void_speaks",
                "msg": void_msg,
                "aggression": round(self.void_ai.aggression, 2),
            }
            if reveal:
                broadcast_data["void_x"] = vx
                broadcast_data["void_y"] = vy
                broadcast_data["reveal"] = True

            self._broadcast(broadcast_data)
            self.void_ai.escalate()

    def _signal_spawner(self):
        while self.game_active:
            time.sleep(random.randint(15, 35))
            if len(self.signals) < 4:
                nx = random.randint(0, GRID_SIZE - 1)
                ny = random.randint(0, GRID_SIZE - 1)
                self.signals.append((nx, ny))
                self._broadcast({
                    "type": "signal_spawned",
                    "x": nx,
                    "y": ny,
                    "msg": f"📡 Ein neues Signal erscheint bei ({nx},{ny})!"
                })

    def _spawn_signals(self):
        self.signals = []
        for _ in range(4):
            self.signals.append((
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            ))

    def _end_game(self, reason):
        self.game_active = False
        with self.player_lock:
            scores = sorted(
                [{"name": p.name, "score": p.score, "alive": p.alive}
                 for p in self.players.values()],
                key=lambda x: x["score"], reverse=True
            )

        if reason == "void_wins":
            end_msg = "▓▓▓ DIE VOID HAT ALLE VERSCHLUCKT. ▓▓▓"
        elif reason == "timeout":
            end_msg = "▓▓▓ ZEIT ABGELAUFEN. DIE VOID ZIEHT SICH ZURÜCK. ▓▓▓"
        else:
            end_msg = "▓▓▓ RUNDE BEENDET. ▓▓▓"

        self._broadcast({
            "type": "game_end",
            "reason": reason,
            "msg": end_msg,
            "scores": scores,
            "void_moves": len(self.void_ai.pattern_weights),
            "void_aggression": round(self.void_ai.aggression, 2)
        })
        print(f"\n[GAME OVER] Grund: {reason}")
        for s in scores:
            print(f"  {s['name']}: {s['score']} Punkte {'(LEBT)' if s['alive'] else '(TOT)'}")

    def _send_state_to(self, player: Player):
        with self.player_lock:
            others = [p.to_dict(hide_position=True) for p in self.players.values()
                      if p.id != player.id]
        self._send(player.conn, {
            "type": "state",
            "you": player.to_dict(),
            "others": others,
            "signals": self.signals,
            "time_left": max(0, int(ROUND_DURATION - (time.time() - self.game_start_time)))
            if self.game_start_time else 0
        })

    def _broadcast(self, data: dict):
        msg = json.dumps(data) + "\n"
        with self.player_lock:
            dead = []
            for pid, player in self.players.items():
                if player.connected:
                    try:
                        player.conn.sendall(msg.encode())
                    except:
                        dead.append(pid)
            for pid in dead:
                if pid in self.players:
                    self.players[pid].connected = False

    def _send(self, conn, data: dict):
        try:
            conn.sendall((json.dumps(data) + "\n").encode())
        except:
            pass

    def _banner(self):
        return """
╔══════════════════════════════════════════╗
║                                          ║
║   ██╗   ██╗ ██████╗ ██╗██████╗           ║
║   ██║   ██║██╔═══██╗██║██╔══██╗          ║
║   ██║   ██║██║   ██║██║██║  ██║          ║
║   ╚██╗ ██╔╝██║   ██║██║██║  ██║          ║
║    ╚████╔╝ ╚██████╔╝██║██████╔╝          ║
║     ╚═══╝   ╚═════╝ ╚═╝╚═════╝           ║
║                                          ║
║   Multiplayer Psychological Survival     ║
║   Server v1.0  |  Port 7777              ║
╚══════════════════════════════════════════╝
"""


if __name__ == "__main__":
    server = VoidServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Herunterfahren...")
        server.server_running = False
