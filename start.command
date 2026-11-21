#!/bin/bash
# Uruchamia program (serwer na 127.0.0.1) i otwiera przeglądarkę. Zamknięcie okna Terminala wyłącza program.
cd "$(dirname "$0")" || exit 1

# Aktualizacja z GitHuba przy każdym starcie. Bez internetu startuje obecna wersja.
STARA_WERSJA="$(git rev-parse HEAD 2>/dev/null)"
if [ -n "$STARA_WERSJA" ]; then
  echo "Sprawdzam aktualizacje…"
  git pull --ff-only -q 2>/dev/null || echo "Bez aktualizacji (brak internetu?) – uruchamiam obecną wersję."
fi

if [ ! -x .venv/bin/python ]; then
  echo "Pierwsze uruchomienie – instaluję program…"
  bash ./instaluj_mac.sh --bez-ikony || { read -r -p "Instalacja nie powiodła się. Naciśnij Enter, aby zamknąć."; exit 1; }
elif [ -n "$STARA_WERSJA" ] && ! git diff --quiet "$STARA_WERSJA" HEAD -- requirements.txt; then
  echo "Instaluję nowe biblioteki…"
  .venv/bin/python -m pip install --quiet -r requirements.txt
fi

exec .venv/bin/python -m app.main
