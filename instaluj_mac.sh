#!/bin/bash
# Jednorazowa instalacja na macOS: środowisko Pythona, biblioteki i ikona „Dokumenty FILAR” na pulpicie.
# Użycie: bash instaluj_mac.sh   (opcja --bez-ikony pomija tworzenie ikony)
set -e
KATALOG="$(cd "$(dirname "$0")" && pwd)"
cd "$KATALOG"

if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
  echo "Brak Pythona 3.9 lub nowszego."
  echo "Zainstaluj go z https://www.python.org/downloads/macos/ albo poleceniem: xcode-select --install"
  exit 1
fi

# Pliki pobrane z internetu macOS oznacza jako „z kwarantanny” – zdejmujemy to z katalogu programu.
xattr -dr com.apple.quarantine "$KATALOG" 2>/dev/null || true
chmod +x "$KATALOG/start.command" "$KATALOG/instaluj_mac.sh"

echo "Tworzę środowisko Pythona…"
python3 -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
echo "Instaluję biblioteki…"
.venv/bin/python -m pip install --quiet -r requirements.txt

if [ "$1" != "--bez-ikony" ]; then
  APLIKACJA="$HOME/Desktop/Dokumenty FILAR.app"
  rm -rf "$APLIKACJA"
  osacompile -o "$APLIKACJA" -e "do shell script \"open \" & quoted form of \"$KATALOG/start.command\""
  echo "Dodano ikonę „Dokumenty FILAR” na pulpicie – uruchamia program z folderu:"
  echo "  $KATALOG"
fi

echo "Gotowe. Uruchom program, klikając ikonę „Dokumenty FILAR” na pulpicie."
