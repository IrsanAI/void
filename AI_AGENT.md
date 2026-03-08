# AI_AGENT.md — VOID KI-Architektur (Entwicklerdoku)

Dieses Dokument ist die zentrale Entwickler-Referenz für den aktuellen Stand der VOID-KI.

> Wartungsregel: Wenn sich der KI-Core in `game/void_server.py` (Klasse `VoidAI`) ändert, müssen **AI_AGENT.md** und die KI-bezogenen README-Abschnitte im selben PR mit aktualisiert werden.

## Factsheet (aktueller Stand)

- **Core-Datei:** `game/void_server.py`
- **Hauptklasse:** `VoidAI`
- **Einsatzort:** Server-seitige Steuerung der VOID in Multiplayer-Runden (`_void_loop`).
- **Rolle im Spiel:**
  - Zielauswahl (isolierte Spieler bevorzugen, sonst Führende)
  - Bewegungsentscheidung inkl. Zufallskomponente
  - Aggressionsskalierung über die Zeit
  - Psychologische Chat-/Systemnachrichten
- **Lernansatz (heute):**
  - Bewegungsmuster werden als Delta-Frequenzen (`pattern_weights`) gespeichert.
  - Historie je Spieler in `behavior_memory`.
  - Nächste Position kann über häufigsten Move geschätzt werden (`predict_next_position`).
- **State-Variablen (zentral):**
  - `behavior_memory: dict[player_id, list[(x,y,action,timestamp)]]`
  - `pattern_weights: dict[(dx,dy), count]`
  - `aggression: float` in `[0.0, 1.0]`
  - `prediction_accuracy: list` (derzeit vorbereitet, aber noch nicht voll ausgewertet)
- **Balancing-relevante Konstanten:**
  - `VOID_THINK_INTERVAL`
  - `GRID_SIZE`
  - Eskalationsschritt in `escalate()`
- **Sicherheit/Netz:** keine kryptografische Logik im KI-Core; rein Gameplay-Logik.

## Architektur-Überblick (kurz)

1. Eingehende Spieleraktionen werden serverseitig verarbeitet.
2. KI kann Bewegungen über `record_move(...)` in ein Pattern-Modell übernehmen.
3. In `_void_loop`:
   - aktive Spieler sammeln,
   - Ziel wählen (`choose_target`),
   - VOID bewegen,
   - Treffer/Eliminierung prüfen,
   - psychologische Nachricht senden,
   - Aggression erhöhen.

## Bekannte Grenzen

- Das Modell ist heuristisch/statistisch und kein ML-Modell mit Training/Evaluation.
- `predict_next_position` nutzt aktuell den häufigsten globalen Schritt; Kontext (Map-Zone, Energiezustand, Runde) fließt kaum ein.
- `prediction_accuracy` ist vorbereitet, aber nicht als harte Metrik in Tuning/Logging integriert.

## Nächste logische Optimierungen / Features

1. **Kontextabhängige Zielwahl**
   - Score, Energie, letzte Aktionen, Distanz zur VOID stärker gewichten.
2. **Rundenbasierte Lernfenster**
   - Alte Muster abwerten (Decay), aktuelle Runde höher gewichten.
3. **Vorhersage-Metriken produktiv nutzen**
   - `prediction_accuracy` als KPI loggen, z. B. in `void_logger`.
4. **Verhaltensprofile**
   - „vorsichtig“, „aggressiv“, „teamorientiert“ pro Spieler ableiten.
5. **Schwierigkeitsprofile**
   - KI-Presets (casual/normal/hardcore) über Aggression + Reveal-Rate + Think-Intervall.
6. **Erklärbare KI-Events (Debug Mode)**
   - „Warum wurde Ziel X gewählt?“ als optionales Debug-Event.

## Änderungs-Checkliste für KI-Core-PRs

- [ ] `game/void_server.py` geprüft/angepasst
- [ ] Dieses Factsheet aktualisiert
- [ ] README-KI-Abschnitt synchronisiert
- [ ] Balancing kurz getestet (mind. 1 lokale Runde)
- [ ] `python3 -m py_compile game/void_server.py` erfolgreich
