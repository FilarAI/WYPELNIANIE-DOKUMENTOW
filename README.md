# Wypełnianie dokumentów – FILAR-USŁUGI

Lokalny program: wgrywasz obiegówkę, decyzję o pozwoleniu na budowę lub teczkę dokumentacji
(.docx albo .pdf), sprawdzasz odczytane dane i pobierasz gotowe
wybrane dokumenty: **Pełnomocnictwo**, **PB-5**, **Oświadczenie kierownika budowy**
oraz **Zawiadomienie o zakończeniu budowy**.
Wszystko działa na Twoim komputerze. Pliki nie są nigdzie wysyłane.

## Instalacja na Macu (jednorazowo)
1. Otwórz **Terminal**. Sprawdź, czy działa Python 3.9 lub nowszy: `python3 --version`.
   Jeśli go nie ma, zainstaluj go z [python.org](https://www.python.org/downloads/macos/).
   Do pobrania projektu poleceniem `git clone` może być też potrzebna instalacja narzędzi
   wiersza poleceń Apple. Jeśli Mac o nią poprosi, zaakceptuj i ponów polecenie.
2. Wklej do Terminala kolejno te trzy polecenia (folder programu znajdzie się na pulpicie):

   ```bash
   cd ~/Desktop
   git clone https://github.com/FilarAI/WYPELNIANIE-DOKUMENTOW.git
   bash ~/Desktop/WYPELNIANIE-DOKUMENTOW/instaluj_mac.sh
   ```

3. Na pulpicie pojawi się ikona **Dokumenty FILAR**. Kliknij ją, żeby uruchomić program.
   Ikona wskazuje pobrany folder programu, więc nie przenoś go ani nie usuwaj.

Jeśli folder `WYPELNIANIE-DOKUMENTOW` już jest na pulpicie, zamiast `git clone` zaktualizuj go:

```bash
cd ~/Desktop/WYPELNIANIE-DOKUMENTOW
git pull --ff-only
bash ./instaluj_mac.sh
```

Możesz także pobrać ZIP z GitHuba, rozpakować go i uruchomić
`bash /ścieżka/do/projektu/instaluj_mac.sh`. Instalacja wymaga połączenia z internetem,
żeby pobrać biblioteki Pythona. Jeśli repozytorium jest prywatne, osoba pobierająca musi
mieć do niego dostęp.

Gdyby na pulpicie została stara ikona, uruchom
`bash ~/Desktop/WYPELNIANIE-DOKUMENTOW/instaluj_mac.sh --tylko-ikona`.

Jeśli chcesz zachować poprzednią ikonę i dodać osobny skrót do tej kopii projektu,
uruchom `bash /ścieżka/do/projektu/narzedzia/utworz_skrot_nowej_wersji.sh`.
Na pulpicie powstanie **Dokumenty uzupełnianie NOWE.app**. Skrót wskazuje folder,
w którym uruchomiono skrypt; po przeniesieniu projektu trzeba go utworzyć ponownie.

## Używanie
1. Kliknij ikonę **Dokumenty FILAR**. Otworzy się okno Terminala (nie zamykaj go) i przeglądarka.
2. Dodaj 1–3 pliki i przy każdym wybierz typ: **Obiegówka**, **Decyzja o pozwoleniu na budowę**
   albo **Teczka dokumentacji budowy**. Możesz zacząć także bez obiegówki. PDF z tekstem jest
   odczytywany bez OCR; skanowany PDF korzysta z systemowego OCR macOS (wymaga narzędzia `swift`).
3. Wybierz dokumenty, które chcesz przygotować.
4. Sprawdź dane. Program pokazuje źródło wpisanych wartości i rozbieżności między plikami.
   Przy rozbieżności wybierz propozycję lub wpisz własną wartość. Jeśli pliki wyglądają na
   różne inwestycje, wgraj poprawny zestaw. Gdy decyzja wymienia wiele działek, zaznacz
   te, które mają trafić do dokumentów; możliwa działka drogi jest oznaczona osobno.
   Dodatkowe nieruchomości w PB-5 trafiają na osobne strony załącznika.
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
