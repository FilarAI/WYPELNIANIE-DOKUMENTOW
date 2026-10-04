#!/bin/bash
# Uruchamia program (serwer na 127.0.0.1) i otwiera przeglądarkę. Zamknięcie okna Terminala wyłącza program.
cd "$(dirname "$0")" || exit 1

if [ ! -x .venv/bin/python ]; then
  echo "Pierwsze uruchomienie – instaluję program…"
  bash ./instaluj_mac.sh --bez-ikony || { read -r -p "Instalacja nie powiodła się. Naciśnij Enter, aby zamknąć."; exit 1; }
fi

exec .venv/bin/python -m app.main
