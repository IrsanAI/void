#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║  IrsanAI — Termux Layout Framework  v1.0                ║
║  Dynamische Terminal-Skalierung für alle IrsanAI-Games  ║
║                                                          ║
║  Mathematisches Modell:                                  ║
║    grid = f(cols, rows, char_ratio, density)            ║
║    layout = classify(cols) → NARROW|NORMAL|WIDE         ║
║    SIGWINCH → live resize ohne Neustart                  ║
╚══════════════════════════════════════════════════════════╝

Verwendung in jedem IrsanAI-Game:

    from void_layout import Layout
    L = Layout()
    L.on_resize(my_render_function)   # auto-rerender on resize
    grid_size = L.grid_size           # optimale Grid-Größe
    cols, rows = L.cols, L.rows       # aktuelle Terminal-Größe
"""

import os
import sys
import signal
import threading
import time
import shutil
from dataclasses import dataclass, field
from typing import Callable, Optional

# ── Terminal-Profil-Klassen ──────────────────────────────────────
NARROW  = "NARROW"   # <  50 cols  — kleines Smartphone-Terminal
NORMAL  = "NORMAL"   # 50-80 cols  — Standard Termux Hochformat
WIDE    = "WIDE"     # >  80 cols  — Querformat oder großer Screen

@dataclass
class LayoutProfile:
    """Berechnetes Layout-Profil für das aktuelle Gerät/Terminal."""
    cols:         int
    rows:         int
    class_:       str          # NARROW | NORMAL | WIDE
    grid_size:    int          # optimale quadratische Grid-Größe
    log_lines:    int          # max. anzuzeigende Log-Zeilen
    header_lines: int          # Zeilen für Header reserviert
    bot_lines:    int          # Zeilen für Bot-Anzeige
    controls_lines: int        # Zeilen für Steuerung
    padding:      int          # horizontaler Padding (Leerzeichen)
    usable_rows:  int          # Rows nach Abzug fixer Elemente
    char_ratio:   float        # geschätztes Breite/Höhe Verhältnis
    density:      str          # COMPACT | NORMAL | SPACIOUS

    def __str__(self):
        return (f"Layout [{self.class_}] {self.cols}×{self.rows} | "
                f"Grid:{self.grid_size}×{self.grid_size} | "
                f"Log:{self.log_lines} | Density:{self.density}")


# ── Kern-Berechnungsmodell ───────────────────────────────────────
class LayoutEngine:
    """
    Mathematisches Modell zur optimalen Layout-Berechnung.

    Modell-Annahmen (empirisch aus Termux-Messungen):
    - Termux Standard-Font: Breite ≈ 0.55 × Höhe eines Zeichens
    - Samsung One UI Termux: char_ratio ≈ 0.48–0.52
    - Grid-Zelle belegt: 2 cols (Zeichen + Leerzeichen)
    - Header fix: 3 Zeilen
    - Controls fix: 2 Zeilen
    - Mindest-Grid: 6×6
    - Max-Grid: 14×14

    Optimierungsziel:
      maximize grid_size
      subject to:
        grid_size * 2 + 4 <= cols        (Breite passt)
        grid_size + fixed_lines <= rows  (Höhe passt)
        grid_size >= 6                   (spielbar)
    """

    HEADER_LINES   = 3
    CONTROLS_LINES = 2
    BOT_LINES      = 2
    LOG_MIN        = 2
    LOG_MAX        = 6
    GRID_MIN       = 6
    GRID_MAX       = 14
    CHAR_RATIO     = 0.50   # Termux-Standard

    def compute(self, cols: int, rows: int) -> LayoutProfile:
        # ── Schritt 1: Klasse bestimmen ──────────────────────────
        if cols < 48:
            class_ = NARROW
        elif cols <= 82:
            class_ = NORMAL
        else:
            class_ = WIDE

        # ── Schritt 2: Zeichenverhältnis schätzen ────────────────
        # Auf sehr schmalen Screens werden Fonts oft größer → ratio sinkt
        char_ratio = self.CHAR_RATIO
        if cols < 40:
            char_ratio = 0.44
        elif cols > 90:
            char_ratio = 0.55

        # ── Schritt 3: Padding berechnen ─────────────────────────
        padding = 1 if class_ == NARROW else 2

        # ── Schritt 4: Verfügbare Breite für Grid ────────────────
        # Grid-Zelle = 2 cols, Rahmen = 2 cols, Padding = 2×padding
        avail_cols_for_grid = cols - 2 - (2 * padding)
        max_grid_from_width = avail_cols_for_grid // 2

        # ── Schritt 5: Verfügbare Höhe für Grid ──────────────────
        # Feste Elemente: header + controls + bots + log_min + separator
        fixed = (self.HEADER_LINES + self.CONTROLS_LINES +
                 self.BOT_LINES + self.LOG_MIN + 3)  # 3 Separatoren
        avail_rows_for_grid = rows - fixed
        max_grid_from_height = max(self.GRID_MIN, avail_rows_for_grid)

        # ── Schritt 6: Optimale Grid-Größe (Minimax) ─────────────
        grid_size = min(
            max_grid_from_width,
            max_grid_from_height,
            self.GRID_MAX
        )
        grid_size = max(grid_size, self.GRID_MIN)

        # ── Schritt 7: Log-Zeilen aus verbleibendem Platz ────────
        used = (self.HEADER_LINES + grid_size + self.CONTROLS_LINES +
                self.BOT_LINES + 3)
        remaining = rows - used
        log_lines = max(self.LOG_MIN, min(remaining, self.LOG_MAX))

        # ── Schritt 8: Dichte (Density) ──────────────────────────
        usable = rows - self.HEADER_LINES - self.CONTROLS_LINES
        fill_ratio = (grid_size + log_lines + self.BOT_LINES) / max(1, usable)
        if fill_ratio > 0.85:
            density = "COMPACT"
        elif fill_ratio > 0.60:
            density = "NORMAL"
        else:
            density = "SPACIOUS"

        usable_rows = rows - self.HEADER_LINES - self.CONTROLS_LINES

        return LayoutProfile(
            cols=cols,
            rows=rows,
            class_=class_,
            grid_size=grid_size,
            log_lines=log_lines,
            header_lines=self.HEADER_LINES,
            bot_lines=self.BOT_LINES,
            controls_lines=self.CONTROLS_LINES,
            padding=padding,
            usable_rows=usable_rows,
            char_ratio=char_ratio,
            density=density,
        )


# ── Haupt-Layout-Klasse (öffentliche API) ────────────────────────
class Layout:
    """
    IrsanAI Termux Layout Framework — öffentliche API.

    Beispiel:
        from void_layout import Layout

        L = Layout()
        L.on_resize(render)      # callback bei Resize

        # Im Render:
        grid_size = L.grid_size
        pad = ' ' * L.padding
    """

    def __init__(self):
        self._engine   = LayoutEngine()
        self._profile  = self._measure()
        self._callbacks: list[Callable] = []
        self._resize_lock = threading.Lock()
        self._last_resize = 0.0
        self._install_sigwinch()

    # ── Messen ───────────────────────────────────────────────────
    def _measure(self) -> LayoutProfile:
        try:
            size = shutil.get_terminal_size(fallback=(60, 30))
            cols, rows = size.columns, size.lines
        except:
            cols, rows = 60, 30
        return self._engine.compute(cols, rows)

    # ── SIGWINCH — Terminal Resize Signal ────────────────────────
    def _install_sigwinch(self):
        """
        SIGWINCH wird vom Terminal gesendet wenn sich die Fenstergröße
        ändert — auch wenn die Android-Tastatur auf/zu geht.
        """
        try:
            signal.signal(signal.SIGWINCH, self._handle_resize)
        except (OSError, ValueError):
            pass  # Nicht verfügbar in manchen Umgebungen

    def _handle_resize(self, signum, frame):
        """Debounced Resize-Handler — wartet 80ms auf weitere Signale."""
        now = time.time()
        self._last_resize = now
        # Debounce in separatem Thread
        threading.Thread(
            target=self._debounced_update,
            args=(now,),
            daemon=True
        ).start()

    def _debounced_update(self, trigger_time: float):
        time.sleep(0.08)  # 80ms debounce
        with self._resize_lock:
            if self._last_resize != trigger_time:
                return  # Neueres Signal kam rein
            old = self._profile
            self._profile = self._measure()
            new = self._profile
            # Nur neu rendern wenn sich etwas Relevantes geändert hat
            if old.cols != new.cols or old.rows != new.rows:
                for cb in self._callbacks:
                    try:
                        cb()
                    except Exception:
                        pass

    # ── Öffentliche API ──────────────────────────────────────────
    def on_resize(self, callback: Callable):
        """Registriert eine Funktion die bei Resize aufgerufen wird."""
        self._callbacks.append(callback)

    def remove_resize_callback(self, callback: Callable):
        self._callbacks = [c for c in self._callbacks if c != callback]

    def refresh(self):
        """Manuell neu messen (z.B. nach Pause)."""
        self._profile = self._measure()

    # ── Properties ───────────────────────────────────────────────
    @property
    def profile(self) -> LayoutProfile:
        return self._profile

    @property
    def cols(self) -> int:
        return self._profile.cols

    @property
    def rows(self) -> int:
        return self._profile.rows

    @property
    def grid_size(self) -> int:
        return self._profile.grid_size

    @property
    def log_lines(self) -> int:
        return self._profile.log_lines

    @property
    def padding(self) -> int:
        return self._profile.padding

    @property
    def pad(self) -> str:
        return ' ' * self._profile.padding

    @property
    def class_(self) -> str:
        return self._profile.class_

    @property
    def density(self) -> str:
        return self._profile.density

    @property
    def is_narrow(self) -> bool:
        return self._profile.class_ == NARROW

    @property
    def is_wide(self) -> bool:
        return self._profile.class_ == WIDE

    # ── Hilfsmethoden für Rendering ──────────────────────────────
    def hline(self, char: str = "─", color: str = "\033[90m") -> str:
        """Horizontale Linie die genau die Terminal-Breite füllt."""
        return f"{color}{char * (self.cols - 1)}\033[0m"

    def center(self, text: str, width: Optional[int] = None) -> str:
        """Zentriert Text auf Terminal-Breite (ignoriert ANSI-Codes)."""
        w = width or self.cols
        clean = self._strip_ansi(text)
        pad = max(0, (w - len(clean)) // 2)
        return ' ' * pad + text

    def truncate(self, text: str, max_len: Optional[int] = None) -> str:
        """Kürzt Text auf verfügbare Breite."""
        limit = (max_len or self.cols) - self.padding - 2
        clean = self._strip_ansi(text)
        if len(clean) <= limit:
            return text
        return text[:limit - 1] + "…"

    def bar(self, ratio: float, width: int = 10,
            fill_code: str = "92", empty_code: str = "90") -> str:
        """Farbiger Fortschrittsbalken."""
        filled = int(min(1.0, max(0.0, ratio)) * width)
        return (f"\033[{fill_code}m" + "█" * filled +
                f"\033[{empty_code}m" + "░" * (width - filled) + "\033[0m")

    @staticmethod
    def _strip_ansi(text: str) -> str:
        import re
        return re.sub(r'\033\[[0-9;]*m', '', text)

    # ── Debug / Info ─────────────────────────────────────────────
    def info(self) -> str:
        p = self._profile
        return (
            f"\n\033[96m IrsanAI Layout Framework v1.0\033[0m\n"
            f"\033[90m ─────────────────────────────────────\033[0m\n"
            f" Terminal:    {p.cols} × {p.rows} Zeichen\n"
            f" Klasse:      \033[93m{p.class_}\033[0m\n"
            f" Grid-Größe:  \033[92m{p.grid_size} × {p.grid_size}\033[0m\n"
            f" Log-Zeilen:  {p.log_lines}\n"
            f" Padding:     {p.padding}\n"
            f" Char-Ratio:  {p.char_ratio:.2f}\n"
            f" Density:     {p.density}\n"
            f" Usable Rows: {p.usable_rows}\n"
            f"\033[90m ─────────────────────────────────────\033[0m\n"
            f" SIGWINCH:    {'✓ aktiv' if self._callbacks else '○ kein callback'}\n"
        )


# ── Singleton für Game-weite Nutzung ────────────────────────────
_layout_instance: Optional[Layout] = None

def get_layout() -> Layout:
    """Gibt die globale Layout-Instanz zurück (Singleton)."""
    global _layout_instance
    if _layout_instance is None:
        _layout_instance = Layout()
    return _layout_instance


# ── Standalone Demo / Diagnose ───────────────────────────────────
if __name__ == "__main__":
    import tty, termios

    def getch():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    L = Layout()

    def demo_render():
        """Live-Demo: zeigt Layout-Info und Grid-Visualisierung."""
        os.system('clear')
        print(L.info())

        p = L.profile
        g = p.grid_size
        pad = L.pad

        # Mini Grid-Preview
        print(f"\033[90m{pad}┌{'─' * (g*2)}┐\033[0m")
        for row in range(g):
            line = f"\033[90m{pad}│\033[0m"
            for col in range(g):
                # Zeige Muster abhängig von Klasse
                if row == g//2 and col == g//2:
                    line += "\033[92m◉\033[0m "
                elif (row + col) % 4 == 0:
                    line += "\033[93m◈\033[0m "
                else:
                    line += "\033[90m·\033[0m "
            line = line.rstrip() + f"\033[90m│\033[0m"
            print(line)
        print(f"\033[90m{pad}└{'─' * (g*2)}┘\033[0m")
        print()
        print(f"\033[90m Drehe Gerät oder ändere Termux-Größe → auto-update\033[0m")
        print(f"\033[90m [Q] Beenden\033[0m")

    L.on_resize(demo_render)
    demo_render()

    # Warte auf Q
    while True:
        ch = getch()
        if ch.lower() == 'q':
            break

    print("\n\033[90m IrsanAI Layout Framework — beendet.\033[0m\n")
