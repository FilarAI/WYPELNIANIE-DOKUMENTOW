# Wypełnianie dokumentów – FILAR-USŁUGI

Lokalny program: wgrywasz obiegówkę, decyzję o pozwoleniu na budowę lub teczkę dokumentacji
(.docx albo .pdf), sprawdzasz odczytane dane i pobierasz gotowe
wybrane dokumenty: **Pełnomocnictwo**, **PB-5**, **PB-2**, **PB-2a**, **PB-7**, **PB-9**, **PB-1**, **Oświadczenie kierownika budowy**,
**Zawiadomienie o zakończeniu budowy**, **BA-4 — wniosek o wydanie dziennika budowy lub rozbiórki**
oraz **Zgłoszenie zmian danych ewidencji gruntów i budynków (EGiB)**.
Możesz też wybrać **OŚ-6165 — zaświadczenie o objęciu gruntu uproszczonym planem urządzenia lasu**.
Osobno dostępny jest **EGiB — wniosek o wydanie wypisu lub wyrysu z operatu ewidencyjnego**.
Możesz także wygenerować **Formularz P — wniosek o udostępnienie materiałów powiatowego zasobu geodezyjnego i kartograficznego**.
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

**Aktualizacje są automatyczne:** przy każdym kliknięciu ikony program pobiera najnowszą wersję
z gałęzi `main` (bez internetu startuje obecna). Do `main` wysyłaj więc tylko sprawdzone wersje.

Ręczna aktualizacja (np. gdy zmienił się `instaluj_mac.sh`):

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
   W kroku **Sprawdź dane** rozwiń opcję **Wygląd uzupełnionych danych** na samej górze formularza. Pozwala wybrać rozmiar zgodny ze wzorem
   lub większy o 2 punkty, pogrubienie oraz kolor czarny albo ciemnoniebieski. Podgląd pokazuje wybrany wygląd.
   Ustawienia obejmują wpisane wartości we wszystkich wybranych Wordach, także w załącznikach PB-5.
   Stała treść i puste miejsca zachowują wygląd wzoru. Większa czcionka może zwiększyć liczbę stron.
6. Aby wyłączyć program, kliknij **Zakończ program** albo zamknij okno Terminala.

Nowe wzory pochodzą z dokumentów dostarczonych przez użytkownika. Przed złożeniem
sprawdź daty i podstawy prawne wydrukowanych wzorów oraz podpisz dokumenty.

Szczegóły techniczne: [CLAUDE.md](CLAUDE.md).

## BA-4 — wydanie dziennika budowy lub rozbiórki
W drugim kroku zaznacz BA-4. Program przepisuje inwestorów i inwestycję z obiegówki oraz znak, datę i organ z decyzji o pozwoleniu na budowę lub rozbiórkę. W trzecim kroku samodzielnie wybierz rodzaj robót, podstawę, pierwszy lub kolejny dziennik i oświadczenia. Dla kolejnego dziennika podaj poprzedni numer i jego stan. Nieprawidłowe daty, sprzeczne warianty, brak oświadczeń lub wymaganych danych blokują generowanie BA-4. Niepasujące warianty są skreślane, podpis pozostaje pusty. Wzór odtworzono ze zdjęcia użytkownika, z adresem Starosty Nowotarskiego.

## Zgłoszenie zmian danych EGiB
W drugim kroku wybierz zgłoszenie zmian danych ewidencji gruntów i budynków. W trzecim sprawdź zgłaszającego, adres korespondencyjny (domyślnie pierwszego inwestora), gminę i proponowany obręb. Numery działek pochodzą ze wspólnej sekcji nieruchomości. Wybierz rolę właściciela lub władającego, wpisz opis zmian i ewentualne załączniki. Zgoda na korespondencję elektroniczną jest opcjonalna i niezaznaczona; jej zaznaczenie wymaga poprawnego adresu e-mail. Błędne daty, numery działek, niezgodność gminy z rozpoznanym identyfikatorem i brak wymaganych pól blokują generowanie. Pełna klauzula informacyjna ze zdjęcia pozostaje w dokumencie, a podpis jest pusty. Wybrana rola jest podkreślona zgodnie ze wzorem.

## Pełnomocnictwo do spraw EGiB
To osobny druk od pełnomocnictwa do inwestycji budowlanej. Dla każdej osoby udzielającej pełnomocnictwa wpisz numer dowodu, organ wydający i PESEL; dane dokumentu pełnomocnika również wpisuje się w kroku 3. Wybierz jeden z dwóch zakresów ze zdjęcia. Na wydruku zostanie zaznaczony odpowiedni kwadrat, a drugi wariant będzie przekreślony. Podpis mocodawcy pozostaje pusty.

## OŚ-6165 — zaświadczenie o objęciu gruntu uproszczonym planem urządzenia lasu
Wybierz OŚ-6165, aby przygotować dwustronicowy wniosek Starostwa Powiatowego w Nowym Targu do celów notarialnych. Wnioskodawca, działki i miejscowość są domyślnie pobierane z obiegówki; możesz je poprawić, podać telefon i datę oraz wybrać sposób odbioru. Druk zawiera opłatę skarbową 17 zł i klauzulę RODO na drugiej stronie.

## EGiB — wypis lub wyrys
To wniosek o udostępnienie wypisów/wyrysów z operatu EGiB, odrębny od zgłoszenia zmian danych ewidencyjnych i pełnomocnictwa EGiB. Dane wnioskodawcy, gminy, obrębu i działek są wstępnie przepisywane z obiegówki. Zaznacz zamawiane materiały, podstawę dostępu do danych, postać dokumentów i sposób odbioru. Wniosek zawiera pola na numery budynków/lokali, księgę wieczystą oraz interes prawny.

## Formularz P — materiały zasobu geodezyjnego
Wniosek o udostępnienie map, danych EGiB, GESUT, BDOT500 i raportów. Wnioskodawca, adres i położenie działki są domyślnie pobierane z obiegówki. Wybierz materiały, jeden cel udostępnienia i sposób odbioru. W zależności od zakresu Starostwo może wymagać formularza uszczegóławiającego P1–P6.

## Ręczne pliki testowe
Folder `manual_tests/` zawiera fikcyjne obiegówki, po jednym poprawnym wygenerowanym dokumencie dla każdego z 15 typów oraz scenariusz z brakującym polem i oczekiwanym komunikatem walidacji. Pakiet można odtworzyć poleceniem `.venv/bin/python narzedzia/generuj_pliki_testowe.py`.
