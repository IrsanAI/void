#!/usr/bin/env python3
"""
VOID — Solo Mode Enhanced v2.0
Mit erweiterten Immersions-Effekten, Glitch-Rendering und Stereo-Sound.

Neue Features:
- Dynamische Paranoia-Level mit UI-Glitches
- Stereo-Richtungsortung der VOID
- Psychologische Flicker-Effekte
- Erweiterte Ambient-Soundscapes
"""

import time
import random
import sys
import os
import threading
import json
import shutil

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    import msvcrt
else:
    import tty
    import termios

# Neue Enhanced Module
try:
    from void_logger import get_logger
    _LOG = get_logger()
    _LOG.info("Solo Mode Enhanced gestartet.")
except ImportError:
    class _DummyLog:
        def info(self, *a): pass
        def debug(self, *a): pass
        def error(self, *a): pass
        def warning(self, *a): pass
    _LOG = _DummyLog()
try:
    from void_layout_enhanced import get_layout, NARROW, NORMAL, WIDE
    _LAYOUT_AVAILABLE = True
except ImportError:
    try:
        from void_layout import get_layout, NARROW, NORMAL, WIDE
        _LAYOUT_AVAILABLE = True
    except ImportError:
        _LAYOUT_AVAILABLE = False

try:
    from void_sound_enhanced import get_sound, get_capabilities_snapshot
    _SOUND_AVAILABLE = True
except ImportError:
    try:
        from void_sound import get_sound
        def get_capabilities_snapshot():
            return {}
        _SOUND_AVAILABLE = True
    except ImportError:
        _SOUND_AVAILABLE = False
        def get_capabilities_snapshot():
            return {}
        def get_sound():
            class _Dummy:
                def play(self, *a): pass
                def start_heartbeat(self, *a): pass
                def set_bpm(self, *a): pass
                def stop_heartbeat(self): pass
                def get_visualizer(self): return ""
                def set_paranoia_level(self, *a): pass
                def set_distance_to_void(self, *a): pass
                def play_with_direction(self, *a): pass
                def stop(self): pass
            return _Dummy()

# ── Terminal ─────────────────────────────────────────────────────
class T:
    @staticmethod
    def clear():
        """Stabiles Bildschirm-Clear ohne externes `clear`-Kommando."""
        print("\033[2J\033[H\033[?25l", end="", flush=True)

    @staticmethod
    def redraw_start():
        print("\033[H", end="", flush=False)

    @staticmethod
    def use_alt_buffer(enable=True):
        print("\033[?1049h" if enable else "\033[?1049l", end="", flush=True)

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
ROUND_TIME  = 180
BOT_COUNT   = 3
SCAN_COST   = 15
MOVE_COST   = 5
SIG_REWARD  = 30
VOID_TICK   = 7.0

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
        self.personality = random.choice(["hunter", "collector", "coward"])

    def tick(self, signals, void_x, void_y, void_visible):
        if not self.alive:
            return
        self.energy = min(100, self.energy + 3)

        if void_visible:
            dist = abs(void_x - self.x) + abs(void_y - self.y)
            if dist <= 3 and self.personality != "hunter":
                self._flee(void_x, void_y)
                return

        if self.personality == "collector" and signals:
            self._move_toward_nearest(signals)
        elif self.personality == "hunter":
            self._random_walk()
        else:
            self._random_walk()

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
        self.move_hist   = {}
        self.visible     = False
        self.reveal_until= 0
        self.paranoia_level = 0.0  # Für Glitch-Effekte

    def record(self, px, py):
        key = (px % 3, py % 3)
        self.move_hist[key] = self.move_hist.get(key, 0) + 1

    def move_toward(self, tx, ty):
        dx = 0 if tx == self.x else (1 if tx > self.x else -1)
        dy = 0 if ty == self.y else (1 if ty > self.y else -1)
        if random.random() < 0.25:
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
        self.paranoia_level = self.aggression  # Paranoia-Level mit Aggression synchronisieren

    def reveal_self(self, duration=4):
        self.visible = True
        self.reveal_until = time.time() + duration

    def update_visibility(self):
        if self.visible and time.time() > self.reveal_until:
            self.visible = False


# ── Haupt-Spielzustand ────────────────────────────────────────────
class SoloGame:

    @staticmethod
    def _strip_ansi(text):
        import re
        return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)

    def _fit_line(self, text, max_cols):
        plain = self._strip_ansi(text)
        if len(plain) > max_cols:
            return plain[:max_cols]
        return text

    def _line(self, text=""):
        self._frame_lines.append(str(text))

    def _flush_frame(self, cols, rows):
        T.redraw_start()
        visible = [self._fit_line(l, cols) for l in self._frame_lines[:rows]]
        if len(visible) < rows:
            visible.extend([""] * (rows - len(visible)))
        payload = "\n".join(f"\033[2K{line}" for line in visible)
        print(payload, end="", flush=True)

    def __init__(self, difficulty="normal"):
        cfg           = DIFFICULTY[difficulty]
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
        self.last_render_time = time.time()
        try:
            _LOG.info(f"Sound capabilities: {get_capabilities_snapshot()}")
        except Exception:
            pass
        if self.L:
            self.L.on_resize(self._on_resize)

    def _on_resize(self):
        if self.L:
            new_grid = self.L.grid_size
            if new_grid != self.GRID:
                self.GRID = new_grid
                self.px = min(self.px, self.GRID - 1)
                self.py = min(self.py, self.GRID - 1)
        self._render()

    def _spawn_signals(self, n=2):
        g = self.GRID if hasattr(self, 'GRID') else GRID
        return [(random.randint(0, g-1), random.randint(0, g-1)) for _ in range(n)]

    def time_left(self):
        return max(0, int(ROUND_TIME - (time.time() - self.start)))

    def add_msg(self, text, style="normal"):
        self.messages.append((time.strftime("%H:%M:%S"), text, style))
        if len(self.messages) > 7:
            self.messages.pop(0)

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
            with open(path, 'w') as f:
                json.dump(self.highscores, f)
        except:
            pass

    def start_game(self):
        T.use_alt_buffer(True)
        T.hide()
        self.snd.play("game_start")
        self.snd.start_heartbeat(44)
        if hasattr(self.snd, "start_ambient"):
            self.snd.start_ambient(0.10)
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

            targets = [(self.px, self.py, "player")]
            for b in self.bots:
                if b.alive:
                    targets.append((b.x, b.y, b.name))

            if random.random() < self.void.aggression:
                tx, ty, tname = self.px, self.py, "player"
            else:
                tx, ty, tname = random.choice(targets)

            self.void.record(self.px, self.py)
            self.void.move_toward(tx, ty)
            self.void.update_visibility()
            
            # Berechne Distanz zur VOID für Stereo-Effekte
            distance = abs(self.void.x - self.px) + abs(self.void.y - self.py)
            direction = "center"
            if self.void.x < self.px:
                direction = "left"
            elif self.void.x > self.px:
                direction = "right"
            
            self.snd.play("void_move")
            self.snd.set_distance_to_void(distance)

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

            msg = self.void.choose_msg()
            self.last_void_msg = msg
            self.add_msg(f"VOID: {msg}", "void")

            if self.void.aggression > 0.7:
                self.snd.play("rivalry")
            elif self.void.aggression > 0.4:
                self.snd.play("paranoia")
            else:
                self.snd.play("loneliness")

            new_bpm = 44 + self.void.aggression * 60
            self.snd.set_bpm(new_bpm)

            # Paranoia-Level für UI-Glitches
            if self.L:
                self.L.set_paranoia_level(self.void.paranoia_level)
            self.snd.set_paranoia_level(self.void.paranoia_level)

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

    def _input_loop(self):
        while self.running:
            try:
                ch = self._getch().lower()
            except:
                continue

            if ch == 'q':
                self.running = False
                T.show()
                T.use_alt_buffer(False)
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

    def _render(self, force=False):
        with self.render_lock:
            try:
                size = shutil.get_terminal_size(fallback=(80, 24))
                cols, rows = max(20, size.columns), max(12, size.lines)
                _LOG.debug(f"Render: Terminal Size {cols}x{rows}")
            except Exception as e:
                cols, rows = 80, 24
                _LOG.error(f"Fehler beim Abrufen der Terminal-Größe: {e}")

            self._frame_lines = []
            self._draw_header()
            self._draw_grid()
            self._draw_bots()
            self._draw_visualizer()
            self._draw_messages()
            self._draw_controls()
            self._flush_frame(cols, rows)

    def _draw_header(self):
        G = self.GRID
        tl = self.time_left()
        time_s = T.red(f"⏱{tl}s") if tl <= 30 else T.yellow(f"⏱{tl}s")
        diff_c = {"easy": T.green, "normal": T.yellow, "hard": T.red}[self.difficulty]
        agg_pct = int(self.void.aggression * 8)
        agg_bar = T.red("█" * agg_pct) + T.gray("░" * (8 - agg_pct))
        en_pct  = int((self.energy / 100) * 8)
        en_col  = "92" if self.energy > 60 else ("93" if self.energy > 30 else "91")
        en_bar  = f"\033[{en_col}m" + "█" * en_pct + "\033[90m" + "░" * (8-en_pct) + "\033[0m"
        self._line(f"{T.bold(diff_c(self.difficulty[:3].upper()))} {time_s} {T.cyan('◈'+str(self.score))}pts")
        self._line(f"{T.red('A')}[{agg_bar}] {T.cyan('E')}[{en_bar}]{self.energy}")
        if self.last_void_msg:
            msg = self.last_void_msg[:50]
            if self.L:
                msg = self.L.glitch_text(msg)
            self._line(f"{T.red('▶')} {T.dim(msg)}")
        else:
            self._line()

    def _draw_grid(self):
        G = self.GRID
        grid = [[T.gray('·')] * G for _ in range(G)]
        for sx, sy in self.signals:
            if 0 <= sx < G and 0 <= sy < G:
                grid[sy][sx] = T.yellow('◈')
        if self.void.visible:
            vx, vy = self.void.x, self.void.y
            if 0 <= vx < G and 0 <= vy < G:
                grid[vy][vx] = T.bold(T.red('▓'))
        bot_colors = ["96", "95", "94"]
        for i, bot in enumerate(self.bots):
            if bot.alive and 0 <= bot.x < G and 0 <= bot.y < G:
                grid[bot.y][bot.x] = f"\033[{bot_colors[i%3]}m○\033[0m"
            elif not bot.alive and 0 <= bot.x < G and 0 <= bot.y < G:
                grid[bot.y][bot.x] = T.gray('×')
        if self.alive and 0 <= self.px < G and 0 <= self.py < G:
            grid[self.py][self.px] = T.bold(T.green('◉'))
        self._line(T.gray("┌" + "─" * (G*2) + "┐"))
        for row in grid:
            line = T.gray("│")
            for cell in row:
                line += cell + " "
            self._line(line.rstrip() + T.gray("│"))
        self._line(T.gray("└" + "─" * (G*2) + "┘"))
        self._line(f"{T.green('◉')}Du {T.cyan('○')}Bot {T.yellow('◈')}Sig {T.red('▓')}VOID")

    def _draw_bots(self):
        parts = []
        for b in self.bots:
            if b.alive:
                parts.append(f"{T.cyan('●')}{b.name} {T.gray(str(b.score))}")
            else:
                parts.append(T.gray(f"×{b.name}"))
        self._line(" ".join(parts))

    def _draw_visualizer(self):
        viz = self.snd.get_visualizer()
        if viz:
            lines = viz.split('\n')
            for l in lines[-3:]:
                self._line(l)

    def _draw_messages(self):
        G = self.GRID
        self._line(T.gray("─" * (G*2+1)))
        shown = self.messages[-3:]
        for ts, msg, style in shown:
            short = ts[-5:]
            cut = msg[:50]
            if self.L:
                cut = self.L.glitch_text(cut)
            if style == "void":   self._line(f"{T.dim(short)} {T.red(cut)}")
            elif style == "good": self._line(f"{T.dim(short)} {T.green(cut)}")
            elif style == "warn": self._line(f"{T.dim(short)} {T.yellow(cut)}")
            else:                 self._line(f"{T.dim(short)} {T.dim(cut)}")
        for _ in range(3 - len(shown)):
            self._line()

    def _draw_controls(self):
        G = self.GRID
        self._line(T.gray("─" * (G*2+1)))
        self._line(f"{T.bold('W')}↑{T.bold('S')}↓{T.bold('A')}←{T.bold('D')}→ "
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
            diff_badge = {"easy": T.green("E"), "normal": T.yellow("N"), "hard": T.red("H")}[e.get("difficulty", "normal")]
            survived = "✓" if e.get("survived") else "✗"
            print(f"  {medal} {e['score']:>4} pts  [{diff_badge}] {survived}  {e.get('date', '?')}")
        print()
        input(T.dim("  [Enter] zurück..."))
        self._render()

    def _end_game(self, survived=False):
        self.snd.stop_heartbeat()
        self.snd.stop()
        self.running = False
        self._save_score(self.score, survived, self.difficulty)
        
        T.show()
        T.use_alt_buffer(False)
        T.clear()
        print()
        if survived:
            print(T.bold(T.green("  🎉 DU HAST ÜBERLEBT!")))
        else:
            print(T.bold(T.red("  💀 DU BIST TOT.")))
        print()
        print(f"  Score: {T.bold(str(self.score))}")
        print(f"  Schwierigkeit: {self.difficulty}")
        print()
        input(T.dim("  [Enter] zum Beenden..."))

    def _getch(self):
        if IS_WINDOWS:
            ch = msvcrt.getch()
            return ch.decode("utf-8", errors="ignore")
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ── Schwierigkeitswahl ────────────────────────────────────────────
def choose_difficulty():
    T.clear()
    print()
    print(T.bold(T.red("  ██╗   ██╗ ██████╗ ██╗██████╗")))
    print(T.bold(T.red("  ██║   ██║██╔═══██╗██║██╔══██╗")))
    print(T.bold(T.red("  ╚██╗ ██╔╝██║   ██║██║██║  ██║")))
    print(T.bold(T.red("   ╚████╔╝ ╚██████╔╝██║██████╔╝")))
    print(T.bold(T.red("    ╚═══╝   ╚═════╝ ╚═╝╚═════╝")))
    print()
    print(T.bold("  SOLO MODE ENHANCED"))
    print()
    print(f"  {T.green('[1]')} Einfach")
    print(f"  {T.yellow('[2]')} Normal")
    print(f"  {T.red('[3]')} Schwer")
    print()
    print(f"  {T.gray('[H]')} Highscores")
    print(f"  {T.gray('[Q]')} Beenden")
    print()
    print("  Wähle: ", end="", flush=True)

    if IS_WINDOWS:
        ch = msvcrt.getch().decode("utf-8", errors="ignore").lower()
    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    if ch == '1':
        return "easy"
    elif ch == '2':
        return "normal"
    elif ch == '3':
        return "hard"
    elif ch == 'h':
        # Highscores anzeigen
        game = SoloGame()
        game._show_highscores()
        return choose_difficulty()
    elif ch == 'q':
        T.clear()
        sys.exit(0)
    else:
        return choose_difficulty()


# ── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    difficulty = choose_difficulty()
    game = SoloGame(difficulty)
    game.start_game()
