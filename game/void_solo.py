#!/usr/bin/env python3
"""
VOID — Solo Mode
Spiele allein gegen die VOID-KI + Bot-Fragmente.
Kein Server nötig. Läuft komplett lokal in Termux.
"""

import time
import random
import sys
import os
import tty
import termios
import threading
import json

# IrsanAI Layout Framework
try:
    from void_layout import get_layout, NARROW, NORMAL, WIDE
    _LAYOUT_AVAILABLE = True
except ImportError:
    _LAYOUT_AVAILABLE = False

# Sound Engine
try:
    from void_sound import get_sound
    _SOUND_AVAILABLE = True
except ImportError:
    _SOUND_AVAILABLE = False
    def get_sound():
        class _Dummy:
            def play(self, *a): pass
            def start_heartbeat(self, *a): pass
            def set_bpm(self, *a): pass
            def stop_heartbeat(self): pass
            def get_visualizer(self): return ""
            def stop(self): pass
        return _Dummy()

# ── Terminal ─────────────────────────────────────────────────────
class T:
    @staticmethod
    def clear():     print("\033[2J\033[H", end="", flush=True)
    @staticmethod
    def hide():      print("\033[?25l", end="", flush=True)
    @staticmethod
    def show():      print("\033[?25h", end="", flush=True)
    @staticmethod
    def bold(s):     return f"\033[1m{s}\033[0m"
    @staticmethod
    def dim(s):      return f"\033[2m{s}\033[0m"
    @staticmethod
    def red(s):      return f"\033[91m{s}\033[0m"
    @staticmethod
    def green(s):    return f"\033[92m{s}\033[0m"
    @staticmethod
    def yellow(s):   return f"\033[93m{s}\033[0m"
    @staticmethod
    def cyan(s):     return f"\033[96m{s}\033[0m"
    @staticmethod
    def gray(s):     return f"\033[90m{s}\033[0m"
    @staticmethod
    def magenta(s):  return f"\033[95m{s}\033[0m"
    @staticmethod
    def white(s):    return f"\033[97m{s}\033[0m"

# ── Konfiguration ────────────────────────────────────────────────
# ── Konfiguration ────────────────────────────────────────────────
ROUND_TIME  = 180
BOT_COUNT   = 3
SCAN_COST   = 15
MOVE_COST   = 5
SIG_REWARD  = 30
VOID_TICK   = 7.0

# GRID wird vom Layout-Framework berechnet — Fallback: 9
def _get_grid():
    if _LAYOUT_AVAILABLE:
        return get_layout().grid_size
    return 9

GRID = _get_grid()

VOID_MSGS = {
    "paranoia": [
        "Ich sehe dich. Schon seit einer Weile.",
        "Du glaubst du weißt wo ich bin. Ich weiß es besser.",
        "Deine letzte Bewegung war... vorhersehbar.",
        "Ich lerne. Jede Sekunde lerne ich.",
        "Ich war dort, bevor du ankamst.",
    ],
    "loneliness": [
        "Du bist allein hier. Das weißt du, oder?",
        "Die anderen Fragmente helfen dir nicht.",
        "Isolation schützt dich. Oder macht sie dich schwächer?",
        "Vertrau niemandem. Nicht mal dir selbst.",
    ],
    "rivalry": [
        "Bot_2 ist schneller als du. Viel schneller.",
        "Wer sammelt mehr? Ich beobachte sehr genau.",
        "Der Beste überlebt. Bist du der Beste?",
        "Dein Score reicht nicht. Noch nicht.",
    ],
    "whisper": [
        "...", "psst.", "bald.", "tick. tack.", "ich bin hier.",
    ]
}

DIFFICULTY = {
    "easy":   {"speed": 10.0, "aggression_start": 0.1, "aggression_step": 0.03},
    "normal": {"speed":  7.0, "aggression_start": 0.3, "aggression_step": 0.05},
    "hard":   {"speed":  4.5, "aggression_start": 0.5, "aggression_step": 0.08},
}

# ── Bot-Fragment KI ───────────────────────────────────────────────
class BotFragment:
    def __init__(self, bot_id, grid):
        self.id    = bot_id
        self.name  = f"Bot_{bot_id}"
        self.x     = random.randint(0, grid - 1)
        self.y     = random.randint(0, grid - 1)
        self.score = 0
        self.energy= 100
        self.alive = True
        self.g     = grid
        # Persönlichkeit bestimmt Strategie
        self.personality = random.choice(["hunter", "collector", "coward"])

    def tick(self, signals, void_x, void_y, void_visible):
        if not self.alive:
            return
        self.energy = min(100, self.energy + 3)   # Bots regen automatisch

        # Flucht wenn VOID sichtbar und nah
        if void_visible:
            dist = abs(void_x - self.x) + abs(void_y - self.y)
            if dist <= 3 and self.personality != "hunter":
                self._flee(void_x, void_y)
                return

        if self.personality == "collector" and signals:
            self._move_toward_nearest(signals)
        elif self.personality == "hunter":
            # Jagt andere Bots um Scores zu konkurrieren (dramatischer Effekt)
            self._random_walk()
        else:
            self._random_walk()

        # Signal einsammeln
        for sig in signals[:]:
            if sig[0] == self.x and sig[1] == self.y:
                self.score += SIG_REWARD
                signals.remove(sig)
                break

    def _flee(self, vx, vy):
        dx = 0 if self.x == vx else (1 if self.x > vx else -1)
        dy = 0 if self.y == vy else (1 if self.y > vy else -1)
        self.x = (self.x + dx) % self.g
        self.y = (self.y + dy) % self.g

    def _move_toward_nearest(self, signals):
        nearest = min(signals, key=lambda s: abs(s[0]-self.x) + abs(s[1]-self.y))
        dx = 0 if nearest[0] == self.x else (1 if nearest[0] > self.x else -1)
        dy = 0 if nearest[1] == self.y else (1 if nearest[1] > self.y else -1)
        # Bewege nur eine Achse pro Tick
        if random.random() < 0.5 and dx != 0:
            self.x = (self.x + dx) % self.g
        elif dy != 0:
            self.y = (self.y + dy) % self.g

    def _random_walk(self):
        dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0),(0,0)])
        self.x = (self.x + dx) % self.g
        self.y = (self.y + dy) % self.g


# ── VOID KI (lokale Version) ──────────────────────────────────────
class VoidAI:
    def __init__(self, diff_cfg):
        self.x           = random.randint(0, GRID-1)
        self.y           = random.randint(0, GRID-1)
        self.aggression  = diff_cfg["aggression_start"]
        self.agg_step    = diff_cfg["aggression_step"]
        self.speed       = diff_cfg["speed"]
        self.move_hist   = {}    # pattern learning
        self.visible     = False
        self.reveal_until= 0

    def record(self, px, py):
        # Lerne letzten Schritt
        key = (px % 3, py % 3)
        self.move_hist[key] = self.move_hist.get(key, 0) + 1

    def move_toward(self, tx, ty):
        dx = 0 if tx == self.x else (1 if tx > self.x else -1)
        dy = 0 if ty == self.y else (1 if ty > self.y else -1)
        if random.random() < 0.25:   # Unvorhersehbarkeit
            dx, dy = random.choice([-1,0,1]), random.choice([-1,0,1])
        self.x = (self.x + dx) % GRID
        self.y = (self.y + dy) % GRID

    def choose_msg(self):
        if self.aggression > 0.7:
            cat = "rivalry"
        elif self.aggression > 0.45:
            cat = "paranoia"
        elif random.random() < 0.25:
            cat = "whisper"
        else:
            cat = random.choice(["paranoia","loneliness"])
        return random.choice(VOID_MSGS[cat])

    def escalate(self):
        self.aggression = min(1.0, self.aggression + self.agg_step)
        self.speed      = max(1.5, self.speed - 0.3)

    def reveal_self(self, duration=4):
        self.visible = True
        self.reveal_until = time.time() + duration

    def update_visibility(self):
        if self.visible and time.time() > self.reveal_until:
            self.visible = False


# ── Haupt-Spielzustand ────────────────────────────────────────────
class SoloGame:
    def __init__(self, difficulty="normal"):
        cfg           = DIFFICULTY[difficulty]
        # ── Layout Framework ──
        self.L        = get_layout() if _LAYOUT_AVAILABLE else None
        self.GRID     = self.L.grid_size if self.L else 9
        self.void     = VoidAI(cfg)
        self.bots     = [BotFragment(i+1, self.GRID) for i in range(BOT_COUNT)]
        self.px       = random.randint(0, self.GRID-1)
        self.py       = random.randint(0, self.GRID-1)
        self.energy   = 100
        self.score    = 0
        self.alive    = True
        self.start    = time.time()
        self.signals  = self._spawn_signals(4)
        self.messages = []
        self.last_void_msg   = ""
        self.running  = True
        self.difficulty      = difficulty
        self.render_lock     = threading.Lock()
        self.highscores      = self._load_scores()
        self.snd             = get_sound()
        # Wire resize → rerender
        if self.L:
            self.L.on_resize(self._on_resize)

    # ── Layout Resize Callback ──
    def _on_resize(self):
        """Wird automatisch aufgerufen wenn Terminal-Größe sich ändert."""
        if self.L:
            new_grid = self.L.grid_size
            if new_grid != self.GRID:
                self.GRID = new_grid
                # Spieler-Position innerhalb neuer Grid-Grenzen halten
                self.px = min(self.px, self.GRID - 1)
                self.py = min(self.py, self.GRID - 1)
        self._render()

    # ── Signale ──
    def _spawn_signals(self, n=2):
        g = self.GRID if hasattr(self, 'GRID') else GRID
        return [(random.randint(0, g-1), random.randint(0, g-1)) for _ in range(n)]

    def time_left(self):
        return max(0, int(ROUND_TIME - (time.time() - self.start)))

    def add_msg(self, text, style="normal"):
        self.messages.append((time.strftime("%H:%M:%S"), text, style))
        if len(self.messages) > 7:
            self.messages.pop(0)

    # ── Highscore persist ──
    def _load_scores(self):
        path = os.path.expanduser("~/.void_scores.json")
        try:
            with open(path) as f:
                return json.load(f)
        except:
            return []

    def _save_score(self, score, survived, difficulty):
        path = os.path.expanduser("~/.void_scores.json")
        entry = {
            "score": score,
            "survived": survived,
            "difficulty": difficulty,
            "date": time.strftime("%Y-%m-%d %H:%M")
        }
        self.highscores.append(entry)
        self.highscores = sorted(self.highscores, key=lambda x: x["score"], reverse=True)[:10]
        try:
            with open(path, "w") as f:
                json.dump(self.highscores, f)
        except:
            pass

    # ── Spielschleife Threads ──
    def start_game(self):
        T.hide()
        self.snd.play("game_start")
        self.snd.start_heartbeat(44)
        threading.Thread(target=self._void_thread, daemon=True).start()
        threading.Thread(target=self._bot_thread, daemon=True).start()
        threading.Thread(target=self._signal_thread, daemon=True).start()
        threading.Thread(target=self._timer_thread, daemon=True).start()
        self._render()
        self._input_loop()

    def _void_thread(self):
        while self.running and self.alive:
            time.sleep(self.void.speed)
            if not self.running:
                break

            # Wähle Ziel: Spieler oder Bot
            targets = [(self.px, self.py, "player")]
            for b in self.bots:
                if b.alive:
                    targets.append((b.x, b.y, b.name))

            # Mit steigender Aggression: lieber den Spieler jagen
            if random.random() < self.void.aggression:
                tx, ty, tname = self.px, self.py, "player"
            else:
                tx, ty, tname = random.choice(targets)

            self.void.record(self.px, self.py)
            self.void.move_toward(tx, ty)
            self.void.update_visibility()
            self.snd.play("void_move")

            # Treffer prüfen
            if self.void.x == self.px and self.void.y == self.py and self.alive:
                self.alive = False
                self.snd.play("void_attack")
                self.snd.stop_heartbeat()
                self.add_msg("💀 DIE VOID HAT DICH ERWISCHT.", "void")
                self._render()
                time.sleep(2)
                self._end_game(survived=False)
                return

            for bot in self.bots:
                if bot.alive and bot.x == self.void.x and bot.y == self.void.y:
                    bot.alive = False
                    self.add_msg(f"💀 {bot.name} wurde verschluckt.", "void")

            # Psychologische Nachricht + passender Sound
            msg = self.void.choose_msg()
            self.last_void_msg = msg
            self.add_msg(f"VOID: {msg}", "void")

            # Sound-Emotion zur VOID-Nachricht
            if self.void.aggression > 0.7:
                self.snd.play("rivalry")
            elif self.void.aggression > 0.4:
                self.snd.play("paranoia")
            else:
                self.snd.play("loneliness")

            # BPM eskaliert mit Aggression
            new_bpm = 44 + self.void.aggression * 60
            self.snd.set_bpm(new_bpm)

            # Manchmal zeigt sich die VOID
            if random.random() < (0.15 + self.void.aggression * 0.25):
                self.void.reveal_self(3 + self.void.aggression * 2)
                self.add_msg("⚠ VOID-POSITION KURZ SICHTBAR!", "warn")

            self.void.escalate()
            self._render()

    def _bot_thread(self):
        while self.running:
            time.sleep(2.5)
            for bot in self.bots:
                vx = self.void.x if self.void.visible else -99
                vy = self.void.y if self.void.visible else -99
                bot.tick(self.signals, vx, vy, self.void.visible)
            self._render()

    def _signal_thread(self):
        while self.running:
            time.sleep(random.randint(18, 30))
            if len(self.signals) < 5:
                new = self._spawn_signals(1)
                self.signals.extend(new)
                self.add_msg(f"📡 Signal bei ({new[0][0]},{new[0][1]}) aufgetaucht!", "warn")
                self._render()

    def _timer_thread(self):
        while self.running and self.alive:
            time.sleep(1)
            tl = self.time_left()
            if tl == 30:
                self.add_msg("⏳ 30 Sekunden! VOID beschleunigt.", "warn")
                self.snd.set_bpm(100)
                self.void.escalate()
                self.void.escalate()
                self._render()
            if tl <= 0:
                self._end_game(survived=True)
                return

    # ── Input ────────────────────────────────────────────────────
    def _input_loop(self):
        while self.running:
            try:
                ch = self._getch().lower()
            except:
                continue

            if ch == 'q':
                self.running = False
                T.show()
                T.clear()
                sys.exit(0)

            if not self.alive or not self.running:
                continue

            if ch == 'w':
                self.py = (self.py - 1) % self.GRID
                self.energy = max(0, self.energy - MOVE_COST)
            elif ch == 's':
                self.py = (self.py + 1) % self.GRID
                self.energy = max(0, self.energy - MOVE_COST)
            elif ch == 'a':
                self.px = (self.px - 1) % self.GRID
                self.energy = max(0, self.energy - MOVE_COST)
            elif ch == 'd':
                self.px = (self.px + 1) % self.GRID
                self.energy = max(0, self.energy - MOVE_COST)
            elif ch == 'e':
                self._scan()
            elif ch == 'r':
                regen = random.randint(10, 20)
                self.energy = min(100, self.energy + regen)
                self.add_msg(f"Regeneriert: +{regen} Energie.", "good")
            elif ch == 'h':
                self._show_highscores()
                continue

            self.void.record(self.px, self.py)
            self._collect_signals()
            self._render()

    def _scan(self):
        if self.energy < SCAN_COST:
            self.add_msg("Zu wenig Energie zum Scannen!", "warn")
            return
        self.energy -= SCAN_COST
        self.snd.play("scan")
        dist = abs(self.void.x - self.px) + abs(self.void.y - self.py)
        if dist <= 3:
            self.void.reveal_self(5)
            self.snd.play("paranoia")
            self.add_msg(f"⚠ VOID DETEKTIERT! Distanz: {dist}. Position enthüllt.", "warn")
        elif dist <= 6:
            self.add_msg(f"Signal schwach. Distanz ~{dist}. Richtung unklar.", "normal")
        else:
            self.add_msg(f"Kein Signal. Distanz >{dist}. Gebiet sicher.", "good")

    def _collect_signals(self):
        for sig in self.signals[:]:
            if sig[0] == self.px and sig[1] == self.py:
                self.score += SIG_REWARD
                self.energy = min(100, self.energy + 15)
                self.signals.remove(sig)
                self.snd.play("signal_collect")
                self.add_msg(f"⚡ Signal absorbiert! +{SIG_REWARD} | Score: {self.score}", "good")
                break

    # ── Render ───────────────────────────────────────────────────
    def _render(self):
        with self.render_lock:
            T.clear()
            self._draw_header()
            print()
            self._draw_grid()
            print()
            self._draw_bots()
            print()
            # Sound-Visualizer
            viz = self.snd.get_visualizer()
            if viz:
                print(viz)
                print()
            self._draw_messages()
            print()
            self._draw_controls()

    def _draw_header(self):
        tl = self.time_left()
        time_s = T.red(f"⏱{tl}s") if tl <= 30 else T.yellow(f"⏱{tl}s")
        diff_c = {"easy": T.green, "normal": T.yellow, "hard": T.red}[self.difficulty]
        agg_pct = int(self.void.aggression * 10)
        agg_bar = T.red("█" * agg_pct) + T.gray("░" * (10 - agg_pct))
        en_pct  = int(self.energy / 10)
        en_col  = "92" if self.energy > 60 else ("93" if self.energy > 30 else "91")
        en_bar  = f"\033[{en_col}m" + "█" * en_pct + "\033[90m" + "░" * (10-en_pct) + "\033[0m"
        status  = T.green("●") if self.alive else T.red("✖")

        print(f" {status} {T.bold(diff_c(self.difficulty[:3].upper()))}  {time_s}  {T.cyan('◈'+str(self.score))}")
        print(f" {T.red('AGG')} [{agg_bar}]  {T.cyan('EN')} [{en_bar}]{self.energy}")
        if self.last_void_msg:
            msg = self.last_void_msg[:38]  # Truncate für schmale Screens
            print(f" {T.red('▶')} {T.dim(msg)}")

    def _draw_grid(self):
        grid = [[T.gray('·')] * self.GRID for _ in range(self.GRID)]

        for sx, sy in self.signals:
            if 0 <= sx < self.GRID and 0 <= sy < self.GRID:
                grid[sy][sx] = T.yellow('◈')

        if self.void.visible:
            vx, vy = self.void.x, self.void.y
            if 0 <= vx < self.GRID and 0 <= vy < self.GRID:
                grid[vy][vx] = T.bold(T.red('▓'))

        bot_colors = ["96", "95", "94"]
        for i, bot in enumerate(self.bots):
            if bot.alive and 0 <= bot.x < self.GRID and 0 <= bot.y < self.GRID:
                grid[bot.y][bot.x] = f"\033[{bot_colors[i%3]}m○\033[0m"
            elif not bot.alive and 0 <= bot.x < self.GRID and 0 <= bot.y < self.GRID:
                grid[bot.y][bot.x] = T.gray('×')

        if self.alive and 0 <= self.px < self.GRID and 0 <= self.py < self.GRID:
            grid[self.py][self.px] = T.bold(T.green('◉'))

        # Kompaktes Grid — kein Leerzeichen zwischen Zellen
        print(T.gray(" ┌" + "─" * (GRID*2) + "┐"))
        for row in grid:
            line = T.gray(" │")
            for cell in row:
                line += cell + " "
            line = line.rstrip(" ") + T.gray("│")
            print(line)
        print(T.gray(" └" + "─" * (GRID*2) + "┘"))
        print(f" {T.green('◉')}Du {T.cyan('○')}Bot {T.yellow('◈')}Sig {T.red('▓')}VOID")

    def _draw_bots(self):
        alive = [b for b in self.bots if b.alive]
        dead  = [b for b in self.bots if not b.alive]
        parts = []
        for b in alive:
            parts.append(f"{T.cyan('●')}{b.name[:5]} {T.gray(str(b.score))}")
        for b in dead:
            parts.append(T.gray(f"×{b.name[:5]}"))
        print(" " + "  ".join(parts))

    def _draw_messages(self):
        if not self.messages:
            return
        print(T.gray(" ─────────────────────────────"))
        for ts, msg, style in self.messages[-3:]:
            short_ts = ts[6:]  # nur HH:MM:SS → MM:SS
            msg_cut = msg[:36]
            if style == "void":
                print(f" {T.dim(short_ts)} {T.red(msg_cut)}")
            elif style == "good":
                print(f" {T.dim(short_ts)} {T.green(msg_cut)}")
            elif style == "warn":
                print(f" {T.dim(short_ts)} {T.yellow(msg_cut)}")
            else:
                print(f" {T.dim(short_ts)} {T.dim(msg_cut)}")

    def _draw_controls(self):
        print(T.gray(" ─────────────────────────────"))
        print(f" {T.bold('W')}↑ {T.bold('S')}↓ {T.bold('A')}← {T.bold('D')}→  "
              f"{T.bold('E')}Scan  {T.bold('R')}Rast  "
              f"{T.bold('H')}Top  {T.bold('Q')}Exit")

    def _show_highscores(self):
        T.clear()
        print()
        print(T.bold(T.cyan("  ── VOID HIGHSCORES ─────────────────────")))
        if not self.highscores:
            print(T.dim("  Noch keine Einträge."))
        for i, e in enumerate(self.highscores[:10]):
            medal = ["🥇","🥈","🥉"][i] if i < 3 else "  "
            surv  = T.green("✓") if e["survived"] else T.red("✗")
            print(f"  {medal} {T.bold(str(e['score']))}  {e['difficulty']}  {surv}  {T.dim(e['date'])}")
        print()
        print(T.dim("  [Beliebige Taste zum Weiterspielen]"))
        self._getch()
        self._render()

    def _end_game(self, survived: bool):
        self.running = False
        self.snd.stop_heartbeat()
        if survived:
            self.snd.play("signal_collect")
        else:
            self.snd.play("player_dead")
        self._save_score(self.score, survived, self.difficulty)
        T.clear()
        print()
        if survived:
            print(T.bold(T.green("  ╔══════════════════════════════════╗")))
            print(T.bold(T.green("  ║   DU HAST ÜBERLEBT.             ║")))
            print(T.bold(T.green("  ╚══════════════════════════════════╝")))
        else:
            print(T.bold(T.red("  ╔══════════════════════════════════╗")))
            print(T.bold(T.red("  ║   DIE VOID HAT DICH.            ║")))
            print(T.bold(T.red("  ╚══════════════════════════════════╝")))
        print()
        print(f"  Score:      {T.bold(T.cyan(str(self.score)))}")
        print(f"  Schwierigkeit: {self.difficulty}")
        print(f"  VOID-Aggression: {round(self.void.aggression, 2)}")
        print()
        print(T.bold("  FRAGMENT-ERGEBNISSE:"))
        all_scores = [{"name": "Du", "score": self.score, "alive": self.alive}]
        for b in self.bots:
            all_scores.append({"name": b.name, "score": b.score, "alive": b.alive})
        all_scores.sort(key=lambda x: x["score"], reverse=True)
        for i, e in enumerate(all_scores):
            medal = ["🥇","🥈","🥉"][i] if i < 3 else "  "
            alv   = T.green("(lebt)") if e["alive"] else T.gray("(tot)")
            name  = T.bold(T.green(e["name"])) if e["name"] == "Du" else e["name"]
            print(f"  {medal} {name}  {T.cyan('◈ '+str(e['score']))}  {alv}")
        print()
        print(T.dim("  Score gespeichert. [H] Highscores  [Q] Beenden"))
        while True:
            try:
                ch = self._getch().lower()
                if ch == 'h':
                    self._show_highscores()
                elif ch == 'q':
                    break
            except:
                break
        T.show()
        T.clear()

    @staticmethod
    def _bar(ratio, width, fill_code, empty_code):
        filled = int(min(1.0, max(0.0, ratio)) * width)
        return (f"\033[{fill_code}m" + "█" * filled +
                f"\033[{empty_code}m" + "░" * (width - filled) + "\033[0m")

    @staticmethod
    def _getch():
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ── Startmenü ────────────────────────────────────────────────────
def menu():
    T.clear()
    print(T.bold(T.gray("""
  ██╗   ██╗ ██████╗ ██╗██████╗
  ██║   ██║██╔═══██╗██║██╔══██╗
  ╚██╗ ██╔╝██║   ██║██║██║  ██║
   ╚████╔╝ ╚██████╔╝██║██████╔╝
    ╚═══╝   ╚═════╝ ╚═╝╚═════╝""")))
    print()
    print(T.bold("  SOLO MODE"))
    print(T.dim("  Du gegen die VOID. + 3 Bot-Fragmente."))
    print()
    print(f"  {T.green('[1]')} Einfach")
    print(f"  {T.yellow('[2]')} Normal")
    print(f"  {T.red('[3]')} Schwer")
    print(f"  {T.gray('[H]')} Highscores")
    print(f"  {T.gray('[Q]')} Beenden")
    print()
    print(T.dim("  STEUERUNG: WASD=Bewegen  E=Scan  R=Rasten"))
    print()
    print("  Wähle: ", end="", flush=True)

    while True:
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch  = sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

        if ch == '1':
            return "easy"
        elif ch == '2':
            return "normal"
        elif ch == '3':
            return "hard"
        elif ch == 'h':
            _show_global_highscores()
            return menu()
        elif ch == 'q':
            T.show()
            T.clear()
            sys.exit(0)


def _show_global_highscores():
    T.clear()
    path = os.path.expanduser("~/.void_scores.json")
    try:
        with open(path) as f:
            scores = json.load(f)
    except:
        scores = []
    print()
    print(T.bold(T.cyan("  ── VOID HIGHSCORES ───────────────────────")))
    if not scores:
        print(T.dim("  Noch keine Einträge. Spiel zuerst!"))
    for i, e in enumerate(scores[:10]):
        medal = ["🥇","🥈","🥉"][i] if i < 3 else "  "
        print(f"  {medal} {T.bold(str(e['score']))}  "
              f"{e['difficulty']}  "
              f"{T.green('✓') if e['survived'] else T.red('✗')}  "
              f"{T.dim(e['date'])}")
    print()
    print(T.dim("  [Beliebige Taste]"))
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


if __name__ == "__main__":
    diff = menu()
    game = SoloGame(difficulty=diff)
    game.start_game()
