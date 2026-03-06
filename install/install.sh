#!/data/data/com.termux/files/usr/bin/bash
# ═══════════════════════════════════════════════════════════════
#  VOID — Termux Installer
#  Aufruf:
#    curl -fsSL https://raw.githubusercontent.com/IrsanAI/void/main/install/install.sh | bash
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
c "  [1/4] Paketquellen aktualisieren..."
pkg update -y -q 2>/dev/null || apt-get update -q 2>/dev/null || true

c "  [2/4] Python installieren (falls nötig)..."
if ! command -v python3 &>/dev/null; then
  pkg install python -y -q 2>/dev/null || apt-get install python3 -y -q 2>/dev/null
  g "        Python installiert ✓"
else
  g "        Python bereits vorhanden ✓"
fi

c "  [3/4] git installieren (falls nötig)..."
if ! command -v git &>/dev/null; then
  pkg install git -y -q 2>/dev/null || apt-get install git -y -q 2>/dev/null
  g "        git installiert ✓"
else
  g "        git bereits vorhanden ✓"
fi

# ── Repo clonen / aktualisieren ─────────────────────────────────
echo ""
c "  [4/4] VOID herunterladen..."
REPO_URL="https://github.com/IrsanAI/void.git"

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "        Aktualisiere bestehendes Repo..."
  cd "$INSTALL_DIR"
  git pull -q origin main 2>/dev/null && g "        Aktualisiert ✓" || y "        Update übersprungen."
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

# ── Alias in .bashrc / .bash_profile anlegen ────────────────────
ALIAS_LINE="alias void='python3 $INSTALL_DIR/game/void_launcher.py'"

for RC in "$HOME/.bashrc" "$HOME/.bash_profile" "$PREFIX/etc/bash.bashrc"; do
  if [ -f "$RC" ] && ! grep -q "alias void=" "$RC" 2>/dev/null; then
    echo "$ALIAS_LINE" >> "$RC"
  fi
done

# Auch in aktuelle Session laden
eval "$ALIAS_LINE" 2>/dev/null || true

# ── Zusammenfassung ─────────────────────────────────────────────
echo ""
gray "  ─────────────────────────────────────────"
g "  ✓ VOID erfolgreich installiert!"
gray "  ─────────────────────────────────────────"
echo ""
b "  Installiert in:  $INSTALL_DIR"
echo ""
b "  Starten:"
echo ""
c "    python3 $INSTALL_DIR/game/void_launcher.py"
echo ""
y "    — ODER nach Neustart von Termux —"
echo ""
c "    void"
echo ""
gray "  ─────────────────────────────────────────"
echo ""

# ── Direkt starten? ─────────────────────────────────────────────
read -r -p "  Jetzt spielen? [J/n] " choice
case "$choice" in
  [nN]*)
    echo ""
    gray "  Starte später mit: void"
    echo ""
    ;;
  *)
    echo ""
    exec python3 "$INSTALL_DIR/game/void_launcher.py"
    ;;
esac
