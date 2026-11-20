#!/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="$HOME/.sauvegarde-rr"
VENV="$BASE/venv"
# --composants: the components only, for the Mac app (it shows each "@@ n/4" step).
ONLY=""
[ "$1" = "--composants" ] && ONLY=1
step() {
  [ -n "$ONLY" ] && echo "@@ $1"
}
# The tool's language (its window's setting): French, else English.
FR=""
grep -q '"langue": "fr"' "$BASE/reglages.json" 2>/dev/null && FR=1
t() {
  if [ -n "$FR" ]; then echo "$1"; else echo "$2"; fi
}

pause() {
  [ -n "$ONLY" ] && return
  printf "\n%s" "$(t "Appuyer sur Entrée pour fermer..." "Press Enter to close...")"
  read _
}

portable_python() {
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) FILE="cpython-3.13.17%2B20261021-aarch64-apple-darwin-install_only.tar.gz"; SUM="9c985cbf327425873469896ce748c7134b6deca8edb81e93c589ad2fc5aff445" ;;
    Darwin-x86_64) FILE="cpython-3.13.17%2B20261021-x86_64-apple-darwin-install_only.tar.gz"; SUM="b7d7c2dd63545cabe996191b6f20f0b652c7de123d9ca451dda7e5f1ebbcbbbc" ;;
    *) return 1 ;;
  esac
  step 2/4
  t "Python manque sur cet ordinateur : téléchargement de Python pour l'outil (25 à 75 Mo)..." "Python is missing on this computer: downloading Python for the tool (25 to 75 MB)..."
  mkdir -p "$BASE"
  ARCHIVE="$BASE/python.tar.gz"
  curl -fL --progress-bar -o "$ARCHIVE" "https://github.com/astral-sh/python-build-standalone/releases/download/20261021/$FILE" || return 1
  GOT="$(shasum -a 256 "$ARCHIVE" | cut -d " " -f 1)"
  if [ "$GOT" != "$SUM" ]; then
    t "Le fichier téléchargé n'est pas le bon : réessayer." "The downloaded file is not the right one: try again."
    rm -f "$ARCHIVE"
    return 1
  fi
  rm -rf "$BASE/python"
  tar -xzf "$ARCHIVE" -C "$BASE" || return 1
  rm -f "$ARCHIVE"
}

# New components (another mark) or missing ones: installed again.
if [ "$(cat "$VENV/rr-pret" 2>/dev/null)" != "821fed449874" ] ||
   ! "$VENV/bin/python" -c "import mitmproxy, msgpack, segno, tkinter, UnityPy, numpy, PIL" >/dev/null 2>&1; then
  step 1/4
  PY=""
  for candidate in python3.13 python3.12 python3.14 python3 "$BASE/python/bin/python3"; do
    # never Apple's /usr/bin/python3: too old, or a stub that asks for the developer tools
    if command -v "$candidate" >/dev/null 2>&1 && [ "$(command -v "$candidate")" != /usr/bin/python3 ] &&
       "$candidate" -c 'import sys, tkinter, venv; sys.exit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  done
  if [ -z "$PY" ]; then
    if portable_python && "$BASE/python/bin/python3" -c "import tkinter, venv" >/dev/null 2>&1; then
      PY="$BASE/python/bin/python3"
    else
      t "Impossible d'avoir Python. Vérifier la connexion Internet et réessayer," "Could not get Python. Check the Internet connection and try again,"
      t "ou installer Python : https://www.python.org/downloads/" "or install Python: https://www.python.org/downloads/"
      pause
      exit 1
    fi
  fi
  t "Première utilisation : installation des composants (quelques minutes)..." "First use: installing the components (a few minutes)..."
  step 3/4
  mkdir -p "$BASE"
  rm -rf "$VENV"
  if ! "$PY" -m venv "$VENV"; then
    t "Impossible de créer l'environnement Python." "Could not create the Python environment."
    pause
    exit 1
  fi
  step 4/4
  if ! "$VENV/bin/python" -m pip install --disable-pip-version-check -q "mitmproxy==12.3.1" "msgpack==1.2.4" "segno==1.6.1" "UnityPy==1.25.4" "numpy==2.5.4" "pillow==13.0.0" >"$BASE/pip.log" 2>&1 &&
     ! "$VENV/bin/python" -I "$HERE/moteur/appli_patch/composants.py"; then
    t "L'installation a échoué. Vérifier la connexion Internet et réessayer." "The installation failed. Check the Internet connection and try again."
    pause
    exit 1
  fi
fi

# For the Mac app: the components are ready, and where the tool is (macOS may open the app alone).
echo "821fed449874" > "$VENV/rr-pret"
printf '%s\n' "$HERE" > "$BASE/outil.txt"
[ -n "$ONLY" ] && exit 0
# The app needs macOS 13; before it, the Tk window.
if [ -d "$HERE/Launcher Ratchet Ranger Rumble.app" ] && [ "$(sw_vers -productVersion | cut -d. -f1)" -ge 13 ]; then
  t "L'outil s'ouvre : ce terminal peut être fermé." "The tool opens: this terminal can be closed."
  open "$HERE/Launcher Ratchet Ranger Rumble.app"
  exit 0
fi
t "La fenêtre de l'outil s'ouvre. Laisser ce terminal ouvert tant qu'elle sert." "The tool's window opens. Leave this terminal open while you use it."
if ! "$VENV/bin/python" -I "$HERE/moteur/appli_patch/appli.py"; then
  pause
fi
