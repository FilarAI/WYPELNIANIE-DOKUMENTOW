# Wypełnianie dokumentów – FILAR-USŁUGI

Lokalny program: wgrywasz obiegówkę (.docx), sprawdzasz odczytane dane i pobierasz gotowe
wybrane dokumenty: **Pełnomocnictwo**, **PB-5**, **Oświadczenie kierownika budowy**
oraz **Zawiadomienie o zakończeniu budowy**.
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

Jeśli chcesz zachować poprzednią ikonę i dodać osobny skrót do tej kopii projektu,
uruchom `bash /ścieżka/do/projektu/narzedzia/utworz_skrot_nowej_wersji.sh`.
Na pulpicie powstanie **Dokumenty uzupełnianie NOWE.app**. Skrót wskazuje folder,
w którym uruchomiono skrypt; po przeniesieniu projektu trzeba go utworzyć ponownie.

## Używanie
1. Kliknij ikonę **Dokumenty FILAR**. Otworzy się okno Terminala (nie zamykaj go) i przeglądarka.
2. Przeciągnij obiegówkę na stronę.
3. Wybierz dokumenty, które chcesz przygotować.
4. Sprawdź dane. Żółte ramki oznaczają niespójności w obiegówce. Popraw, co trzeba.
   Dane kierownika budowy są ustawione na Bartłomieja Filara. Pozostałe nieznane dane
   i oświadczenia uzupełnij po sprawdzeniu; program nie zaznacza ich sam.
   Nad zapisem zobaczysz podsumowanie pustych pól i niewybranych odpowiedzi; kliknij pozycję,
   aby przejść do pola. Podsumowanie nie blokuje generowania.
5. Wybierz folder (przycisk **Wybierz…**) i kliknij **Zapisz dokumenty w folderze**. Program zapamięta folder.
   Możesz też kliknąć **Pobierz jako ZIP**.
6. Aby wyłączyć program, kliknij **Zakończ program** albo zamknij okno Terminala.

Nowe wzory pochodzą z dokumentów dostarczonych przez użytkownika. Przed złożeniem
sprawdź daty i podstawy prawne wydrukowanych wzorów oraz podpisz dokumenty.

Szczegóły techniczne: [CLAUDE.md](CLAUDE.md).
