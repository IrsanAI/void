# LOP — Live Open Points / Roadmap

> Zweck: zentrale, laufend aktualisierte Liste aller offenen Aufgaben für VOID.
> Jede PR sollte mindestens einen Punkt in dieser Datei aktualisieren.

## Legende
- [ ] Offen
- [~] In Arbeit
- [x] Erledigt
- Priorität: P0 (kritisch), P1 (hoch), P2 (mittel), P3 (nice-to-have)

---

## P0 — Multiplayer über Internet stabil

- [x] **Launcher VPN/Netz-Check Option** (`[4]`) mit klarer Checkliste eingebaut.
- [x] **`void_netcheck.py`** erstellt (lokale IP, Tailscale-IP, Port-Check 7777).
- [x] Client-Fehlertexte bei Timeout verbessert (NAT/CGNAT/VPN-Hinweise + Netcheck-Befehl).
- [x] **Relay-Prototyp v0.1** (Cloud/VPS): Host+Client verbinden outbound, Join per Room-Code (`void_relay.py`).
- [ ] Heartbeat/Keepalive & Auto-Reconnect für Relay-Verbindungen.
- [ ] Minimales Matchmaking (Room erstellen/joinen) mit Code-Lebensdauer.

## P1 — Session/Identity (globale VOID-ID)

- [ ] Kryptografische VOID-ID (Public/Private Key) pro Spieler.
- [ ] Signierte Session-Tokens (Replay-Schutz + Ablaufzeit).
- [ ] Nickname-Claim-Service (weltweit eindeutig, reservierbar).
- [ ] Gerätetausch-Flow: Key-Export/Import (Backup sicher machen).

## P1 — Mobile Layout-Stabilität

- [~] Safe Render Mode für Mobile aktiv (reduziertes Redraw / robustere Darstellung).
- [ ] Adaptive safe margins je Terminalgröße (Android/iOS Profile).
- [ ] Optionaler Minimal-UI-Modus für sehr kleine/instabile Terminals.
- [ ] Dedizierter Resize-Stresstest (Keyboard auf/zu, Rotation, split-screen).

## P2 — Audio/UX

- [x] Sound-Diagnose-Tool vorhanden (`void_sound_diagnose.py`).
- [ ] Preset „silent-safe“ für Umgebungen ohne Audio-Backend.
- [ ] Installer: explizite Audio-Backend Zusammenfassung nach Installation.
- [ ] GH-Page: echte Mehrsprachigkeit DE/EN statt Platzhalter-Toggle.

## P2 — Installer & Runtime Hardening

- [x] iOS-Installer robuster (iSH/a-Shell Pfad + `~/bin/void`).
- [x] Termux-Installer mit PATH-`void`-Befehl.
- [ ] Installer-Selftest: prüft alle Kern-Dateien + `python3` Laufbarkeit.
- [ ] Post-Install „doctor" Kommando (`void doctor`) für Schnell-Diagnose.

## P3 — Dev/Quality

- [x] KI-Architektur-Doku ergänzt (`AI_AGENT.md`) + Wartungshinweis im KI-Core.
- [ ] Smoke-Test-Skript für Solo/Client/Server Startpfade.
- [ ] Strukturierte Error-Codes im Client/Server (statt nur freie Texte).
- [ ] Kleine Telemetrie-Option (opt-in) für Verbindungsfehler-Statistik.

---

## Nächster Sprint (vereinbart)

1. Relay v0.1 stabilisieren (Retries, bessere Fehlermeldungen, optional mehrere Joiner/Rooms).
2. Heartbeat/Keepalive + Auto-Reconnect für Relay-Verbindungen.
3. Kurzer End-to-End Testplan für Android ↔ iOS über Mobilfunk + VPN + Relay.
