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
c "  [1/5] Paketquellen aktualisieren..."
pkg update -y -q 2>/dev/null || apt-get update -q 2>/dev/null || true

c "  [2/5] Python installieren (falls nötig)..."
if ! command -v python3 &>/dev/null; then
  pkg install python -y -q 2>/dev/null || apt-get install python3 -y -q 2>/dev/null
  g "        Python installiert ✓"
else
  g "        Python bereits vorhanden ✓"
fi

c "  [3/5] git installieren (falls nötig)..."
if ! command -v git &>/dev/null; then
  pkg install git -y -q 2>/dev/null || apt-get install git -y -q 2>/dev/null
  g "        git installiert ✓"
else
  g "        git bereits vorhanden ✓"
fi

# ── Repo clonen / aktualisieren ─────────────────────────────────
echo ""
c "  [4/5] VOID herunterladen..."
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

# ── [5/5] Alias + Widget einrichten ─────────────────────────────
c "  [5/5] Alias & Home-Screen Widget einrichten..."

ALIAS_LINE="alias void='python3 $INSTALL_DIR/game/void_launcher.py'"

# Alias in alle Shell-Configs schreiben
ALIAS_ADDED=false
for RC in "$HOME/.bashrc" "$HOME/.bash_profile" "$PREFIX/etc/bash.bashrc"; do
  if [ -f "$RC" ] && ! grep -q "alias void=" "$RC" 2>/dev/null; then
    echo "" >> "$RC"
    echo "# VOID Game — IrsanAI" >> "$RC"
    echo "$ALIAS_LINE" >> "$RC"
    ALIAS_ADDED=true
  fi
done

# Falls keine RC-Datei existiert, .bashrc anlegen
if [ ! -f "$HOME/.bashrc" ]; then
  echo "# VOID Game — IrsanAI" > "$HOME/.bashrc"
  echo "$ALIAS_LINE" >> "$HOME/.bashrc"
  ALIAS_ADDED=true
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

# ── Zusammenfassung ─────────────────────────────────────────────
echo ""
gray "  ════════════════════════════════════════════"
g "  ✓ VOID erfolgreich installiert!"
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
read -r -p "  Jetzt spielen? [J/n] " choice
case "$choice" in
  [nN]*)
    echo ""
    gray "  ┌──────────────────────────────────────┐"
    echo -e "  │  ${BOLD}${CYAN}void${RESET}  ← einfach tippen & Enter      │"
    gray "  └──────────────────────────────────────┘"
    echo ""
    ;;
  *)
    echo ""
    exec python3 "$INSTALL_DIR/game/void_launcher.py"
    ;;
esac
