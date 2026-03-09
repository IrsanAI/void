# PLATFORM SUPPORT MATRIX

Ziel: Android, Apple (iOS) und Windows auf einem gemeinsamen Nenner betreiben,
aber die plattformspezifischen Unterschiede transparent dokumentieren.

## Aktueller Stand

| Bereich | Android (Termux) | Apple iOS (a-Shell / iSH) | Windows (PowerShell / Terminal) |
|---|---|---|---|
| Installation | ✅ `install/install.sh` | ✅ `install/install_ios.sh` | ⚠️ manuell via `git clone` + `python` |
| Launcher | ✅ | ✅ | ✅ |
| Solo/Client/Server Runtime | ✅ | ✅ | ✅ |
| Relay (Beta) | ✅ | ✅ | ✅ |
| Netcheck | ✅ | ✅ (abhängig von Shell-Tools) | ✅ |
| Audio/Haptik | ✅ (Termux-API/Sox-Fallbacks) | ✅ (iOS-CLI/a-Shell Features) | ⚠️ je nach Terminal/Host |

## Bewertung "gemeinsamer Nenner"

**Ja, sinnvoll und notwendig.**

Gemeinsamer Nenner sollte bleiben:
1. Ein gemeinsamer Python-Kern (`game/*.py`) für Gameplay/Netzwerk/Relay.
2. Eine gemeinsame Fehlersemantik (Error-Codes + klare Meldungen).
3. Ein gemeinsamer Smoke-Test für Kernpfade (`game/void_smoke_test.py`).

Plattform-spezifisch sollten nur bleiben:
- Installer/Bootstrap,
- optionale Audio/Haptik-Anbindungen,
- kleine UX-Hinweise im Launcher.

## Erkannte Lücke

- Für Windows gibt es derzeit keinen dedizierten Installer-Skriptpfad wie für Android/iOS.
- Empfehlung: optional `install/install_windows.ps1` ergänzen (Paketcheck + Startkommando),
  ohne den Python-Kern zu verzweigen.
