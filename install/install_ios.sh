#!/bin/sh
# VOID — iOS Installer (a-Shell / iSH)
# Installiert VOID robust auf Apple-Geräten.

set -e

INSTALL_DIR="$HOME/games/void"
REPO_URL="https://github.com/IrsanAI/void.git"

printf '[1;31m
'
printf '  ██╗   ██╗ ██████╗ ██╗██████╗ 
'
printf '  ██║   ██║██╔═══██╗██║██╔══██╗
'
printf '  ╚██╗ ██╔╝██║   ██║██║██║  ██║
'
printf '   ╚████╔╝ ╚██████╔╝██║██████╔╝
'
printf '    ╚═══╝   ╚═════╝ ╚═╝╚═════╝ 
'
printf '[0m'
printf 'VOID — iOS Edition wird installiert...

'

play_success_sound() {
    if command -v afplay >/dev/null 2>&1; then
        afplay /System/Library/Sounds/Glass.aiff >/dev/null 2>&1 || true
    elif command -v say >/dev/null 2>&1; then
        say "Void installation complete" >/dev/null 2>&1 || true
    else
        printf ""
    fi
}

# iSH erkennen und Abhängigkeiten sauber installieren
if command -v apk >/dev/null 2>&1; then
    echo "iSH/Alpine erkannt → installiere Basis-Pakete (python3 git curl)..."
    apk update >/dev/null 2>&1 || true
    apk add python3 git curl >/dev/null 2>&1 || apk add python3 git curl
else
    # a-Shell: python3/curl oft vorhanden, trotzdem prüfen
    if ! command -v curl >/dev/null 2>&1; then
        echo "Fehler: curl fehlt. Bitte in a-Shell nachinstallieren."
        exit 1
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Fehler: python3 fehlt. Bitte in deiner iOS-Shell installieren."
        exit 1
    fi
fi

if command -v say >/dev/null 2>&1 || command -v afplay >/dev/null 2>&1; then
    echo "Audio-Ausgabe erkannt (say/afplay verfügbar)."
else
    echo "Hinweis: In dieser Shell sind ggf. nur eingeschränkte Audiofunktionen verfügbar."
fi

mkdir -p "$HOME/games"

# Falls teilweise kaputte Alt-Installation existiert: Backup und neu klonen
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Bestehendes VOID-Repo gefunden → aktualisiere..."
    git -C "$INSTALL_DIR" pull --ff-only || true
else
    if [ -d "$INSTALL_DIR" ] && [ "$(ls -A "$INSTALL_DIR" 2>/dev/null)" != "" ]; then
        BACKUP_DIR="$HOME/games/void_backup_$(date +%Y%m%d_%H%M%S)"
        echo "Teilinstallation erkannt → verschiebe nach $BACKUP_DIR"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
    fi
    echo "Klone VOID Repository..."
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi

# Fallback falls branch 'master' statt 'main' lokal gewünscht ist
if [ ! -f "$INSTALL_DIR/game/void_launcher.py" ]; then
    echo "Fehler: Launcher-Datei fehlt nach Installation."
    exit 1
fi
if [ ! -f "$INSTALL_DIR/game/void_server.py" ]; then
    echo "Fehler: Server-Datei fehlt nach Installation (Abbruch)."
    exit 1
fi

# Ausführbar machen
chmod +x "$INSTALL_DIR"/game/*.py 2>/dev/null || true

# Robuster Startbefehl (unabhängig von Alias und Shell-Neustart)
mkdir -p "$HOME/bin"
cat > "$HOME/bin/void" << EOF
#!/bin/sh
python3 "$INSTALL_DIR/game/void_launcher.py" "\$@"
EOF
chmod +x "$HOME/bin/void"

# PATH dauerhaft ergänzen
if [ -f "$HOME/.profile" ] && ! grep -q 'HOME/bin' "$HOME/.profile" 2>/dev/null; then
    printf '
export PATH="$HOME/bin:$PATH"
' >> "$HOME/.profile"
fi
if [ -f "$HOME/.ashrc" ] && ! grep -q 'HOME/bin' "$HOME/.ashrc" 2>/dev/null; then
    printf '
export PATH="$HOME/bin:$PATH"
' >> "$HOME/.ashrc"
fi

# Optionaler Alias
if [ -f "$HOME/.profile" ] && ! grep -q "alias void=" "$HOME/.profile" 2>/dev/null; then
    printf "alias void='python3 $INSTALL_DIR/game/void_launcher.py'
" >> "$HOME/.profile"
fi

printf '
[1;32mInstallation abgeschlossen![0m
'
play_success_sound
printf 'Start:  %s
' "python3 $INSTALL_DIR/game/void_launcher.py"
printf 'Oder:   %s
' "$HOME/bin/void"
printf '
Wichtig für iSH: Öffne die App neu oder führe aus: export PATH="$HOME/bin:$PATH"
'
