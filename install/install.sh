#!/data/data/com.termux/files/usr/bin/bash
# ═══════════════════════════════════════════════════════════════
#  VOID — Termux Installer
#  Aufruf:
#    curl -fsSL https://raw.githubusercontent.com/IrsanAI/void/master/install/install.sh | bash
# ═══════════════════════════════════════════════════════════════

set -e

# ── Farben ──────────────────────────────────────────────────────
RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
CYAN='\033[96m'; GRAY='\033[90m'; BOLD='\033[1m'; RESET='\033[0m'

r() { echo -e "${RED}$*${RESET}"; }
g() { echo -e "${GREEN}$*${RESET}"; }
y() { echo -e "${YELLOW}$*${RESET}"; }
c() { echo -e "${CYAN}$*${RESET}"; }
b() { echo -e "${BOLD}$*${RESET}"; }
gray() { echo -e "${GRAY}$*${RESET}"; }

# ── Banner ──────────────────────────────────────────────────────
clear
echo ""
gray "  ██╗   ██╗ ██████╗ ██╗██████╗ "
gray "  ██║   ██║██╔═══██╗██║██╔══██╗"
gray "  ╚██╗ ██╔╝██║   ██║██║██║  ██║"
gray "   ╚████╔╝ ╚██████╔╝██║██████╔╝"
gray "    ╚═══╝   ╚═════╝ ╚═╝╚═════╝ "
echo ""
b "  IrsanAI · VOID Game Installer"
gray "  ─────────────────────────────────────────"
echo ""

# ── Prüfe Termux ────────────────────────────────────────────────
if [ ! -d "/data/data/com.termux" ] && [ -z "$TERMUX_VERSION" ]; then
  y "  ⚠ Termux nicht erkannt. Fahre trotzdem fort..."
fi

# ── Install-Verzeichnis ─────────────────────────────────────────
INSTALL_DIR="$HOME/games/void"
mkdir -p "$INSTALL_DIR"

# ── Pakete ──────────────────────────────────────────────────────
echo ""
c "  [1/6] Paketquellen aktualisieren..."
pkg update -y -q 2>/dev/null || apt-get update -q 2>/dev/null || true

c "  [2/6] Python installieren (falls nötig)..."
if ! command -v python3 &>/dev/null; then
  pkg install python -y -q 2>/dev/null || apt-get install python3 -y -q 2>/dev/null
  g "        Python installiert ✓"
else
  g "        Python bereits vorhanden ✓"
fi

c "  [3/6] git installieren (falls nötig)..."
if ! command -v git &>/dev/null; then
  pkg install git -y -q 2>/dev/null || apt-get install git -y -q 2>/dev/null
  g "        git installiert ✓"
else
  g "        git bereits vorhanden ✓"
fi

c "  [4/6] Sound-Komponenten installieren (optional, empfohlen)..."
if ! command -v play &>/dev/null; then
  pkg install sox -y -q 2>/dev/null || apt-get install sox -y -q 2>/dev/null || y "        sox konnte nicht installiert werden."
fi
if ! command -v termux-vibrate &>/dev/null; then
  pkg install termux-api -y -q 2>/dev/null || apt-get install termux-api -y -q 2>/dev/null || y "        termux-api Paket nicht verfügbar."
fi
if command -v termux-vibrate &>/dev/null || command -v play &>/dev/null; then
  g "        Sound-Basis erkannt ✓"
else
  y "        Nur visuelle Effekte verfügbar (kein play/termux-api)."
fi

# ── Repo clonen / aktualisieren ─────────────────────────────────
echo ""
c "  [5/6] VOID herunterladen..."
REPO_URL="https://github.com/IrsanAI/void.git"

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "        Aktualisiere bestehendes Repo..."
  cd "$INSTALL_DIR"
  git pull -q origin master 2>/dev/null && g "        Aktualisiert ✓" || y "        Update übersprungen."
else
  echo "        Klone Repository..."
  git clone --depth=1 -q "$REPO_URL" "$INSTALL_DIR" 2>/dev/null
  if [ $? -eq 0 ]; then
    g "        Repository geklont ✓"
  else
    r "  ✗ Klonen fehlgeschlagen. Prüfe deine Internetverbindung."
    exit 1
  fi
fi

# ── Launcher als ausführbar markieren ───────────────────────────
chmod +x "$INSTALL_DIR/game/void_launcher.py"
chmod +x "$INSTALL_DIR/game/void_solo.py"
chmod +x "$INSTALL_DIR/game/void_server.py"
chmod +x "$INSTALL_DIR/game/void_client.py"

# ── [6/6] Alias + Widget einrichten ─────────────────────────────
c "  [6/6] Alias & Home-Screen Widget einrichten..."

ALIAS_LINE="alias void='python3 $INSTALL_DIR/game/void_launcher.py'"

# Alias in alle Shell-Configs schreiben
for RC in "$HOME/.bashrc" "$HOME/.bash_profile"; do
  if [ -f "$RC" ]; then
    if ! grep -q "alias void=" "$RC" 2>/dev/null; then
      echo "" >> "$RC"
      echo "# VOID Game — IrsanAI" >> "$RC"
      echo "$ALIAS_LINE" >> "$RC"
    fi
  fi
done

# Falls keine RC-Datei existiert, .bashrc anlegen
if [ ! -f "$HOME/.bashrc" ]; then
  echo "# VOID Game — IrsanAI" > "$HOME/.bashrc"
  echo "$ALIAS_LINE" >> "$HOME/.bashrc"
fi

# Sofort in aktuelle Session laden
eval "$ALIAS_LINE" 2>/dev/null || true
g "        Alias 'void' eingerichtet ✓"

# ── Termux:Widget Shortcut anlegen ──────────────────────────────
WIDGET_DIR="$HOME/.shortcuts"
mkdir -p "$WIDGET_DIR"

cat > "$WIDGET_DIR/VOID" << WIDGET_EOF
#!/data/data/com.termux/files/usr/bin/bash
# VOID Game — IrsanAI
# Home-Screen Shortcut via Termux:Widget
python3 $INSTALL_DIR/game/void_launcher.py
WIDGET_EOF

chmod +x "$WIDGET_DIR/VOID"
g "        Home-Screen Widget vorbereitet ✓"


play_success_sound() {
  if command -v play >/dev/null 2>&1; then
    (
      play -n -q synth 0.10 sine 523.25 vol 0.25 >/dev/null 2>&1
      play -n -q synth 0.10 sine 659.25 vol 0.25 >/dev/null 2>&1
      play -n -q synth 0.18 sine 783.99 vol 0.30 >/dev/null 2>&1
    ) || true
  elif command -v termux-vibrate >/dev/null 2>&1; then
    termux-vibrate -d 90 >/dev/null 2>&1 || true
    sleep 0.08
    termux-vibrate -d 140 >/dev/null 2>&1 || true
  fi
}

# ── Zusammenfassung ─────────────────────────────────────────────
echo ""
gray "  ════════════════════════════════════════════"
g "  ✓ VOID erfolgreich installiert!"
play_success_sound
gray "  ════════════════════════════════════════════"
echo ""
b "  Installiert in:"
c "    $INSTALL_DIR"
echo ""
gray "  ─────────────────────────────────────────"
b "  STARTEN — 3 Wege:"
echo ""
echo -e "  ${BOLD}${CYAN}  void${RESET}"
gray "        In Termux tippen — startet sofort."
echo ""
echo -e "  ${BOLD}${CYAN}  python3 $INSTALL_DIR/game/void_launcher.py${RESET}"
gray "        Funktioniert immer, ohne Alias."
echo ""
echo -e "  ${BOLD}${CYAN}  Home-Screen Widget${RESET}"
gray "        1) Termux:Widget installieren:"
gray "           https://f-droid.org/packages/com.termux.widget"
gray "        2) Widget auf Home-Screen legen"
gray "        3) 'VOID' auswählen → Fertig!"
echo ""
gray "  ─────────────────────────────────────────"
echo ""

# ── Direkt starten? ─────────────────────────────────────────────
echo -n "  Jetzt spielen? [J/n] "
read -r choice
if [[ "$choice" =~ ^[nN] ]]; then
    echo ""
    gray "  ┌──────────────────────────────────────┐"
    echo -e "  │  ${BOLD}${CYAN}void${RESET}  ← einfach tippen & Enter      │"
    gray "  └──────────────────────────────────────┘"
    echo ""
else
    echo ""
    python3 "$INSTALL_DIR/game/void_launcher.py"
fi
