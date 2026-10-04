# CLAUDE.md

## Cel projektu
Lokalny program biura **FILAR-USŁUGI** (Rabka-Zdrój) do automatycznego wypełniania dokumentów.
Użytkownik wgrywa **obiegówkę** projektu (.docx). Program odczytuje z niej dane (inwestor, nazwa
i adres inwestycji, działka) i pokazuje je w formularzu do poprawy. Następnie generuje dokumenty z szablonów biura:
1. **Pełnomocnictwo** (`szablony/pelnomocnictwo.docx`): jedno, wspólne dla wszystkich inwestorów,
2. **PB-5**, czyli oświadczenie o posiadanym prawie do dysponowania nieruchomością na cele budowlane
   (`szablony/pb5_oswiadczenie.docx`): **osobny plik dla każdego inwestora**.

Zakres na start: tylko obiegówka i te dwa szablony. Kolejne dokumenty mogą dojść później.

## Środowisko docelowe
- macOS. Program uruchamia się ikoną na pulpicie: serwer Flask na **127.0.0.1** otwiera przeglądarkę.
- Interfejs, komunikaty, nazwy plików wynikowych i dokumentacja są **po polsku**.

## Stack
- Python 3.11+, Flask (UI), `python-docx` (odczyt obiegówki), `docxtpl` (wypełnianie szablonów).
- Słownik TERYT (TERC z GUS) zapisany offline w `app/data/terc.csv`.

## Struktura (docelowa, w budowie)
```
app/main.py              Flask: / (upload) → /podglad (formularz) → /generuj (ZIP z .docx)
app/parser_obiegowki.py  obiegówka → słownik danych + lista ostrzeżeń
app/teryt.py             identyfikator działki → województwo / powiat / gmina
app/generator.py         wypełnianie szablonów docxtpl
szablony/                szablony biura ze znacznikami {{ }}
tests/fixtures/          zanonimizowane pliki testowe + oczekiwane wyniki (JSON)
start.command            uruchomienie serwera + przeglądarki (macOS)
instaluj_mac.sh          jednorazowa instalacja: .venv, zależności, ikona na pulpicie
```

## Komendy
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # instalacja
.venv/bin/python -m pytest                                           # testy
./start.command                                                      # uruchomienie (macOS)
```

## Obiegówka: jak wygląda
- Składa się z kilku stron (strona tytułowa PZT, strona tytułowa PB, oświadczenia projektanta).
  Każda strona ma **tabelę** z etykietami w 1. kolumnie: `NAZWA INWESTYCJI`, `ADRES INWESTYCJI`,
  `INWESTOR:`, `KATEGORIA OBIEKTU:`, `DATA OPRACOWANIA`, `PROJEKTANT GŁÓWNY:`, zespół projektowy.
- W komórce tekst jest podzielony na akapity: inwestor to imię i nazwisko, ulica, kod i miejscowość.
- Identyfikator działki ma format TERYT `WWPPGG_R.OOOO.NR`, np. `120903_4.0002.1358`
  (woj. 12 małopolskie, powiat 1209 myślenicki, gmina 120903 Myślenice, obręb 0002, działka 1358).
- Etykiety mają w oryginałach literówki (np. `NAZWA NWESTYCJI`). Parser dopasowuje je tolerancyjnie.
- Wzorcowy wynik parsera: `tests/fixtures/obiegowka_PB_oczekiwane.json`.

## Zasady
- **Prywatność:** serwer nasłuchuje tylko na `127.0.0.1`. W trakcie działania brak połączeń z internetem.
  Wgrane pliki są przetwarzane w pamięci i nie są zapisywane na dysku.
- **Nie commitować dokumentów klientów.** `.gitignore` blokuje `*.docx`/`*.pdf` poza `szablony/`
  i `tests/fixtures/`. W fixture'ach są tylko dane zanonimizowane (inwestor: Jan Kowalski, ul. Przykładowa 1).
- **Spójność danych:** parser porównuje te same pola ze wszystkich stron obiegówki i **zawsze zwraca
  ostrzeżenia** o różnicach. Nigdy nie wybiera po cichu jednej wersji. Ostrzeżenia są pokazywane w formularzu.
- **Szablony** edytuje się w Wordzie. Znaczniki `{{ pole }}` muszą być w jednym „runie”: wpisz znacznik
  od nowa jednym ciągiem, bez zmiany formatowania w środku. Po każdej zmianie szablonu uruchom testy.
- Pełnomocnictwo: formy gramatyczne zależą od liczby i płci inwestorów
  („zamieszkała / zamieszkały / zamieszkali”, „udzielam / udzielamy”). Płeć jest zgadywana po imieniu
  i poprawialna w formularzu. Pełnomocnik (Bartłomiej Filar) i miejsce wystawienia (Rabka-Zdrój) to stałe w konfiguracji.
- PB-5: kraj „Polska”. Województwo, powiat i gmina pochodzą z identyfikatora działki (TERYT).

## Jak dodać nowy dokument (szablon)
1. Skopiuj wzór biura do `szablony/` i zamień pola do wypełnienia na znaczniki `{{ }}` z nazwami pól parsera.
2. Dodaj wpis w `app/generator.py` (nazwa pliku wynikowego oraz czy dokument jest jeden, czy osobny dla każdego inwestora).
3. Dodaj test w `tests/test_generator.py`, który sprawdza, że w wyniku nie zostały `{{` ani puste kropki.
