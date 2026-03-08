#!/usr/bin/env python3
"""VOID Sound Diagnose
Zeigt verfügbare Audio-Pfade pro Plattformmodul und kann kurze Test-Events auslösen.
"""

import time
import platform
from void_sound import HAS_TERMUX_API as B_TERMUX, HAS_PLAY as B_PLAY, HAS_BEEP as B_BEEP
from void_sound_enhanced import (
    HAS_TERMUX_API as E_TERMUX,
    HAS_PLAY as E_PLAY,
    HAS_BEEP as E_BEEP,
    HAS_AFPLAY,
    HAS_SAY,
    get_sound as get_enh,
)


def _mark(ok: bool) -> str:
    return "✓" if ok else "✗"


def main():
    print("\nVOID Sound Diagnose")
    print("===================")
    print(f"Host: {platform.system()} {platform.release()}")

    print("\n[Basic Engine]")
    print(f" termux-api: {_mark(B_TERMUX)}")
    print(f" sox/play:   {_mark(B_PLAY)}")
    print(f" beep:       {_mark(B_BEEP)}")

    print("\n[Enhanced Engine]")
    print(f" termux-api: {_mark(E_TERMUX)}")
    print(f" sox/play:   {_mark(E_PLAY)}")
    print(f" beep:       {_mark(E_BEEP)}")
    print(f" afplay:     {_mark(HAS_AFPLAY)}")
    print(f" say:        {_mark(HAS_SAY)}")

    print("\n[Interpretation]")
    if E_PLAY or E_BEEP or HAS_AFPLAY or HAS_SAY:
        print(" Audible audio path detected.")
    elif E_TERMUX:
        print(" Only haptics (vibration) likely available.")
    else:
        print(" No direct audio backend detected; visualizer-only mode expected.")

    print("\n[Test: Enhanced Event Sounds]")
    snd = get_enh()
    for ev in ["game_start", "scan", "signal_collect"]:
        print(f"  -> {ev}")
        snd.play(ev)
        time.sleep(0.35)

    print("\n[Test complete] If you heard nothing, install sox/termux-api (Termux) or use a shell with audio support.")


if __name__ == "__main__":
    main()
