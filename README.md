# VOID — Psychologisches Terminal-Survival

```
██╗   ██╗ ██████╗ ██╗██████╗
██║   ██║██╔═══██╗██║██╔══██╗
╚██╗ ██╔╝██║   ██║██║██║  ██║
 ╚████╔╝ ╚██████╔╝██║██████╔╝
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝
```

> Das erste psychologische Multiplayer-Terminal-Game für Termux auf Android.

[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Termux-brightgreen?style=flat-square)](https://termux.dev)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-gray?style=flat-square)](LICENSE)
[![IrsanAI](https://img.shields.io/badge/by-IrsanAI-red?style=flat-square)](https://github.com/IrsanAI)

---

## Installation (eine Zeile, in Termux)

```bash
curl -fsSL https://raw.githubusercontent.com/IrsanAI/void/main/install/install.sh | bash
```

**Voraussetzung:** [Termux](https://f-droid.org/en/packages/com.termux/) auf Android. Das war's.

→ **[Zur Landing Page](https://irsanai.github.io/void)**

---

## Was ist VOID?

VOID ist ein **asymmetrisches psychologisches Survivalspiel** im Terminal.

Du bist ein **Fragment** — unsichtbar, isoliert, gejagt. Die **VOID** ist keine KI-Figur im üblichen Sinn. Sie ist ein lernender Algorithmus, der dein Verhalten analysiert, Muster erkennt und dich gezielt jagt.

### Drei psychologische Ebenen

| Emotion | Mechanik |
|---|---|
| **Paranoia** | Du weißt nie, wo die VOID ist. Scans enthüllen sie — und dich. |
| **Einsamkeit / Bindung** | Ping hilft dem Team, verrät aber deine Position. Vertrauen kostet Energie. |
| **Rivalität** | Signale erhöhen deinen Score. Die VOID jagt statistisch den Führenden. |

---

## Spielmodi

### Solo — `void_solo.py`
- Du allein gegen die VOID-KI
- **3 Bot-Fragmente** simulieren Mitspieler (Collector, Hunter, Coward)
- **3 Schwierigkeitsgrade**: Einfach / Normal / Schwer
- Lokale **Highscore-Speicherung** (`~/.void_scores.json`)

### Multiplayer — `void_server.py` + `void_client.py`
- **2–6 Spieler** im gleichen WLAN über TCP/IP
- Server startet automatisch, wenn ≥2 Spieler verbunden
- VOID-KI läuft serverseitig, lernt alle Spieler gleichzeitig

---

## Starten

```bash
# Launcher (empfohlen) — wähle Solo, Client oder Server
python3 ~/games/void/game/void_launcher.py

# — oder nach Termux-Neustart —
void
```

### Manuell

```bash
# Solo
python3 ~/games/void/game/void_solo.py

# Multiplayer — Server (ein Gerät)
python3 ~/games/void/game/void_server.py

# Multiplayer — Client (alle anderen)
python3 ~/games/void/game/void_client.py 192.168.1.XX
```

**Deine WLAN-IP:**
```bash
ip addr | grep 'inet ' | grep wlan
```

---

## Steuerung

| Taste | Aktion | Kosten |
|---|---|---|
| `W A S D` | Bewegen | 5 Energie |
| `E` | Scannen — VOID orten | 15 Energie |
| `P` | Notsignal — Position teilen | 0 (Position enthüllt!) |
| `R` | Rasten — Energie regenerieren | 0 |
| `H` | Highscores anzeigen | — |
| `Q` | Beenden | — |

---

## VOID-KI: Wie sie lernt

Die VOID ist kein Random-Walker:

1. **Mustererkennung** — analysiert Bewegungshistorie aller Fragmente
2. **Zielpriorisierung** — isolierte Spieler werden bevorzugt angegriffen
3. **Eskalation** — Aggression und Geschwindigkeit steigen laufend
4. **Psychologische Nachrichten** — Paranoia, Einsamkeit, Rivalität — je nach Aggressionslevel
5. **Kurzoffenbarung** — zeigt sich als Druckmittel, dann verschwindet sie wieder

---

## Dateistruktur

```
void/
├── game/
│   ├── void_launcher.py   ← Startpunkt (Solo / Client / Server)
│   ├── void_solo.py       ← Solo-Modus mit Bot-KI
│   ├── void_client.py     ← Multiplayer-Client
│   └── void_server.py     ← Multiplayer-Server
├── install/
│   └── install.sh         ← One-line Installer für Termux
├── docs/
│   └── index.html         ← GitHub Pages Landing Page
└── README.md
```

---

## Technisch

- **Pure Python 3** — keine externen Packages
- **Stdlib only**: `socket`, `threading`, `tty`, `termios`, `json`
- **Terminal-UI**: ANSI-Escape-Codes, kein curses nötig
- **Persistenz**: JSON-Datei im Home-Verzeichnis

---

## Entwickelt von

**IrsanAI** — github.com/IrsanAI

---

## Lizenz

MIT — frei nutzbar, modifizierbar, weiterzugeben.
