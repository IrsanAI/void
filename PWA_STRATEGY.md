# VOID PWA Strategy (Exploration)

## Einschätzung zur Idee

Kurz: **Sehr stark und sinnvoll** – als zusätzlicher Produktpfad.

Die PWA-Transformation adressiert den größten Reibungspunkt von VOID (Onboarding über Shell/Installer),
ohne den Terminal-Charme aufzugeben.

## Realistischer Zielzustand

- Browser-Start via URL (`void.irsan.ai`) statt lokaler Installer.
- Terminal-Look & Feel über `xterm.js`.
- Python-Game-Logik per `Pyodide` im Browser (hohe Code-Wiederverwendung).
- Multiplayer über WebSockets (Relay-Logik serverseitig, keine CGNAT-Probleme auf Clientseite).

## Warum diese Richtung passt

1. **Cross-Device by default**: Android, iOS, Windows, macOS, Linux über Browser.
2. **Installationshürde sinkt**: kein Python-/Git-Setup nötig für Spieler.
3. **Architektur bleibt stimmig**: KI- und Game-Logik kann in Python bleiben.

## Risiken

- Pyodide-Ladezeit (WASM-Größe) → braucht guten Boot-Screen.
- Audio/Haptik im Browser bleibt plattformabhängig.
- Multiplayer-Protokoll muss für WebSocket-Pfad sauber abstrahiert werden.

## Empfohlener nächster Schritt

**Proof of Concept (PoC)** zuerst:
- `xterm.js` rendern,
- `Pyodide` laden,
- einfacher Python-Heartbeat im Terminal (`VOID is watching...`).

Wenn dieses Fundament stabil läuft, kann die nächste Stufe folgen:
- Grid-Render,
- Input-Handling,
- KI-Tick,
- Netzwerk-Adapter.


## Aktueller PoC-Status

- `docs/pwa_starter.html` enthält jetzt ein interaktives Mini-Grid (xterm.js + Pyodide),
  Keyboard-Input (WASD/Pfeile), einen einfachen VOID-Chase-Loop und Glitch-Pulse bei Gefahr.
- Damit ist der "Heartbeat"-Schritt überschritten; nächster Schritt ist die Portierung echter Game-State-Strukturen aus `void_solo_enhanced.py`.

- Zusätzlich wurden `docs/manifest.webmanifest` und `docs/sw.js` ergänzt (PWA-Grundlagen: installierbar + Cache-Basis).
