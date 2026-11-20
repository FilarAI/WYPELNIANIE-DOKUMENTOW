# Prompty do wizualizacji i późniejszego wdrożenia

Status: propozycja do akceptacji. Poniższy prompt nie uruchamia wdrożenia. Kolory i szczegóły: PLAN-I-DESIGN.md.

## Wspólny prompt projektowy

Zaprojektuj trzy ekrany aplikacji desktopowej „Dokumenty FILAR”, lokalnego narzędzia polskiego biura projektowego przygotowującego dokumenty urzędowe z Word/PDF. Użytkownik pracuje z długimi nazwami inwestycji, numerami działek i kilkoma inwestorami. Celem jest szybko odnaleźć potrzebny dokument, sprawdzić dane i wygenerować poprawny wynik.

Użyj Impeccable do hierarchii i przepływu, Web Design Guidelines do dostępności i interakcji, a Unslop do końcowego uporządkowania. Przestrzegaj zatwierdzonego systemu designu; nie proponuj kolejnego stylu przy każdym przebiegu.

Wspólna rama: logo dostarczone przez użytkownika 36 px, nazwa aplikacji, przełącznik System/Jasny/Ciemny, pasek etapów Pliki → Dokumenty → Dane i generowanie. Wyrównanie treści do lewej. Szerokość do 1440 px, obszar roboczy 880–960 px i panel kontekstu 280 px; przy małych ekranach jedna kolumna. Jedna rodzina systemowa, H1 28/36 waga 600, H2 20/28 waga 600, tytuły 16/24 waga 500, treść i kontrolki 14/22, metadane 13/20. Odstępy 4/8/12/16/24/32/48 px. Pola i przyciski 44 px, promień 8 px. Sekcje 12 px promienia. Jeden zestaw liniowych ikon. Polskie etykiety zwykłą pisownią. Neutralne powierzchnie, niebieski jako główny kolor akcji i wyboru.

Ekran 1: tytuł „Wgraj pliki źródłowe”, duże pole przeciągania, dostępny przycisk wyboru; lista 1–3 plików z nazwą, rozmiarem, wyborem typu i usunięciem. Pokaż osobno stan dodania, rzeczywistego odczytu i błędu. Odczyt ma tekst „Odczytuję dane…” i spinner; procent tylko gdy system rzeczywiście go mierzy.

Ekran 2: tytuł „Wybierz dokumenty”, wyszukiwarka po nazwie lub kodzie, filtry dziedzin, lista alfabetyczna z checkboxami. Przykłady: „BA-4 — dziennik budowy”, „PB-1 — pozwolenie na budowę”, „Pełnomocnictwo”. Pełna nazwa i informacja o osobnym pliku dla inwestora w drugiej linii. Z boku lista wybranych i licznik, na dole „Sprawdź dane”.

Ekran 3: tytuł „Sprawdź dane i wygeneruj dokumenty”. Najpierw zadania „Adres inwestycji — wartości różnią się między plikami” i „PB-1 — uzupełnij termin”, z akcją „Przejdź do pola”. Następnie dane wspólne i rozwijane sekcje wybranych dokumentów. Etykieta, input i opis tworzą jeden komponent. Przy rozbieżności pokaż źródło i możliwe wartości. Boczne podsumowanie nawigacyjne oraz dolny pasek „3 dokumenty · 2 zadania do sprawdzenia” i „Generuj dokumenty”. Pola opcjonalne nie są liczone jako błąd. Formatowanie i folder w sekcji eksportu.

Animacje wyłącznie funkcjonalne: dodanie pliku 160 ms opacity/translateY(4 px); hover 120 ms; oczekiwanie na odczyt/generowanie; sukces 180 ms. Jedna krzywa ease-out, pełna obsługa reduced motion. Bez animowanych teł, pulsujących kart i kaskadowego pojawiania całego formularza. Zachowaj dostarczone logo jako wyjątek od ogólnych zaleceń redukcji dekoracji.

Przykładowe dane są fikcyjne: „Rozbudowa budynku mieszkalnego w Rabce-Zdroju”, inwestor „Anna Nowak”, działka „245/7”, plik „obiegowka_projekt.docx”. Bez zmyślonych statystyk i deklaracji prawnych. Makieta ma służyć ocenie układu; statusy produkcyjne muszą później wynikać z rzeczywistych danych.

Zwróć trzy oddzielne ekrany z rzeczywistymi polskimi tekstami i widoczną hierarchią. Nie zmieniaj kodu aplikacji, dopóki projekt nie zostanie zaakceptowany.

## Wariant jasny — dopisz do wspólnego promptu

Tryb jasny: tło #F5F6F8, powierzchnie #FFFFFF, powierzchnie pomocnicze #F0F2F5, tekst #182230, pomocniczy #526071, ramki #D8DEE8. Główna akcja #245BDB z białym tekstem, zaznaczenie #EDF3FF, linki #245BDB. Ostrzeżenie #FFF8E7 z tekstem #705013. Lekki neutralny cień tylko tam, gdzie wyjaśnia warstwę, np. dolny pasek. Zachowaj czytelne pola oraz dużo miejsca na długie nazwy; bez dużych pustych pasów nad treścią.

## Wariant ciemny — dopisz do wspólnego promptu

Odtwórz dokładnie ten sam układ, dane, rozmiary i hierarchię w trybie ciemnym. Tło #101216, powierzchnie #191D24, pomocnicze #222833, tekst #F0F3F8, pomocniczy #AAB6C8, ramki #394353. Główna akcja #245BDB z białym tekstem; aktywny tekst i focus #8AB4FF, zaznaczenie #202E49. Ostrzeżenie #30291C z tekstem #F0CD81. Głębia wynika z poziomów powierzchni, nie z poświaty. Niebieski nie zalewa całego tła. Ustaw color-scheme: dark także dla kontrolek natywnych.

## Prompt wykonawczy po akceptacji

Wdróż zaakceptowany PLAN-I-DESIGN.md w istniejącym projekcie Flask/Jinja/CSS/vanilla JS. Najpierw odczytaj stan repozytorium i aktualne zmiany. Użyj obecnych generatorów DOCX, nazw pól, reguł walidacji i formatu żądań. Ujednolić komponenty przez makra Jinja i zmienne CSS. Wprowadź kolejno ramę i tokeny, ekran 1, ekran 2, ekran 3, a potem animacje i końcowy przegląd. Nie imituj brakujących funkcji backendu; gdy wymagany stan nie jest dostępny, pokazuj uczciwy stan nieokreślony. Waliduj wymagane pola na podstawie wybranego dokumentu i aktualnych zależności. Chroń wprowadzone dane przy błędach i wracaniu między ekranami. Sprawdź pełne przejście, pliki wynikowe, oba motywy, klawiaturę, długie polskie teksty i reduced motion. Zakończ Web Design Guidelines i przebiegiem Unslop w ramach przyjętego kierunku. Security Audit pozostaw na późniejszą, osobną pracę.

Źródła: Impeccable (pbakaus), Web Design Guidelines (Vercel), Unslop — Damir Sokolovsky, CC BY 4.0.
