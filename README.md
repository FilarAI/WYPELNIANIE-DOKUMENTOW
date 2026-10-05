# Wypełnianie dokumentów – FILAR-USŁUGI

Lokalny program: wgrywasz obiegówkę (.docx), sprawdzasz odczytane dane i pobierasz gotowe
**Pełnomocnictwo** oraz **PB-5** (oświadczenie o prawie do dysponowania nieruchomością).
Wszystko działa na Twoim komputerze. Pliki nie są nigdzie wysyłane.

## Instalacja na Macu (jednorazowo)
1. Potrzebny jest Python 3.9 lub nowszy. Sprawdź w Terminalu: `python3 --version`.
   Jeśli go nie ma, Mac zaproponuje instalację narzędzi deweloperskich. Możesz też pobrać Pythona z python.org.
2. Pobierz projekt z GitHuba (przycisk **Code → Download ZIP** na właściwej gałęzi) i rozpakuj go,
   np. do katalogu `Dokumenty`.
3. Otwórz Terminal, przeciągnij do niego plik `instaluj_mac.sh`, dopisz przed nim `bash ` i naciśnij Enter:
   ```
   bash /ścieżka/do/projektu/instaluj_mac.sh
   ```
4. Na pulpicie pojawi się ikona **Dokumenty FILAR**.
   Gdyby na pulpicie została stara ikona, uruchom w Terminalu `bash /ścieżka/do/projektu/instaluj_mac.sh --tylko-ikona`.

## Używanie
1. Kliknij ikonę **Dokumenty FILAR**. Otworzy się okno Terminala (nie zamykaj go) i przeglądarka.
2. Przeciągnij obiegówkę na stronę.
3. Sprawdź dane. Żółte ramki oznaczają niespójności w obiegówce. Popraw, co trzeba.
4. Wybierz folder (przycisk **Wybierz…**) i kliknij **Zapisz dokumenty w folderze**. Program zapamięta folder.
   Możesz też kliknąć **Pobierz jako ZIP**.
5. Aby wyłączyć program, kliknij **Zakończ program** albo zamknij okno Terminala.

Szczegóły techniczne: [CLAUDE.md](CLAUDE.md).
