#!/bin/sh
# VOID — iOS Installer (a-Shell / iSH)
# Installiert VOID auf Apple-Geräten.

echo "\033[1;31m"
echo "  ██╗   ██╗ ██████╗ ██╗██████╗ "
echo "  ██║   ██║██╔═══██╗██║██╔══██╗"
echo "  ╚██╗ ██╔╝██║   ██║██║██║  ██║"
echo "   ╚████╔╝ ╚██████╔╝██║██████╔╝"
echo "    ╚═══╝   ╚═════╝ ╚═╝╚═════╝ "
echo "\033[0m"
echo "VOID — iOS Edition wird installiert...\n"

# Abhängigkeiten prüfen (iSH nutzt apk, a-Shell hat curl eingebaut)
if ! command -v curl >/dev/null 2>&1; then
    echo "curl nicht gefunden. Versuche Installation via apk (iSH)..."
    if command -v apk >/dev/null 2>&1; then
        apk add curl git python3
    else
        echo "Fehler: Paketmanager nicht gefunden. Bitte installiere curl manuell."
        exit 1
    fi
fi

# Verzeichnis erstellen
mkdir -p ~/games/void
cd ~/games/void

# Repository klonen (falls git vorhanden) oder Dateien laden
if command -v git >/dev/null 2>&1; then
    echo "Klone Repository via git..."
    git clone https://github.com/IrsanAI/void.git .
else
    echo "Git nicht gefunden. Lade Dateien manuell..."
    # Fallback: curl einzelne Dateien (vereinfacht)
    mkdir -p game
    curl -L https://raw.githubusercontent.com/IrsanAI/void/master/game/void_launcher.py -o game/void_launcher.py
    curl -L https://raw.githubusercontent.com/IrsanAI/void/master/game/void_solo_enhanced.py -o game/void_solo_enhanced.py
    curl -L https://raw.githubusercontent.com/IrsanAI/void/master/game/void_sound_enhanced.py -o game/void_sound_enhanced.py
    curl -L https://raw.githubusercontent.com/IrsanAI/void/master/game/void_layout_enhanced.py -o game/void_layout_enhanced.py
fi

# Alias erstellen (a-Shell nutzt 'alias')
if [ -f "$HOME/.profile" ]; then
    echo "alias void='python3 ~/games/void/game/void_launcher.py'" >> ~/.profile
    echo "Alias 'void' zu .profile hinzugefügt."
fi

echo "\n\033[1;32mInstallation abgeschlossen!\033[0m"
echo "Starte das Spiel mit: \033[1mpython3 ~/games/void/game/void_launcher.py\033[0m"
echo "Oder tippe einfach 'void' nach einem Neustart der App."
