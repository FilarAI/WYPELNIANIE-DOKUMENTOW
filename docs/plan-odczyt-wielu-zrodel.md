# Plan odczytu obiegówki, decyzji i dokumentacji budowy

## Cel

Program przyjmuje jeden lub kilka plików DOCX/PDF z ręcznie wskazanym rodzajem źródła. Odczytuje wyłącznie dane potrzebne do czterech obecnie generowanych dokumentów, porównuje je między źródłami i pokazuje użytkownikowi wartości wymagające sprawdzenia. Nie przenosi automatycznie informacji tylko dlatego, że znalazł podobne słowo lub liczbę.

## Ustalenia z dostarczonych przykładów

- Pierwszy plik jest decyzją o pozwoleniu na budowę. Ma tekst akapitowy, bez tabel obiegówki. Zawiera inwestorów, adres, działkę, organ, numer i znak decyzji, datę jej wydania oraz parametry budynku. Osobno występuje data, od której decyzja stała się ostateczna. To nie jest data wydania decyzji.
- Drugi plik jest teczką zawierającą decyzję, protokoły, dokumenty urządzeń, fragmenty projektu i mapy. Ma około 1900 akapitów i wiele powtórzeń. Nie wolno traktować każdego wystąpienia słowa „decyzja”, „inwestor”, „kubatura” czy „pojemność” jako danych tego samego pola.
- W teczce występują parametry projektowane i informacje o późniejszych odbiorach. Są też pojemności zbiornika gazowego i urządzeń, których nie wolno wpisać do pola pojemności zbiornika na ścieki.
- Numer działki drogi dojazdowej może pojawić się obok działek inwestycji. Dla PB-5 trzeba dodatkowo potwierdzić, które nieruchomości mają być objęte oświadczeniem.
- Obecny parser obiegówki odrzuca oba pliki, bo szuka tabel z etykietami. Nowe źródła wymagają osobnych parserów.

## Zakres danych

| Dokument wynikowy | Kandydaci z plików | Zostaje do decyzji człowieka |
| --- | --- | --- |
| Pełnomocnictwo | Inwestorzy, ich adresy, nazwa i lokalizacja inwestycji, działki | Data pełnomocnictwa, korekta form gramatycznych i niepewnych imion lub nazwisk |
| PB-5 | Inwestorzy i ich adresy, adres nieruchomości, jednostki administracyjne, identyfikatory działek wyprowadzone tylko z kompletnych danych ewidencyjnych | Zakres nieruchomości i osoba składająca oświadczenie; nie wywodzić prawa do nieruchomości z samej decyzji |
| Oświadczenie kierownika | Inwestorzy, inwestycja, działki, znak lub numer oraz data pozwolenia | Oświadczenia o zgodności i stanie budowy, odstępstwa, EP i współczynniki U bez jednoznacznego źródła pomiarowego |
| Zawiadomienie | Dane powyżej, organ decyzji, jednoznacznie opisane parametry budynku, wybrane informacje z protokołów dotyczące wykonanych instalacji | Załączniki faktycznie dołączane, rodzaj odbioru, stan wykonania, pozostałe dane bez pewnego źródła |

Kategorie obiektu, nazwiska projektantów, numery urządzeń, dane producentów i treść pouczeń nie są częścią tego zadania, jeśli żaden z czterech generatorów ich nie używa.

## Przepływ użytkownika

1. Na pierwszym ekranie użytkownik dodaje 1–3 pliki. Przy każdym wybiera typ: **Obiegówka**, **Decyzja o pozwoleniu na budowę**, **Teczka dokumentacji budowy**. Dopuszczamy brak obiegówki; wtedy brakujące pola pozostają puste do ręcznego uzupełnienia. Typ jest obowiązkowy, a program sprawdza podstawową zgodność treści z wyborem.
2. Następny ekran zachowuje wybór czterech dokumentów wynikowych.
3. Formularz pokazuje wspólne dane, propozycje z informacją „z którego pliku i fragmentu” oraz osobną listę konfliktów. W razie sprzeczności użytkownik wybiera wartość albo wpisuje własną. Brak rozstrzygnięcia oznacza puste pole, a nie cichy wybór jednego pliku.
4. W sekcji parametrów odróżniamy **z projektu/decyzji** od **potwierdzone w protokole/po wykonaniu**. Sam opis planowanego rozwiązania nie zaznacza odpowiedzi o stanie wykonanym. Żadnych oświadczeń, wyborów tak/nie ani załączników program nie zaznacza sam.

## Architektura odczytu

1. **Warstwa plików:** walidacja formatu po zawartości, limit rozmiaru i liczby stron, odczyt w pamięci. DOCX: akapity, tabele, nagłówki i stopki. PDF z warstwą tekstową: tekst wraz z numerem strony. PDF skanowany: OCR stron bez tekstu; błędy OCR są oznaczane jako niższa pewność. Dobór i pakowanie silnika OCR na macOS trzeba potwierdzić próbą na rzeczywistym skanie, bo dostarczono wyłącznie DOCX.
2. **Parsery typów:** pozostawić parser obiegówki; dodać parser decyzji czytający przede wszystkim sentencję i tabelę/sekcję parametrów; dodać parser teczki, który najpierw wydziela poddokumenty (decyzja, projekt, protokół, certyfikat itp.), a potem czyta tylko sekcje istotne dla czterech wyników. Informacje z reklam, instrukcji urządzeń i mapowych numerów punktów pomijać.
3. **Kandydat z dowodem:** każde rozpoznane pole przechowuje wartość, rodzaj źródła, nazwę pliku, stronę lub sekcję, krótki fragment tekstu, stan „projektowane/wykonane”, poziom pewności i ewentualną uwagę. Dokumentów klientów i pełnego tekstu nie zapisywać na dysku.
4. **Scalanie:** normalizacja zapisu nazw, dat, liczb i jednostek oraz identyfikatorów działek przed porównaniem. Zgodne wartości z kilku miejsc wzmacniają propozycję. Różne inwestycje (osoby, miejscowość, działki lub znak pozwolenia) powodują wyraźny konflikt całego zestawu; program nie scala ich w jeden komplet. Przy rozbieżnościach pojedynczych pól pokazuje oba źródła. Nie stosuje ogólnej zasady „najnowszy dokument wygrywa”.
5. **Generowanie:** obecne szablony zachować. Formularz przekazuje zaakceptowane wartości w istniejącej strukturze. Rozszerzyć reprezentację wielu działek; przed automatycznym wypełnieniem PB-5 sprawdzić, czy obecny pojedynczy wiersz formularza wystarcza, a jeśli nie, przygotować kolejne strony/załącznik lub pozostawić ten fragment do ręcznej decyzji.

## Reguły, które muszą być sprawdzone w testach

- Data wydania decyzji, data jej ostateczności i daty protokołów są osobnymi polami; do pola „data pozwolenia” trafia wyłącznie data wydania.
- „Numer decyzji” i „znak sprawy” są osobnymi kandydatami; etykieta formularza i treść wzoru powinny jasno wskazywać, który wpis zostanie użyty.
- Pojemność zbiornika gazu nigdy nie zasila pola zbiornika na ścieki. Parametry urządzeń nie stają się parametrami budynku.
- Parametry budynku są przypisywane tylko do odpowiednich etykiet i jednostek; rozrzucone przez OCR liczby nie są kojarzone po samej kolejności wystąpienia.
- Nazwiska wielu inwestorów i ich kolejność są porównywane po normalizacji; odmiana gramatyczna w decyzji nie jest uznawana za pewny zapis do dokumentu bez kontroli.
- Działki inwestycji, drogi i sąsiednie nie są łączone automatycznie. Wielu działek nie wolno ucinać do pierwszej.
- Teczka z powtórzeniami i skan z błędami OCR nie powodują dziesiątek fałszywych ostrzeżeń.
- Dwa pliki z różnych inwestycji pokazują blokujący konflikt przed generacją; ścieżka jednego starego pliku obiegówki nadal działa.
- Testy używają zanonimizowanych przykładów. Otrzymanych dokumentów klientów nie dodawać do repozytorium.

## Kolejność wdrożenia

1. Spisać mapę pól formularza i źródeł, ustalić reguły dla wielu działek oraz numeru/znaku decyzji.
2. Zbudować odczyt DOCX/PDF i parser decyzji, z testami na zanonimizowanym odpowiedniku pierwszego pliku.
3. Dodać segmentację teczki, parser istotnych fragmentów i testy pomyłek widocznych w drugim pliku.
4. Dodać scalanie, pochodzenie wartości, konflikt całego zestawu i ekran przeglądu wielu plików.
5. Dodać OCR skanowanych PDF i próbę na rzeczywistym skanie; dostosować instalator macOS.
6. Sprawdzić cztery wygenerowane dokumenty, regresję starej obiegówki oraz zachowanie przy brakach i konfliktach.
