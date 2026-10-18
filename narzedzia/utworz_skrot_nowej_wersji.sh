#!/bin/bash
# Osobny skrót na Biurku do tej kopii repozytorium. Nie usuwa poprzedniej aplikacji.
set -euo pipefail

KATALOG="$(cd "$(dirname "$0")/.." && pwd)"
APLIKACJA="${1:-$HOME/Desktop/Dokumenty uzupełnianie NOWE.app}"
IKONA="$KATALOG/ikona/ikona.icns"

if [ -e "$APLIKACJA" ]; then
  echo "Skrót już istnieje: $APLIKACJA" >&2
  exit 1
fi
if [ ! -x "$KATALOG/.venv/bin/python" ]; then
  echo "Brak środowiska Pythona. Uruchom najpierw: bash $KATALOG/instaluj_mac.sh --bez-ikony" >&2
  exit 1
fi

SCIEZKA_JS="$("$KATALOG/.venv/bin/python" -c 'import json, sys; print(json.dumps(sys.argv[1]))' "$KATALOG/start.command")"
osacompile -l JavaScript -o "$APLIKACJA" -e "function run() {
  ObjC.import('Foundation');
  var proces = \$.NSTask.alloc.init;
  proces.launchPath = '/usr/bin/open';
  proces.arguments = \$.NSArray.arrayWithObject($SCIEZKA_JS);
  proces.launchAndReturnError(null);
}"
if [ -f "$IKONA" ]; then
  ZASOBY="$APLIKACJA/Contents/Resources"
  cp "$IKONA" "$ZASOBY/applet.icns"
  rm -f "$ZASOBY/Assets.car"
  /usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$APLIKACJA/Contents/Info.plist" >/dev/null 2>&1 || true
fi
codesign --force --sign - "$APLIKACJA" >/dev/null
codesign --verify --deep --strict "$APLIKACJA"
echo "Utworzono skrót: $APLIKACJA"
echo "Uruchamia folder: $KATALOG"
