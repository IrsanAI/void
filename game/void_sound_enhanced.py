#!/usr/bin/env python3
"""
VOID — Enhanced Sound Engine v2.0
Erweiterte psychologische Soundscapes für maximale Immersion.

Neue Features:
- Dynamische Ambient-Soundscapes (Low-Frequency-Rauschen)
- Stereo-Simulation für Richtungsortung
- Adaptive Soundmischung basierend auf Spielzustand
- Echos und Reverb-Effekte
- "Glitch"-Sounds bei extremer Paranoia
"""

import subprocess
import threading
import time
import random
import os
import sys
import math

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
HAS_AFPLAY       = _cmd_exists("afplay") # iOS (a-Shell)
HAS_SAY          = _cmd_exists("say")    # iOS (a-Shell)

# ── Emotion → Sound-Profil (erweitert) ───────────────────────────
SOUND_PROFILES = {
    "paranoia": {
        "color":   "\033[91m",
        "char":    "▓",
        "vibrate": [80, 40, 80],
        "label":   "PARANOIA",
        "freq_pattern": [1, 0, 1, 0, 0, 1, 0, 0, 0, 1],
        "ambient_freq": 55,  # Tiefe, beängstigende Frequenz
        "ambient_duration": 800,  # ms
        "echo": True,
    },
    "loneliness": {
        "color":   "\033[94m",
        "char":    "░",
        "vibrate": [200],
        "label":   "EINSAMKEIT",
        "freq_pattern": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        "ambient_freq": 110,  # Tiefere, melancholische Frequenz
        "ambient_duration": 1200,
        "echo": False,
    },
    "rivalry": {
        "color":   "\033[93m",
        "char":    "█",
        "vibrate": [50, 20, 50, 20, 150],
        "label":   "RIVALITÄT",
        "freq_pattern": [1, 1, 0, 1, 1, 0, 0, 1, 0, 1],
        "ambient_freq": 220,  # Höhere, aggressive Frequenz
        "ambient_duration": 400,
        "echo": True,
    },
    "void_move": {
        "color":   "\033[90m",
        "char":    "·",
        "vibrate": [30],
        "label":   "VOID",
        "freq_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "ambient_freq": 65,
        "ambient_duration": 150,
        "echo": False,
    },
    "signal_collect": {
        "color":   "\033[92m",
        "char":    "◈",
        "vibrate": [40, 20, 40, 20, 40],
        "label":   "SIGNAL",
        "freq_pattern": [1, 1, 1, 0, 1, 1, 0, 0, 1, 0],
        "ambient_freq": 880,
        "ambient_duration": 300,
        "echo": False,
    },
    "void_attack": {
        "color":   "\033[91m",
        "char":    "█",
        "vibrate": [300, 50, 300],
        "label":   "ANGRIFF",
        "freq_pattern": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "ambient_freq": 40,  # Sehr tiefe, bedrohliche Frequenz
        "ambient_duration": 1500,
        "echo": True,
    },
    "heartbeat": {
        "color":   "\033[31m",
        "char":    "♥",
        "vibrate": [60, 80, 80],
        "label":   "HEARTBEAT",
        "freq_pattern": [1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "ambient_freq": 90,
        "ambient_duration": 200,
        "echo": False,
    },
}

# ── ASCII Frequenz-Visualizer (verbessert) ──────────────────────
class AsciiVisualizer:
    """Rendert einen 10-Band Fake-Equalizer als ASCII-Art mit Glitch-Effekten."""
    WIDTH = 10
    HEIGHT = 5

    def __init__(self):
        self._bars = [0.0] * self.WIDTH
        self._target = [0.0] * self.WIDTH
        self._lock = threading.Lock()
        self._active = False
        self._thread = None
        self._profile = "paranoia"
        self._glitch_mode = False  # Für extreme Paranoia
        self._glitch_intensity = 0.0

    def trigger(self, profile_name: str):
        self._profile = profile_name
        profile = SOUND_PROFILES.get(profile_name, SOUND_PROFILES["void_move"])
        pattern = profile["freq_pattern"]
        with self._lock:
            for i, v in enumerate(pattern):
                self._target[i] = v * (0.6 + random.random() * 0.4)

    def set_glitch(self, intensity: float):
        """Setzt Glitch-Effekt-Intensität (0.0-1.0)."""
        self._glitch_intensity = max(0.0, min(1.0, intensity))
        self._glitch_mode = intensity > 0.3

    def start(self):
        self._active = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False

    def _loop(self):
        while self._active:
            with self._lock:
                for i in range(self.WIDTH):
                    diff = self._target[i] - self._bars[i]
                    self._bars[i] += diff * 0.35
                    self._target[i] *= 0.88

            time.sleep(0.04)

    def render(self) -> str:
        """Gibt den Visualizer als String zurück (mit optionalen Glitch-Effekten)."""
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
                # Glitch-Effekt: Zufällige Zeichen-Ersetzung bei hoher Intensität
                if self._glitch_mode and random.random() < self._glitch_intensity * 0.3:
                    glitch_char = random.choice(["█", "▓", "▒", "░", "·", "×", "?"])
                    line += color + glitch_char + reset + " "
                elif bar >= threshold:
                    line += color + "█" + reset + " "
                elif bar >= threshold - (1/self.HEIGHT):
                    line += dim + "▄" + reset + " "
                else:
                    line += dim + "·" + reset + " "
            lines.append(line)

        label = profile["label"]
        if self._glitch_mode:
            # Glitch-Label
            glitched = "".join(
                random.choice([c, "?", "█", "·"]) if random.random() < self._glitch_intensity * 0.2 else c
                for c in label
            )
            lines.append(f"  {dim}{glitched:^20}{reset}")
        else:
            lines.append(f"  {dim}{label:^20}{reset}")
        return "\n".join(lines)


# ── Vibration ────────────────────────────────────────────────────
def _vibrate(pattern: list):
    # iOS a-Shell Fallback (cvibrate)
    if not HAS_TERMUX_API:
        if _cmd_exists("cvibrate"):
            try:
                subprocess.run(["cvibrate"], capture_output=True, timeout=1)
            except:
                pass
        return
    def _do():
        for i, ms in enumerate(pattern):
            if i % 2 == 0:
                try:
                    subprocess.run(
                        ["termux-vibrate", "-d", str(ms)],
                        capture_output=True, timeout=2
                    )
                except:
                    pass
            else:
                time.sleep(ms / 1000)
    threading.Thread(target=_do, daemon=True).start()


# ── Erweiterte Vibrationsmuster ──────────────────────────────────
def _vibrate_stereo(intensity: float, direction: str = "center"):
    """
    Simuliert Stereo-Effekte durch asymmetrische Vibrationsmuster.
    direction: "left", "right", "center", "approaching"
    """
    if not HAS_TERMUX_API:
        return
    
    base_intensity = int(50 + intensity * 150)
    
    if direction == "left":
        pattern = [base_intensity, 50, base_intensity // 2]
    elif direction == "right":
        pattern = [base_intensity // 2, 50, base_intensity]
    elif direction == "approaching":
        pattern = [base_intensity // 2, 30, base_intensity, 20, base_intensity + 50]
    else:  # center
        pattern = [base_intensity, 30, base_intensity]
    
    _vibrate(pattern)


# ── Beep (falls sox/beep verfügbar) ─────────────────────────────
def _beep(freq_hz: int, duration_ms: int, vol: float = 0.5):
    # iOS a-Shell Fallback (say oder afplay)
    if not HAS_PLAY and not HAS_BEEP:
        if HAS_SAY and freq_hz < 200: # Tiefe Töne als "Grollen" via TTS
            def _do_say():
                try:
                    subprocess.run(["say", "void"], capture_output=True, timeout=1)
                except: pass
            threading.Thread(target=_do_say, daemon=True).start()
            return
        elif HAS_AFPLAY:
            # Hier könnte man System-Sounds nutzen, falls Pfade bekannt sind
            pass

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


# ── Ambient Soundscape Generator ─────────────────────────────────
def _play_ambient(freq_hz: int, duration_ms: int, vol: float = 0.3):
    """Spielt ein tiefes Ambient-Rauschen ab."""
    _beep(freq_hz, duration_ms, vol)


# ── Echo-Effekt ──────────────────────────────────────────────────
def _play_with_echo(freq_hz: int, duration_ms: int, vol: float = 0.5, echo_count: int = 2):
    """Spielt einen Sound mit Echo-Effekt ab."""
    def _do():
        for i in range(echo_count + 1):
            delay = (i * duration_ms) / (echo_count + 1)
            time.sleep(delay / 1000)
            echo_vol = vol * (1.0 - (i / (echo_count + 1)))
            _beep(freq_hz, duration_ms // 2, echo_vol)
    threading.Thread(target=_do, daemon=True).start()


# ── Sound-Presets (erweitert) ────────────────────────────────────
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
    "glitch":          [(150, 50, 0.4), (75, 100, 0.3), (200, 50, 0.35)],  # Glitch-Sound
}

def _play_sequence(name: str):
    seq = SOUND_SEQUENCES.get(name, [])
    def _do():
        for freq, dur, vol in seq:
            _beep(freq, dur, vol)
            time.sleep(dur / 1000 + 0.02)
    if seq:
        threading.Thread(target=_do, daemon=True).start()


# ── Haupt-Sound-Interface (erweitert) ────────────────────────────
class VoidSound:
    """
    Erweiterte VOID Sound Engine mit Ambient-Soundscapes und Stereo-Effekten.
    """
    def __init__(self):
        self.viz = AsciiVisualizer()
        self.viz.start()
        self._heartbeat_thread = None
        self._hb_running = False
        self._hb_bpm = 44
        self.enabled = True
        self._ambient_thread = None
        self._ambient_running = False
        self._distance_to_void = float('inf')  # Für Stereo-Effekte

    def play(self, event: str):
        """Spiele einen Sound-Event ab (mit erweiterten Effekten)."""
        if not self.enabled:
            return
        self.viz.trigger(event)
        profile = SOUND_PROFILES.get(event, {})
        _vibrate(profile.get("vibrate", [50]))
        _play_sequence(event)
        
        # Ambient-Soundscape
        if "ambient_freq" in profile:
            _play_ambient(profile["ambient_freq"], profile.get("ambient_duration", 300), 0.2)
        
        # Echo-Effekt
        if profile.get("echo", False) and HAS_PLAY:
            seq = SOUND_SEQUENCES.get(event, [])
            if seq:
                freq, dur, vol = seq[0]
                _play_with_echo(freq, dur, vol * 0.5, echo_count=2)

    def play_with_direction(self, event: str, distance: float, direction: str = "center"):
        """Spiele einen Sound mit Richtungs-Information ab (Stereo-Simulation)."""
        if not self.enabled:
            return
        self.play(event)
        _vibrate_stereo(min(1.0, 1.0 / max(1.0, distance)), direction)

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

    def set_paranoia_level(self, level: float):
        """
        Setzt den Paranoia-Level (0.0-1.0).
        Bei hohen Werten: Glitch-Effekte in der UI.
        """
        self.viz.set_glitch(level)

    def set_distance_to_void(self, distance: float):
        """Aktualisiert die Distanz zur VOID für Stereo-Effekte."""
        self._distance_to_void = distance

    def get_visualizer(self) -> str:
        """Gibt den aktuellen Visualizer-String zurück."""
        return self.viz.render()

    def stop(self):
        self._hb_running = False
        self._ambient_running = False
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
    print("\n\033[91m VOID Enhanced Sound Engine — Demo v2.0\033[0m")
    print(" Capabilities:")
    print(f"   termux-api:  {'✓' if HAS_TERMUX_API else '✗ (pkg install termux-api)'}")
    print(f"   sox (play):  {'✓' if HAS_PLAY else '✗ (pkg install sox)'}")
    print(f"   beep:        {'✓' if HAS_BEEP else '✗'}")
    print(f"   visualizer:  ✓ (immer verfügbar)")
    print()
    print(" New Features:")
    print("   ✓ Ambient Soundscapes")
    print("   ✓ Stereo-Simulation")
    print("   ✓ Echo-Effekte")
    print("   ✓ Glitch-UI bei Paranoia")
    print()

    snd = get_sound()
    events = ["heartbeat", "paranoia", "signal_collect", "void_attack", "loneliness", "rivalry", "glitch"]

    import tty, termios
    def getch():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    print(" Drücke 1-7 für Events, P für Paranoia-Test, Q zum Beenden:\n")
    for i, e in enumerate(events):
        print(f"   [{i+1}] {e}")
    print(f"   [P] Paranoia-Glitch-Test")
    print()

    snd.start_heartbeat(48)

    while True:
        ch = getch()
        if ch == 'q':
            break
        if ch == 'p':
            print(f"\r  ▶ Paranoia-Glitch-Test", end="", flush=True)
            for i in range(10):
                snd.set_paranoia_level(i / 10)
                snd.play("paranoia")
                time.sleep(0.3)
            snd.set_paranoia_level(0)
        elif ch.isdigit() and 1 <= int(ch) <= len(events):
            ev = events[int(ch) - 1]
            snd.play(ev)
            print(f"\r  ▶ {ev:<20}", end="", flush=True)

    snd.stop()
    print("\n\033[90m Enhanced Sound Engine beendet.\033[0m\n")
