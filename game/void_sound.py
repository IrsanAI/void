#!/usr/bin/env python3
"""
VOID — Sound Engine
Psychologisches Soundsystem für Termux.
Nutzt termux-api (termux-tts-speak, termux-vibrate) wenn verfügbar.
Generiert ANSI-Frequenz-Visualizer als immer verfügbaren Fallback.
"""

import subprocess
import threading
import time
import random
import os
import sys

# ── Verfügbarkeit prüfen ─────────────────────────────────────────
def _cmd_exists(cmd):
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except:
        return False

HAS_TERMUX_API   = _cmd_exists("termux-vibrate")
HAS_BEEP         = _cmd_exists("beep")
HAS_PLAY         = _cmd_exists("play")   # sox

# ── Emotion → Sound-Profil ───────────────────────────────────────
# Jede Emotion hat: vibrations, ascii_color, ascii_char, tts_msg
SOUND_PROFILES = {
    "paranoia": {
        "color":   "\033[91m",   # Rot
        "char":    "▓",
        "vibrate": [80, 40, 80], # ms: an, pause, an
        "label":   "PARANOIA",
        "freq_pattern": [1, 0, 1, 0, 0, 1, 0, 0, 0, 1],  # unregelmäßig
    },
    "loneliness": {
        "color":   "\033[94m",   # Blau
        "char":    "░",
        "vibrate": [200],        # langer einzelner Puls
        "label":   "EINSAMKEIT",
        "freq_pattern": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0],  # langsam, weit
    },
    "rivalry": {
        "color":   "\033[93m",   # Gelb
        "char":    "█",
        "vibrate": [50, 20, 50, 20, 150],  # schnell-schnell-lang
        "label":   "RIVALITÄT",
        "freq_pattern": [1, 1, 0, 1, 1, 0, 0, 1, 0, 1],  # aggressiv
    },
    "void_move": {
        "color":   "\033[90m",   # Grau
        "char":    "·",
        "vibrate": [30],
        "label":   "VOID",
        "freq_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    },
    "signal_collect": {
        "color":   "\033[92m",   # Grün
        "char":    "◈",
        "vibrate": [40, 20, 40, 20, 40],
        "label":   "SIGNAL",
        "freq_pattern": [1, 1, 1, 0, 1, 1, 0, 0, 1, 0],
    },
    "void_attack": {
        "color":   "\033[91m",   # Rot
        "char":    "█",
        "vibrate": [300, 50, 300],  # starker Doppelschlag
        "label":   "ANGRIFF",
        "freq_pattern": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # voll
    },
    "heartbeat": {
        "color":   "\033[31m",   # Dunkelrot
        "char":    "♥",
        "vibrate": [60, 80, 80], # lub-dub
        "label":   "HEARTBEAT",
        "freq_pattern": [1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    },
}

# ── ASCII Frequenz-Visualizer ────────────────────────────────────
class AsciiVisualizer:
    """Rendert einen 10-Band Fake-Equalizer als ASCII-Art."""
    WIDTH = 10
    HEIGHT = 5

    def __init__(self):
        self._bars = [0.0] * self.WIDTH
        self._target = [0.0] * self.WIDTH
        self._lock = threading.Lock()
        self._active = False
        self._thread = None
        self._profile = "paranoia"

    def trigger(self, profile_name: str):
        self._profile = profile_name
        profile = SOUND_PROFILES.get(profile_name, SOUND_PROFILES["void_move"])
        pattern = profile["freq_pattern"]
        with self._lock:
            for i, v in enumerate(pattern):
                self._target[i] = v * (0.6 + random.random() * 0.4)

    def start(self):
        self._active = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False

    def _loop(self):
        while self._active:
            with self._lock:
                # Smooth bars toward target
                for i in range(self.WIDTH):
                    diff = self._target[i] - self._bars[i]
                    self._bars[i] += diff * 0.35
                    # Decay target
                    self._target[i] *= 0.88

            time.sleep(0.04)

    def render(self) -> str:
        """Gibt den Visualizer als String zurück (überschreibbar)."""
        profile = SOUND_PROFILES.get(self._profile, SOUND_PROFILES["void_move"])
        color = profile["color"]
        reset = "\033[0m"
        dim = "\033[2m"

        with self._lock:
            bars = self._bars[:]

        lines = []
        for row in range(self.HEIGHT, 0, -1):
            threshold = row / self.HEIGHT
            line = "  "
            for bar in bars:
                if bar >= threshold:
                    line += color + "█" + reset + " "
                elif bar >= threshold - (1/self.HEIGHT):
                    line += dim + "▄" + reset + " "
                else:
                    line += dim + "·" + reset + " "
            lines.append(line)

        label = profile["label"]
        lines.append(f"  {dim}{label:^20}{reset}")
        return "\n".join(lines)


# ── Vibration ────────────────────────────────────────────────────
def _vibrate(pattern: list):
    if not HAS_TERMUX_API:
        return
    def _do():
        for i, ms in enumerate(pattern):
            if i % 2 == 0:  # An-Phase
                try:
                    subprocess.run(
                        ["termux-vibrate", "-d", str(ms)],
                        capture_output=True, timeout=2
                    )
                except:
                    pass
            else:  # Pause
                time.sleep(ms / 1000)
    threading.Thread(target=_do, daemon=True).start()


# ── Beep (falls sox/beep verfügbar) ─────────────────────────────
def _beep(freq_hz: int, duration_ms: int, vol: float = 0.5):
    if HAS_PLAY:
        def _do():
            try:
                subprocess.run(
                    ["play", "-n", "-q",
                     "synth", f"{duration_ms/1000:.2f}",
                     "sine", str(freq_hz),
                     "vol", str(vol)],
                    capture_output=True, timeout=3
                )
            except:
                pass
        threading.Thread(target=_do, daemon=True).start()
    elif HAS_BEEP:
        def _do():
            try:
                subprocess.run(
                    ["beep", "-f", str(freq_hz), "-l", str(duration_ms)],
                    capture_output=True, timeout=3
                )
            except:
                pass
        threading.Thread(target=_do, daemon=True).start()


# ── Sound-Presets ────────────────────────────────────────────────
SOUND_SEQUENCES = {
    "heartbeat":       [(90,  80, 0.7),  (55,  120, 0.5)],
    "signal_collect":  [(880, 60, 0.4),  (1046, 90, 0.5), (1318, 120, 0.6)],
    "paranoia":        [(110, 200, 0.3), (98,  300, 0.25)],
    "void_attack":     [(55,  400, 0.9), (41,  600, 0.8)],
    "void_move":       [(65,  100, 0.2)],
    "loneliness":      [(174, 500, 0.2), (164, 800, 0.15)],
    "rivalry":         [(220, 80,  0.5), (220, 80, 0.5), (330, 160, 0.6)],
    "scan":            [(1200, 30, 0.3), (900, 30, 0.25), (600, 80, 0.2)],
    "player_dead":     [(110, 300, 0.6), (82,  500, 0.7), (55, 1000, 0.8)],
    "game_start":      [(440, 100, 0.4), (554, 100, 0.5), (659, 200, 0.6)],
}

def _play_sequence(name: str):
    seq = SOUND_SEQUENCES.get(name, [])
    def _do():
        for freq, dur, vol in seq:
            _beep(freq, dur, vol)
            time.sleep(dur / 1000 + 0.02)
    if seq:
        threading.Thread(target=_do, daemon=True).start()


# ── Haupt-Sound-Interface ────────────────────────────────────────
class VoidSound:
    """
    Zentrale Klasse für das VOID-Soundsystem.
    Wird in void_solo.py und void_client.py instanziiert.
    """
    def __init__(self):
        self.viz = AsciiVisualizer()
        self.viz.start()
        self._heartbeat_thread = None
        self._hb_running = False
        self._hb_bpm = 44
        self.enabled = True

    def play(self, event: str):
        """Spiele einen Sound-Event ab."""
        if not self.enabled:
            return
        self.viz.trigger(event)
        _vibrate(SOUND_PROFILES.get(event, {}).get("vibrate", [50]))
        _play_sequence(event)

    def start_heartbeat(self, bpm: float = 44):
        """Startet den pulsierenden Herzschlag-Loop."""
        self._hb_bpm = bpm
        self._hb_running = True
        self._heartbeat_thread = threading.Thread(
            target=self._hb_loop, daemon=True
        )
        self._heartbeat_thread.start()

    def set_bpm(self, bpm: float):
        self._hb_bpm = max(30, min(140, bpm))

    def stop_heartbeat(self):
        self._hb_running = False

    def _hb_loop(self):
        while self._hb_running:
            self.play("heartbeat")
            self.viz.trigger("heartbeat")
            interval = 60 / self._hb_bpm
            time.sleep(interval)

    def get_visualizer(self) -> str:
        """Gibt den aktuellen Visualizer-String zurück."""
        return self.viz.render()

    def stop(self):
        self._hb_running = False
        self.viz.stop()


# ── Singleton ────────────────────────────────────────────────────
_sound_instance = None

def get_sound() -> VoidSound:
    global _sound_instance
    if _sound_instance is None:
        _sound_instance = VoidSound()
    return _sound_instance


# ── Standalone Demo ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n\033[91m VOID Sound Engine — Demo\033[0m")
    print(" Capabilities:")
    print(f"   termux-api:  {'✓' if HAS_TERMUX_API else '✗ (pkg install termux-api)'}")
    print(f"   sox (play):  {'✓' if HAS_PLAY else '✗ (pkg install sox)'}")
    print(f"   beep:        {'✓' if HAS_BEEP else '✗'}")
    print(f"   visualizer:  ✓ (immer verfügbar)")
    print()

    snd = get_sound()
    events = ["heartbeat", "paranoia", "signal_collect", "void_attack", "loneliness", "rivalry"]

    import tty, termios
    def getch():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    print(" Drücke 1-6 für Events, Q zum Beenden:\n")
    for i, e in enumerate(events):
        print(f"   [{i+1}] {e}")
    print()

    snd.start_heartbeat(48)

    while True:
        ch = getch()
        if ch == 'q':
            break
        if ch.isdigit() and 1 <= int(ch) <= len(events):
            ev = events[int(ch) - 1]
            snd.play(ev)
            print(f"\r  ▶ {ev:<20}", end="", flush=True)

    snd.stop()
    print("\n\033[90m Sound Engine beendet.\033[0m\n")
