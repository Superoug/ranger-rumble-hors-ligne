#!/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="$HOME/.sauvegarde-rr"
VENV="$BASE/venv"

pause() {
  printf "\nAppuie sur Entrée pour fermer..."
  read _
}

if ! "$VENV/bin/python" -c "import mitmproxy, msgpack, segno, tkinter" >/dev/null 2>&1; then
  PY=""
  for candidate in python3.14 python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
      if "$candidate" -c "import tkinter" >/dev/null 2>&1; then
        PY="$candidate"
        break
      fi
      NO_TK="$candidate"
    fi
  done
  if [ -z "$PY" ]; then
    if [ -n "$NO_TK" ]; then
      echo "Python est là, mais sans Tkinter (ce qui fait la fenêtre)."
      echo "Linux : installe le paquet python3-tk."
      echo "Mac avec Homebrew : brew install python-tk, ou le Python de https://www.python.org/downloads/"
    else
      echo "Il faut Python 3.12 ou plus récent."
      echo "Mac : https://www.python.org/downloads/"
      echo "Linux : installe les paquets python3, python3-venv et python3-tk."
    fi
    pause
    exit 1
  fi
  echo "Première utilisation : installation des composants (quelques minutes)..."
  mkdir -p "$BASE"
  rm -rf "$VENV"
  if ! "$PY" -m venv "$VENV"; then
    echo "Impossible de créer l'environnement Python (Linux : installe python3-venv)."
    pause
    exit 1
  fi
  if ! "$VENV/bin/python" -m pip install --disable-pip-version-check -q "mitmproxy==12.3.1" "msgpack==1.2.4" "segno==1.6.1"; then
    echo "L'installation a échoué. Vérifie la connexion Internet et réessaie."
    pause
    exit 1
  fi
fi

echo "La fenêtre de l'outil s'ouvre. Laisse ce terminal ouvert tant qu'elle sert."
if ! "$VENV/bin/python" -I "$HERE/moteur/appli_patch/appli.py"; then
  pause
fi
