#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║  IrsanAI — Termux Layout Framework v2.0 (Enhanced)      ║
║  Mit Glitch-Effekten und dynamischen Übergängen         ║
╚══════════════════════════════════════════════════════════╝

Neue Features:
- Glitch-Rendering bei extremer Paranoia
- Farbübergänge basierend auf Spielzustand
- Dynamische Separator-Animationen
- Psychologische Flicker-Effekte
"""

import os
import sys
import signal
import threading
import time
import shutil
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

# ── Terminal-Profil-Klassen ──────────────────────────────────────
NARROW  = "NARROW"
NORMAL  = "NORMAL"
WIDE    = "WIDE"

@dataclass
class LayoutProfile:
    """Berechnetes Layout-Profil für das aktuelle Gerät/Terminal."""
    cols:         int
    rows:         int
    class_:       str
    grid_size:    int
    log_lines:    int
    header_lines: int
    bot_lines:    int
    controls_lines: int
    padding:      int
    usable_rows:  int
    char_ratio:   float
    density:      str

    def __str__(self):
        return (f"Layout [{self.class_}] {self.cols}×{self.rows} | "
                f"Grid:{self.grid_size}×{self.grid_size} | "
                f"Log:{self.log_lines} | Density:{self.density}")


# ── Kern-Berechnungsmodell ───────────────────────────────────────
class LayoutEngine:
    """Mathematisches Modell zur optimalen Layout-Berechnung."""

    HEADER_LINES   = 3
    CONTROLS_LINES = 1
    BOT_LINES      = 1
    LOG_MIN        = 3
    LOG_MAX        = 4
    GRID_MIN       = 6
    GRID_MAX       = 10
    CHAR_RATIO     = 0.50
    VIZ_LINES      = 3

    def compute(self, cols: int, rows: int) -> LayoutProfile:
        if cols < 48:
            class_ = NARROW
        elif cols <= 82:
            class_ = NORMAL
        else:
            class_ = WIDE

        char_ratio = self.CHAR_RATIO
        if cols < 40:
            char_ratio = 0.44
        elif cols > 90:
            char_ratio = 0.55

        padding = 1

        avail_cols_for_grid = cols - 2 - padding
        max_grid_from_width = avail_cols_for_grid // 2

        fixed = (self.HEADER_LINES + 2 + 1 +
                 self.BOT_LINES + 1 +
                 self.VIZ_LINES + 1 +
                 self.LOG_MIN + 1 +
                 self.CONTROLS_LINES)
        avail_rows_for_grid = rows - fixed
        max_grid_from_height = max(self.GRID_MIN, avail_rows_for_grid)

        grid_size = min(
            max_grid_from_width,
            max_grid_from_height,
            self.GRID_MAX
        )
        grid_size = max(grid_size, self.GRID_MIN)

        used = (self.HEADER_LINES + 2 + 1 + grid_size +
                self.BOT_LINES + 1 +
                self.VIZ_LINES + 1 +
                1 + self.CONTROLS_LINES)
        remaining = max(0, rows - used)
        log_lines = max(self.LOG_MIN, min(remaining + self.LOG_MIN, self.LOG_MAX))

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


# ── Glitch-Effekt-Engine ─────────────────────────────────────────
class GlitchEngine:
    """Erzeugt psychologische Glitch-Effekte für extreme Paranoia."""
    
    def __init__(self):
        self._glitch_intensity = 0.0
        self._flicker_state = False
        self._flicker_timer = 0.0
    
    def set_intensity(self, intensity: float):
        """Setzt Glitch-Intensität (0.0-1.0)."""
        self._glitch_intensity = max(0.0, min(1.0, intensity))
    
    def update(self, delta_time: float):
        """Aktualisiert Flicker-Zustand."""
        self._flicker_timer += delta_time
        if self._flicker_timer > 0.1:
            self._flicker_state = not self._flicker_state
            self._flicker_timer = 0.0
    
    def apply_to_text(self, text: str) -> str:
        """Wendet Glitch-Effekt auf Text an."""
        if self._glitch_intensity < 0.1:
            return text
        
        result = []
        for char in text:
            if random.random() < self._glitch_intensity * 0.15:
                # Zufälliger Glitch-Charakter
                result.append(random.choice(["█", "▓", "▒", "?", "×", "·", "~"]))
            else:
                result.append(char)
        return "".join(result)
    
    def apply_color_shift(self, color_code: str) -> str:
        """Verschiebt Farben bei hoher Glitch-Intensität."""
        if self._glitch_intensity < 0.5:
            return color_code
        
        # Zufällige Farbverschiebung
        colors = ["\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[96m"]
        if self._flicker_state:
            return random.choice(colors)
        return color_code


# ── Haupt-Layout-Klasse (erweitert) ──────────────────────────────
class Layout:
    """
    IrsanAI Termux Layout Framework v2.0 — öffentliche API.
    Mit Glitch-Effekten und psychologischen Übergängen.
    """

    def __init__(self):
        self._engine   = LayoutEngine()
        self._profile  = self._measure()
        self._callbacks: list[Callable] = []
        self._resize_lock = threading.Lock()
        self._last_resize = 0.0
        self._glitch = GlitchEngine()
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
        try:
            signal.signal(signal.SIGWINCH, self._handle_resize)
        except (OSError, ValueError):
            pass

    def _handle_resize(self, signum, frame):
        now = time.time()
        self._last_resize = now
        threading.Thread(
            target=self._debounced_update,
            args=(now,),
            daemon=True
        ).start()

    def _debounced_update(self, trigger_time: float):
        time.sleep(0.08)
        with self._resize_lock:
            if self._last_resize != trigger_time:
                return
            old = self._profile
            self._profile = self._measure()
            new = self._profile
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
        """Manuell neu messen."""
        self._profile = self._measure()

    def set_paranoia_level(self, level: float):
        """Setzt den Paranoia-Level für Glitch-Effekte."""
        self._glitch.set_intensity(level)

    def update_glitch(self, delta_time: float = 0.016):
        """Aktualisiert Glitch-Effekte (sollte in der Render-Schleife aufgerufen werden)."""
        self._glitch.update(delta_time)

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
        line = f"{color}{char * (self.cols - 1)}\033[0m"
        return self._glitch.apply_to_text(line)

    def separator(self, char: str = "─", animated: bool = False) -> str:
        """Separator mit optionaler Animation."""
        if animated and self._glitch._glitch_intensity > 0.3:
            # Psychologischer Flicker-Effekt
            chars = [char, "~", "·", "─", "═"]
            char = random.choice(chars)
        return self.hline(char)

    def center(self, text: str, width: Optional[int] = None) -> str:
        """Zentriert Text auf Terminal-Breite."""
        w = width or self.cols
        clean = self._strip_ansi(text)
        pad = max(0, (w - len(clean)) // 2)
        return " " * pad + text

    def glitch_text(self, text: str) -> str:
        """Wendet Glitch-Effekt auf Text an."""
        return self._glitch.apply_to_text(text)

    def _strip_ansi(self, text: str) -> str:
        """Entfernt ANSI-Escape-Codes."""
        import re
        return re.sub(r'\033\[[0-9;]*m', '', text)


# ── Singleton-Getter ─────────────────────────────────────────────
_layout_instance = None

def get_layout() -> Layout:
    global _layout_instance
    if _layout_instance is None:
        _layout_instance = Layout()
    return _layout_instance


# ── Backward Compatibility ──────────────────────────────────────
def get_layout_legacy():
    """Für Kompatibilität mit altem Code."""
    return get_layout()
