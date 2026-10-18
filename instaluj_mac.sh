#!/bin/bash
# Jednorazowa instalacja na macOS: środowisko Pythona, biblioteki i ikona „Dokumenty FILAR” na pulpicie.
# Użycie: bash instaluj_mac.sh                 pełna instalacja
#         bash instaluj_mac.sh --bez-ikony     bez ikony na pulpicie (używa tego start.command)
#         bash instaluj_mac.sh --tylko-ikona   tylko odtworzenie ikony na pulpicie (szybko, bez instalacji bibliotek)
set -e
KATALOG="$(cd "$(dirname "$0")" && pwd)"
cd "$KATALOG"

utworz_ikone() {
  APLIKACJA="$HOME/Desktop/Dokumenty FILAR.app"
  IKONA="$KATALOG/ikona/ikona.icns"
  rm -rf "$APLIKACJA"
  URUCHOM="do shell script \"open \" & quoted form of \"$KATALOG/start.command\""
  # „open location” = start z linku dokumentyfilar:// (np. z ekranu aplikacji biura w przeglądarce).
  osacompile -o "$APLIKACJA" -e "on run" -e "$URUCHOM" -e "end run" \
    -e "on open location adres" -e "$URUCHOM" -e "end open location"
  /usr/libexec/PlistBuddy \
    -c "Add :CFBundleURLTypes array" \
    -c "Add :CFBundleURLTypes:0 dict" \
    -c "Add :CFBundleURLTypes:0:CFBundleURLName string pl.filar.dokumenty" \
    -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes array" \
    -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes:0 string dokumentyfilar" \
    "$APLIKACJA/Contents/Info.plist"

  if [ -f "$IKONA" ]; then
    ZASOBY="$APLIKACJA/Contents/Resources"
    cp "$IKONA" "$ZASOBY/applet.icns"
    # Nowszy macOS bierze ikonę z katalogu grafik (Assets.car), a nie z applet.icns – usuwamy go
    # razem z odwołaniem w Info.plist, żeby została nasza ikona.
    rm -f "$ZASOBY/Assets.car"
    /usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$APLIKACJA/Contents/Info.plist" >/dev/null 2>&1 || true
  fi
  # Ponowny podpis po zmianie Info.plist i zasobów (podpis lokalny, jak przy osacompile).
  codesign --force --sign - "$APLIKACJA" >/dev/null 2>&1 || true
  if [ -f "$IKONA" ]; then
    # Ikona ustawiona bezpośrednio w Finderze – działa także wtedy, gdy macOS pamięta starą ikonę z tej samej ścieżki.
    IKONA="$IKONA" APLIKACJA="$APLIKACJA" osascript -l JavaScript -e '
      ObjC.import("AppKit");
      var env = $.NSProcessInfo.processInfo.environment;
      var obraz = $.NSImage.alloc.initWithContentsOfFile(env.objectForKey("IKONA"));
      $.NSWorkspace.sharedWorkspace.setIconForFileOptions(obraz, env.objectForKey("APLIKACJA"), 0);' >/dev/null 2>&1 || true
    touch "$APLIKACJA"
  fi
  # Rejestracja w systemie: ikona i adres dokumentyfilar://
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
    -f "$APLIKACJA" >/dev/null 2>&1 || true
  echo "Dodano ikonę „Dokumenty FILAR” na pulpicie – uruchamia program z folderu:"
  echo "  $KATALOG"
}

if [ "$1" = "--tylko-ikona" ]; then
  utworz_ikone
  exit 0
fi

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
  utworz_ikone
fi

echo "Gotowe. Uruchom program, klikając ikonę „Dokumenty FILAR” na pulpicie."
