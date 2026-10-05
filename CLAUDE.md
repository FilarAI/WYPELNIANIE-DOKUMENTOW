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
- macOS. Program uruchamia się ikoną „Dokumenty FILAR” na pulpicie: `start.command` uruchamia serwer Flask
  na **127.0.0.1** (port od 5050) i otwiera przeglądarkę.
- **Python 3.9+**, bo systemowy python3 na Macu to często 3.9. Każdy moduł ma `from __future__ import annotations`.
  Nie używaj składni wymagającej 3.10+ (`match`, `X | Y` poza adnotacjami).
- Interfejs, komunikaty, nazwy plików wynikowych i dokumentacja są **po polsku**.

## Stack
- Flask (UI), `python-docx` (odczyt obiegówki, budowa szablonów), `docxtpl` (wypełnianie szablonów).
- Słowniki TERYT z GUS (eteryt.stat.gov.pl, pliki „urzędowe”), zapisane offline:
  `app/data/terc.csv` (województwa, powiaty, gminy) i `app/data/simc.csv` (miejscowości samodzielne, przycięte kolumny).

## Struktura
```
app/main.py              Flask: / (upload) → /podglad (formularz) → /generuj (zapis do folderu lub ZIP),
                         /wybierz-folder, /pokaz-folder, /zakoncz
app/parser_obiegowki.py  obiegówka → słownik danych + lista ostrzeżeń (opis pól w docstringu)
app/teryt.py             identyfikator działki / nazwa miejscowości → województwo, powiat, gmina
app/generator.py         wypełnianie szablonów (docxtpl), formy gramatyczne pełnomocnictwa
app/konfiguracja.py      dane pełnomocnika biura (osoba upoważniona w PB-5)
app/zapis.py             zapis do wybranego folderu (okno macOS przez osascript), pamięć ostatniego folderu
app/templates/           HTML: baza.html (obramowanie, nagłówek, pasek kroków), _makra.html (ikony SVG, pola, odmiana)
app/static/styl.css      wygląd; kolory, odstępy, cienie jako zmienne CSS na początku pliku
docs/projekt-ui/         specyfikacja interfejsu (źródło prawdy dla wyglądu) i makiety
narzedzia/zbuduj_szablony.py  buduje szablony/*.docx od zera (źródło prawdy dla szablonów)
narzedzia/zbuduj_ikone.py     ikona/zrodlo.webp → ikona/ikona.icns (ikona na pulpicie) i app/static/ikona-*.png (logo, favicon)
narzedzia/zbuduj_obiegowke_testowa.py  obiegówki testowe z fikcyjnymi danymi (tests/fixtures/obiegowka_testowa_*.docx)
szablony/                gotowe szablony ze znacznikami {{ }}
tests/                   pytest; fixtures: zanonimizowana obiegówka + oczekiwany wynik (JSON),
                         obiegówki testowe: pełna (1 inwestor, lokal, adres działki z kodem) i z dwojgiem inwestorów
start.command            uruchomienie (macOS); przy braku .venv sam instaluje
instaluj_mac.sh          jednorazowa instalacja: .venv, zależności, ikona na pulpicie (osacompile)
```

## Komendy
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # instalacja
.venv/bin/python -m pytest                                           # testy
.venv/bin/python -m app.main --bez-przegladarki                      # serwer bez otwierania przeglądarki
.venv/bin/python narzedzia/zbuduj_szablony.py                        # przebudowa szablonów
```

## Obiegówka: jak wygląda
- Składa się z kilku stron (strona tytułowa PZT, strona tytułowa PB, oświadczenia projektanta).
  Każda strona ma **tabelę** z etykietami w 1. kolumnie: `NAZWA INWESTYCJI`, `ADRES INWESTYCJI`,
  `INWESTOR:`, `KATEGORIA OBIEKTU:`, `DATA OPRACOWANIA`, `PROJEKTANT GŁÓWNY:`, zespół projektowy.
- python-docx powtarza komórki scalone, dlatego parser deduplikuje je po elemencie `_tc`.
- Komórka inwestora: akapity „imię i nazwisko”, „ul. …”, „kod miejscowość”. Kilka osób: „Jan i Anna …”
  albo kolejne bloki z osobnymi adresami.
- Identyfikator działki ma format TERYT `WWPPGG_R.OOOO.NR`, np. `120903_4.0002.1358`
  (woj. 12 małopolskie, powiat 1209 myślenicki, gmina 120903 Myślenice, obręb 0002, działka 1358).
- Etykiety mają w oryginałach literówki (np. `NAZWA NWESTYCJI`), więc parser dopasowuje je przez `difflib` (próg 0.85).
- Główne źródło danych to strona „PROJEKT BUDOWLANY”. Adres inwestycji jest składany z najpełniejszych
  wersji ze wszystkich stron (ulica bywa tylko w oświadczeniach).
- Wzorcowy wynik parsera: `tests/fixtures/obiegowka_PB_oczekiwane.json`.

## Zasady
- **Prywatność:** serwer nasłuchuje tylko na `127.0.0.1`. W trakcie działania brak połączeń z internetem.
  Wgrane pliki są przetwarzane w pamięci (`io.BytesIO`) i nie są zapisywane na dysku.
- **Nie commitować dokumentów klientów.** `.gitignore` blokuje `*.docx`/`*.pdf` poza `szablony/`
  i `tests/fixtures/`. W fixture'ach są tylko dane zanonimizowane (inwestor: Jan Kowalski, ul. Przykładowa 1).
- **Spójność danych:** parser porównuje te same pola ze wszystkich stron obiegówki i **zawsze zwraca
  ostrzeżenia** o różnicach. Nigdy nie wybiera po cichu jednej wersji. Ostrzeżenia są pokazywane w formularzu.
- **Szablony** zmienia się w `narzedzia/zbuduj_szablony.py`, a potem buduje od nowa (nie ręcznie w Wordzie).
  Znacznik `{{ pole }}` musi być w jednym runie, a `"\n"` w wartości daje złamanie linii.
  Puste pola generator zastępuje kropkami (`PUSTE_POLE`), żeby można je było uzupełnić długopisem.
- Pełnomocnictwo: formy gramatyczne zależą od liczby i płci inwestorów
  („Ja/My”, „zamieszkała / zamieszkały / zamieszkali”, „udzielam / udzielamy”, „mnie / nas”, „Upoważniam / Upoważniamy”).
  Płeć jest zgadywana po imieniu i poprawialna w formularzu. Pełnomocnik (Bartłomiej Filar) jest wpisany na stałe w szablonie.
- PB-5: kraj „Polska”. Województwo, powiat i gmina działki pochodzą z identyfikatora TERYT, a dla inwestora
  z nazwy miejscowości (SIMC; przy niejednoznacznej nazwie wybierana jest ta bliżej działki). Dane osoby upoważnionej
  wpisywane są tylko po zaznaczeniu opcji w formularzu.
- **Miejscowość działki z TERYT:** gdy obiegówka podaje tylko działkę (bez miejscowości), parser bierze ją z identyfikatora
  (`teryt.miasto_z_identyfikatora()`): rodzaj 1/4 → nazwa miasta, 8/9 → nazwa powiatu (Warszawa, Kraków), wieś (2/5) → puste.
  Miejscowość z obiegówki zawsze ma pierwszeństwo.
- **„↑ Przepisz ten adres do działki”** (przycisk w bloku inwestora, JS w `podglad.html`): kopiuje ulicę, nr domu, kod
  i miejscowość inwestora do pól działki; województwo/powiat/gminę działki tylko gdy są puste (TERYT jest pewniejszy).
- **Nr lokalu w PB-5:** „–” (`BRAK_LOKALU`), gdy adres jest podany bez lokalu; kropki tylko gdy brak całego adresu.
- Port serwera: od 5050 w górę z pominięciem portów blokowanych przez przeglądarki (5060, 5061 – `PORTY_ZABLOKOWANE`).
- **Zapis:** domyślnie dokumenty (.docx, bez ZIP) trafiają do folderu wybranego w formularzu. Przycisk „Wybierz…”
  otwiera systemowe okno macOS (`osascript … choose folder`). Ostatni folder jest zapamiętywany w `~/.dokumenty_filar.json`
  (w testach zmienna `DOKUMENTY_FILAR_USTAWIENIA`). Istniejące pliki nie są nadpisywane (dopisywane jest „ (2)”).
  Pobranie ZIP zostaje jako druga opcja.
- **Wygląd:** zgodnie z `docs/projekt-ui/specyfikacja.md`. Wartości zmienia się w zmiennych CSS, nie w regułach.
  Font systemowy i ikony SVG w kodzie, bez CDN i Google Fonts (brak internetu). Animacje subtelne,
  wyłączane przez „Ogranicz ruch” (`prefers-reduced-motion`).
- **Ikona programu** (`ikona/zrodlo.webp`, przezroczyste tło): favicon, logo w nagłówku, ekran wyłączenia
  (wpisana w stronę jako data URI, bo serwer już się wyłącza) i ikona aplikacji na pulpicie (`instaluj_mac.sh` podmienia
  `applet.icns`). Tylko w programie, nie w dokumentach. Po podmianie grafiki uruchom `narzedzia/zbuduj_ikone.py` (wymaga Pillow).
  Tryb ciemny: blok `:root[data-motyw="ciemny"]` w `styl.css`, przełącznik w nagłówku (system / jasny / ciemny,
  pamiętany w `localStorage`). Każdy kolor przez zmienną z wartością w obu motywach.
- **Grafika:** baner z logo jest tylko w pełnomocnictwie (PB-5 to urzędowy formularz, bez grafiki).
  Plik `szablony/grafika/naglowek_filar.png`: PNG na całą szerokość kartki (obecnie 2000 × 360 px = 21 × 3,8 cm,
  przycięty z grafiki 2000 × 667 z Canvy), treść min. ~60 px od krawędzi, bez daty (data jest tekstem pod banerem).
  Górny margines strony liczy się z proporcji obrazu (`wysokosc_banera_cm()` + 0,6 cm). Baner idzie na całą szerokość kartki dzięki
  ujemnym wcięciom akapitu nagłówka (`naglowek_z_grafika()`). Gdy pliku brak, szablon powstaje bez banera.
  Po podmianie grafiki uruchom `narzedzia/zbuduj_szablony.py`. Stopka biura jest tekstem (szara, z linią nad).

## Wersje
- `app/__init__.py` → `WERSJA`: zmieniaj przy każdej paczce `Dokumenty-FILAR.zip` dla biura. Wersja i folder programu
  są w stopce każdej strony i w Terminalu, więc od razu widać, czy ikona uruchamia aktualny folder
  (po rozpakowaniu obok starego macOS tworzy „Dokumenty-FILAR 2”, a ikona dalej wskazuje stary folder).
- Arkusz stylów jest wczytywany z `?v=<czas zmiany pliku>` (`wersja_stylu` w `app/main.py`),
  więc przeglądarka nie pokazuje starego wyglądu z pamięci podręcznej.

## Jak dodać nowy dokument (szablon)
1. Dodaj funkcję budującą szablon w `narzedzia/zbuduj_szablony.py` (znaczniki `{{ }}` z nazwami pól parsera).
2. Dodaj w `app/generator.py` funkcję kontekstu i wpis w `generuj_dokumenty()` (jeden plik czy osobny dla każdego inwestora).
3. Dodaj test w `tests/test_generator.py`, który sprawdza treść oraz brak `{{` w wyniku.
