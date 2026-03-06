# VOID — Psychologisches Terminal-Survival

```
██╗   ██╗ ██████╗ ██╗██████╗
██║   ██║██╔═══██╗██║██╔══██╗
╚██╗ ██╔╝██║   ██║██║██║  ██║
 ╚████╔╝ ╚██████╔╝██║██████╔╝
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝
```

> Das erste psychologische Multiplayer-Terminal-Game für Android (Termux) und iOS (a-Shell/iSH).

[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20iOS-brightgreen?style=flat-square)](https://github.com/IrsanAI/void)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-gray?style=flat-square)](LICENSE)
[![IrsanAI](https://img.shields.io/badge/by-IrsanAI-red?style=flat-square)](https://github.com/IrsanAI)

---

## 📱 Installation

Wähle dein Betriebssystem für die Ein-Zeilen-Installation:

### Android (Termux)
```bash
curl -fsSL https://raw.githubusercontent.com/IrsanAI/void/main/install/install.sh | bash
```
**Voraussetzung:** [Termux](https://f-droid.org/en/packages/com.termux/) aus dem F-Droid Store.

### Apple iOS (iPhone/iPad)
```bash
# In iSH (falls curl fehlt):
apk add curl && curl -fsSL https://raw.githubusercontent.com/IrsanAI/void/main/install/install_ios.sh | sh

# In a-Shell:
curl -fsSL https://raw.githubusercontent.com/IrsanAI/void/main/install/install_ios.sh | sh
```
**Voraussetzung:** [a-Shell](https://apps.apple.com/app/a-shell/id1473805438) oder [iSH](https://apps.apple.com/app/ish-shell/id1436902243) aus dem App Store.

### Windows (PowerShell / Terminal)
```powershell
git clone https://github.com/IrsanAI/void.git
cd void
python game/void_launcher.py
```
**Hinweis:** Empfohlen ist **Windows Terminal** mit UTF-8-Font (z. B. Cascadia Mono oder JetBrains Mono), damit die Grid-Symbole sauber dargestellt werden.

→ **[Zur Landing Page](https://irsanai.github.io/void)**

---

## 🍎 VOID auf iOS (Apple)

VOID ist nun vollständig kompatibel mit Apple-Geräten. Dank der Unterstützung für **a-Shell** und **iSH** können iPhone- und iPad-Nutzer das Spiel direkt im Terminal erleben.

*   **Sound-Support:** Nutzt `say` für psychologische Audio-Effekte und `afplay` für System-Sounds.
*   **Haptik:** Unterstützt Vibration via `cvibrate` (in a-Shell verfügbar).
*   **Performance:** Optimiert für die mobilen Prozessoren von Apple für ein flüssiges Terminal-Erlebnis.

---

## 🧠 Was ist VOID?

VOID ist ein **asymmetrisches psychologisches Survivalspiel** im Terminal.

Du bist ein **Fragment** — unsichtbar, isoliert, gejagt. Die **VOID** ist keine KI-Figur im üblichen Sinn. Sie ist ein lernender Algorithmus, der dein Verhalten analysiert, Muster erkennt und dich gezielt jagt.

### Drei psychologische Ebenen

| Emotion | Mechanik |
|---|---|
| **Paranoia** | Du weißt nie, wo die VOID ist. Scans enthüllen sie — und dich. |
| **Einsamkeit / Bindung** | Ping hilft dem Team, verrät aber deine Position. Vertrauen kostet Energie. |
| **Rivalität** | Signale erhöhen deinen Score. Die VOID jagt statistisch den Führenden. |

---

## 🎮 Spielmodi

### Solo — `void_solo_enhanced.py` (Empfohlen)
- **Enhanced Edition:** Mit dynamischen Soundscapes, Stereo-Simulation und Glitch-UI.
- Du allein gegen die VOID-KI + **3 Bot-Fragmente**.
- **3 Schwierigkeitsgrade**: Einfach / Normal / Schwer.
- Lokale **Highscore-Speicherung** (`~/.void_scores.json`).

### Multiplayer — `void_server.py` + `void_client.py`
- **2–6 Spieler** im gleichen WLAN über TCP/IP.
- Server startet automatisch, wenn ≥2 Spieler verbunden.
- VOID-KI läuft serverseitig, lernt alle Spieler gleichzeitig.

---

## 🚀 Starten

```bash
# Launcher (empfohlen) — wähle Solo, Client oder Server
python3 ~/games/void/game/void_launcher.py

# — oder nach Neustart —
void
```

### Manuell (Solo Enhanced)
```bash
python3 ~/games/void/game/void_solo_enhanced.py
```

---

## ⌨️ Steuerung

| Taste | Aktion | Kosten |
|---|---|---|
| `W A S D` | Bewegen | 5 Energie |
| `E` | Scannen — VOID orten | 15 Energie |
| `P` | Notsignal — Position teilen | 0 (Position enthüllt!) |
| `R` | Rasten — Energie regenerieren | 0 |
| `H` | Highscores anzeigen | — |
| `Q` | Beenden | — |

---

## 🛠 Technisch

- **Pure Python 3** — keine externen Packages (Stdlib only).
- **Cross-Platform:** Android (Termux) & iOS (a-Shell/iSH).
- **Terminal-UI:** ANSI-Escape-Codes & Glitch-Rendering-Engine.
- **Sound-Engine:** Adaptive Fallbacks für Termux-API, Sox, Beep und iOS-CLI.

### 🔊 Sound-Diagnose

Falls du in Termux nur Vibrationen, aber keinen hörbaren Sound bekommst:

```bash
python3 ~/games/void/game/void_sound_diagnose.py
```

Typischer Fix in Termux:

```bash
pkg install sox termux-api
```

> Hinweis: Für `termux-vibrate` muss zusätzlich die **Termux:API App** installiert sein.

---

## 👨‍💻 Entwickelt von

**IrsanAI** — [github.com/IrsanAI](https://github.com/IrsanAI)

---

## 📄 Lizenz

MIT — frei nutzbar, modifizierbar, weiterzugeben.
