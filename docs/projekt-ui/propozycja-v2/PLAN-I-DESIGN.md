# Dokumenty FILAR — propozycja interfejsu v2

Status: do akceptacji. To propozycja, nie wdrożony system. Działająca aplikacja pozostaje w obecnej wersji. Analiza: kod aktualnych szablonów i CSS, wcześniejsze zrzuty aplikacji i specyfikacja. Makieta HTML jest ilustracją kompozycji, nie testem funkcji produkcyjnych.

## Skille i sposób pracy

- Impeccable: już zainstalowany w `~/.codex/skills/impeccable`. Użyty do określenia celu, hierarchii, przepływu i zakresu. Lokalny launcher wcześniej odmówił uruchomienia; zastosowano instrukcję fallback i analizę istniejącego kodu/specyfikacji. Nie aktualizowano istniejącej wersji automatycznie.
- Web Design Guidelines (Vercel): zainstalowany z podanego repozytorium; użyty do analizy formularzy, focusu, informacji zwrotnej, obsługi klawiatury i motywów. „Awesome skill” interpretujemy jako ten podlinkowany skill.
- Unslop: zainstalowany; użyty do oceny odstępów, koloru, tekstów, typografii i animacji oraz określenia kierunku. Po wdrożeniu służy do końcowego dopracowania przyjętego systemu.
- Security Audit (Cloudflare): zainstalowany, audyt odłożony na osobny etap na życzenie użytkownika.

Nowe skille będą automatycznie dostępne od następnej wiadomości. Ich instrukcje odczytano już w tym etapie.

Kolejność: Impeccable → Web Design Guidelines → Unslop. Jedna zaakceptowana specyfikacja rozstrzyga różnice między skillami. Nie uruchamiamy trzech kolejnych, niezależnych redesignów. Zachowujemy polską pisownię etykiet i dostarczone logo, nawet jeśli ogólne rady skilla sugerują inne rozwiązania.

## Kierunek w pięciu zdaniach (Unslop)

1. Produkt: lokalne narzędzie biura projektowego do przygotowywania dokumentów urzędowych z plików źródłowych.
2. Charakter: rzeczowy, spokojny, precyzyjny.
3. Świat: uporządkowana teczka sprawy — dokumenty, dane inwestycji i kontrola zgodności.
4. Akcenty: dostarczone niebieskie logo oraz główna akcja i zaznaczenie bieżącego zadania.
5. Wyróżnik: wspólny wzorzec „dana → źródło → potwierdzenie”, widoczny przy polach wymagających decyzji.

## Analiza obecnej aplikacji

Nie jest potrzebne usuwanie całej warstwy wizualnej. Już istnieją: dwa motywy, niebieski akcent, semantyczne statusy, wspólne makra, prawdziwe etykiety i obsługa ograniczenia animacji. Wiele ekranów ma spójną podstawę. Potrzebna jest przede wszystkim lepsza organizacja pracy i konsekwencja komponentów.

Najważniejsze problemy:

1. Ekran 3 zaczyna od ustawień formatowania dokumentu (`podglad.html:64`), zanim użytkownik rozwiąże błędy i rozbieżności. Przenosimy je do ustawień eksportu przy końcu pracy.
2. Lista dokumentów łączy kod, długi tytuł i informacje o osobnych plikach w jednej etykiecie (`wybor_dokumentow.html:15`). Rozdzielamy tytuł i opis; pełne nazwy urzędowe zachowujemy.
3. Brak wyszukiwarki, filtrów i widocznego licznika wybranych dokumentów. Przy 15 typach lista wymaga niepotrzebnego czytania.
4. Podsumowanie pustych pól (`podglad.html:375`) szuka tylko jawnego `type="text"`; pomija część pól bez atrybutu. Liczy też pola opcjonalne i niewybrane opcje jako braki. Nie można na tej podstawie pokazywać wiarygodnego statusu „gotowe”.
5. Puste pole „Pełnomocnik: brak” i pusta wartość wymagana nie znaczą tego samego. Walidacja musi znać znaczenie pola i zależności w formularzu.
6. Dokumenty mają własne sekcje i makra, co sprzyja rozjeżdżaniu się odstępów i opisów. Potrzebny wspólny kontrakt pola i sekcji dokumentu.
7. `styl.css:415–417`: podtytuły są pisane wersalikami, szeroko rozstrzelone i bardzo jasne. Proponujemy zwykłą pisownię i czytelniejszy kolor.
8. `styl.css:603–609`: animowane jest każde bezpośrednie dziecko formularza. Przy długich formularzach daje to ruch bez informacji o działaniu. Animacje zostawiamy przy zmianach stanu i krótkim wejściu ekranu.
9. Specyfikacja `docs/projekt-ui/specyfikacja.md` zawiera nieaktualne decyzje: dwa dokumenty bez wyboru i automatyczny odczyt po dodaniu pliku. Kod obsługuje już wybór 15 typów i 1–3 źródła. Po akceptacji v2 ujednolicamy dokumentację.

### Przegląd Web Design Guidelines

- `app/templates/start.html:42` — stan submit dodaje klasę, ale nie zmienia komunikatu dostępnego dla czytnika i nie blokuje powtórnego żądania. Dodać rzeczywisty stan zajętości i `role="status"`.
- `app/templates/wybor_dokumentow.html:9` — błąd wyboru korzysta z `alert()`. Zastąpić komunikatem przy liście z przeniesieniem focusu.
- `app/templates/podglad.html:355–363` — przejście do pola używa bezwarunkowego smooth scroll. Uwzględnić preferencję ograniczonego ruchu.
- `app/templates/podglad.html:375` — kontrola kompletności pomija niektóre typy kontrolek; ujednolicić selektor i logikę wymagalności.
- `app/static/styl.css:624` — obsługa `prefers-reduced-motion` już istnieje; zachować i objąć nowe animacje.

Powyższe to przegląd kodu, nie pełny audyt dostępności całej aplikacji. Kontrast proponowanych kolorów i rzeczywiste interakcje sprawdzimy podczas wdrożenia.

## Proponowany układ

### Stała rama aplikacji

Nagłówek 64 px z logo 36 px, nazwą i przełącznikiem System / Jasny / Ciemny. Poniżej pasek trzech etapów: Pliki → Dokumenty → Dane i generowanie. „Gotowe” jest wynikiem procesu, nie kolejnym zadaniem do wykonania. Treść ma jasny tytuł wyrównany do lewej. Przy szerokim oknie pokazujemy boczny panel kontekstu; poniżej 1100 px panel trafia nad treść lub do rozwijanego podsumowania.

Nie dodajemy stałego panelu menu z pustymi pozycjami ani wykresów. Rama ma służyć bieżącej sprawie. W przyszłości historia spraw może otrzymać własny ekran, jeśli pojawi się taka potrzeba.

### Ekran 1 — Pliki źródłowe

- Duże pole przeciągania i przycisk „Wybierz pliki”; oba obsługiwane klawiaturą.
- Lista dodanych plików: nazwa, rozmiar, wybierany rodzaj, „Usuń”. Zachowujemy limit 1–3 źródeł i wspierane formaty.
- Przed odczytem: „Dodano”; po kliknięciu „Odczytaj pliki”: wspólny stan „Odczytuję dane…”. Status per plik dopiero gdy backend faktycznie go raportuje.
- Nie pokazujemy fikcyjnych procentów ani zmyślonych etapów. Jeśli dodamy postęp przesyłania, wynika z rzeczywistych zdarzeń uploadu; parsowanie ma osobny stan nieokreślony.
- Błąd wskazuje plik i sposób naprawy. Poprawne pliki pozostają wybrane, jeśli pozwoli na to obsługa błędów po stronie serwera.
- Automatyczne rozpoznawanie typu jest osobnym rozszerzeniem parsera; nie udajemy go samą animacją.

### Ekran 2 — Dokumenty do przygotowania

- Wyszukiwarka „Szukaj po nazwie lub kodzie”. Filtry: Wszystkie, Budowlane, Geodezyjne, Pełnomocnictwa.
- Lista alfabetyczna w obrębie aktywnego filtra. Kod i krótki tytuł na górze; pełna nazwa i informacja „osobno dla każdego inwestora” poniżej.
- Zaznaczalny cały wiersz; widoczny checkbox; licznik „Wybrano 3 dokumenty”.
- Panel po prawej: wybrane pozycje i źródła. Przycisk „Sprawdź dane” pokazuje, do jakiej czynności prowadzi.
- Zestawy „Pozwolenie” i „Zakończenie” dopiero po uzgodnieniu dokładnej zawartości. Nie oznaczamy ich jako prawnie kompletnych pakietów.

### Ekran 3 — Dane i generowanie

- Na górze konkretne zadania: wymagane braki, rozbieżności, dane do potwierdzenia. Każde z „Przejdź do pola”. Opcjonalne pola mają etykietę „opcjonalnie”, nie zwiększają licznika błędów.
- Dalej dane wspólne: inwestycja, działka, inwestorzy. Wprowadzane raz i używane przez wybrane dokumenty.
- Następnie ustawienia wybranych dokumentów w rozwijanych sekcjach. Brak obowiązkowy automatycznie otwiera odpowiednią sekcję.
- Kliknięcie zadania rozwija wszystkich zwiniętych przodków, przewija pole i nadaje focus. Wyjaśnia, co wymaga poprawy.
- Boczne podsumowanie nawigacyjne: Dane wspólne, wybrane dokumenty, Eksport. Pokazuje statusy oparte na istniejącej walidacji, nie na samym wypełnieniu wszystkich inputów.
- Przy dole widoczny pasek: liczba dokumentów, wymagane zadania i „Generuj dokumenty”. Nie zasłania pól, komunikatów ani klawiatury ekranowej.
- Format tekstu, folder i sposób pobrania w sekcji „Zapis i wygląd dokumentów”.
- Po wygenerowaniu: prawdziwa lista plików i wynik zapisu, możliwość pobrania i powrotu do korekty bez ponownego wgrywania (wymaga zachowania stanu po stronie aplikacji).

## Proponowany system designu

Jedna rodzina: systemowa `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`. Na Macu wykorzystuje rodzinę systemową; nie wymaga internetu. Jeśli w przyszłości wymagana będzie identyczna rodzina na wszystkich systemach, dołączymy lokalnie font z polskimi znakami. Na każdym ekranie te same role, rozmiary i grubości.

| Rola | Rozmiar / interlinia | Waga |
|---|---|---|
| H1 | 28 / 36 px | 600 |
| H2 | 20 / 28 px | 600 |
| Tytuł dokumentu / sekcji | 16 / 24 px | 500 |
| Pola, przyciski, tekst | 14 / 22 px | 400 lub 500 |
| Etykiety | 14 / 20 px | 500 |
| Metadane i podpowiedzi | 13 / 20 px | 400 |

Etykiety zwykłą pisownią, bez rozstrzelonych wersalików. Pełna nazwa pliku dostępna po rozwinięciu; istotnych ostrzeżeń nie ucinamy. Długie identyfikatory mogą się łamać bez poszerzania ekranu.

| Token | Jasny | Ciemny |
|---|---|---|
| Tło | `#F5F6F8` | `#101216` |
| Powierzchnia | `#FFFFFF` | `#191D24` |
| Powierzchnia pomocnicza | `#F0F2F5` | `#222833` |
| Tekst główny | `#182230` | `#F0F3F8` |
| Tekst pomocniczy | `#526071` | `#AAB6C8` |
| Ramka neutralna | `#D8DEE8` | `#394353` |
| Główny przycisk | `#245BDB` + biały tekst | `#245BDB` + biały tekst |
| Link / aktywny tekst | `#245BDB` | `#8AB4FF` |
| Zaznaczone tło | `#EDF3FF` | `#202E49` |
| Focus | `#245BDB` | `#8AB4FF` |
| Uwaga: tekst / tło | `#705013` / `#FFF8E7` | `#F0CD81` / `#30291C` |
| Błąd: tekst / tło | `#B42318` / `#FFF0EE` | `#FFACA6` / `#342023` |
| Sukces: tekst / tło | `#176144` / `#EAF6EF` | `#9DD8BA` / `#1B2D25` |

Niebieski jest głównym kolorem akcji, focusu, wyboru i aktywnego etapu. Powierzchnie pozostają neutralne. Kolory ostrzeżeń zawsze mają ikonę i opis. Ramka aktywnego pola/checkboxa ma wyraźniejszy kontrast niż separator.

- Skala odstępów: 4, 8, 12, 16, 24, 32, 48 px. Pole → opis 8 px; między polami 16–24 px; między sekcjami 32 px.
- Przyciski i pola: 44 px wysokości; textarea minimum 88 px; promień 8 px.
- Sekcje: 12 px promienia i 24 px paddingu. Grupowanie przede wszystkim odstępem i separatorem; unikamy kolejnych kart wewnątrz kart.
- Szerokość ramy do 1440 px; treść robocza około 880–960 px i panel kontekstu 280 px. Na małych ekranach jedna kolumna z 16 px marginesu.
- Focus: wyraźny obrys 2 px z odsunięciem 2 px. Natywne kontrolki, obsługa Tab / Shift+Tab / Enter / Spacja.
- Logo dostarczone przez użytkownika: 36 px, bez dodatkowego glow, zmiany kolorów i animacji dekoracyjnej.
- Ciemny motyw wykorzystuje różnice powierzchni i ramki; jasny może mieć niewielki neutralny cień dla elementów pływających.

## Ruch i stany

| Zdarzenie | Propozycja | Czas |
|---|---|---|
| Przeciągnięcie pliku nad pole | zmiana ramki i tła, bez powiększania całego formularza | 120 ms |
| Dodanie pliku | opacity + przesunięcie 4 px | 160 ms |
| Odczyt plików | spinner tylko w stanie zajętości, tekst „Odczytuję dane…” | do odpowiedzi serwera |
| Rzeczywisty postęp uploadu | pasek przez `transform: scaleX`, procent tylko z pomiaru | aktualizacja na zdarzeniach |
| Rozwinięcie sekcji | natychmiastowa zmiana układu, krótki fade treści | 120 ms |
| Wybór dokumentu | zmiana zaznaczenia, bez skoku i pulsowania | 100 ms |
| Generowanie | zajęty przycisk, tekst „Generuję dokumenty…”, ochrona przed podwójnym wysłaniem | do wyniku |
| Sukces | jednorazowe pojawienie ikony i listy wyników | 180 ms |

Jedna krzywa `cubic-bezier(.2,.8,.2,1)`. `prefers-reduced-motion`: brak przesunięć, obrotów i smooth scroll; statyczny tekst statusu nadal pokazuje pracę. Żadnych animacji wszystkich sekcji po kolei ani ruchu w pętli poza prawdziwym oczekiwaniem.

## Etapy wdrożenia po akceptacji

1. Uporządkować źródło prawdy: PRODUCT.md, DESIGN.md i brief trzech ekranów według zatwierdzonej propozycji. Zweryfikować stan repozytorium z obecnymi zmianami i zapisać punkt odniesienia.
2. Zbudować tokeny light/dark oraz wspólne makra: pole, opis, błąd, dokument na liście, status pliku, nagłówek sekcji i pasek akcji. Zachować Flask/Jinja i dotychczasowe generatory DOCX.
3. Wdrożyć ekran 1 z realnym feedbackiem odczytu, potem ekran 2 z wyszukiwaniem i zaznaczeniami. Nowe mechanizmy postępu lub rozpoznawania typu tylko z rzeczywistą obsługą backendu.
4. Wdrożyć ekran 3: stan pól wymaganych i opcjonalnych zgodny z walidacją każdego dokumentu, wspólne dane, sekcje dokumentów, przejścia do pól, eksport. Zachować wartości po błędzie i przy wracaniu między etapami.
5. Zastosować Web Design Guidelines: klawiatura, focus, czytnik, komunikaty live, reduced motion, długie treści, motyw bez migania i brak poziomego scrolla.
6. Unslop na gotowym przepływie: odstępy → kolor → ikony → tekst → typografia → układ → detale → wizualia → ruch. Dopracować zaakceptowany kierunek, nie zmieniać go samodzielnie.
7. Sprawdzić kompletne przejście dla typowej sprawy, kilku inwestorów, rozbieżności, braków, 1–3 plików i 15 typów dokumentów. Jasny i ciemny przy 1440, 1024 i 390 px; jeden zbiorczy przegląd i jedna runda poprawek. Sprawdzić także wynik eksportu po zmianie UI.
8. Dostarczyć lokalną wersję do akceptacji. Security Audit przeprowadzić jako późniejszą, osobną pracę przed szerszą dystrybucją.

## Kryteria akceptacji

- Użytkownik widzi bieżący etap i następną czynność bez szukania przycisku.
- Można znaleźć dokument po kodzie i nazwie; licznik odpowiada zaznaczonym pozycjom.
- Puste opcjonalne pole nie jest błędem; „brak pełnomocnika” jest prawidłową odpowiedzią.
- Każde wymagane zadanie prowadzi do widocznego pola; dane nie giną po walidacji.
- Odczyt i generowanie mają prawdziwe statusy, bez fikcyjnych procentów.
- W obu motywach używane są te same proporcje i role tekstu; focus i semantyczne statusy są czytelne.
- Poprawne dokumenty nadal powstają i zawierają te same dane merytoryczne.

## Materiały i autorstwo

Impeccable: https://github.com/pbakaus/impeccable
Web Design Guidelines: https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines
Aktualne wytyczne: https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
Unslop: Damir Sokolovsky (@heydamir), https://github.com/heydamir/unslop, CC BY 4.0. Kierunek i kolejność przeglądu opracowano z wykorzystaniem tych instrukcji.
Security Audit: https://github.com/cloudflare/security-audit-skill — zainstalowany, nieuruchomiony.
