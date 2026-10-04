# Dokumenty FILAR – specyfikacja interfejsu

Źródło prawdy dla wyglądu programu. Makiety (`makieta-*.webp`, `komponenty.webp`) pokazują kierunek,
a przy rozbieżnościach decydują wartości z tego pliku. W kodzie wartości są zmiennymi CSS
na początku `app/static/styl.css`.

## Zasady
- Interfejs prawie monochromatyczny. Niebieski tylko dla aktywnego kroku, przycisków głównych, focusu,
  linków i zaznaczonych kontrolek. Zielony tylko po sukcesie, żółty tylko przy danych do sprawdzenia,
  czerwony tylko przy błędzie albo usuwaniu (i dopiero po najechaniu).
- Brak połączeń z internetem: font systemowy (SF Pro na Macu), ikony jako SVG w kodzie
  (`app/templates/_makra.html`, kształty Lucide), bez CDN i Google Fonts.
- Tylko jasny motyw.

## Kolory
| Token | Kolor | Token | Kolor |
|---|---|---|---|
| Tło | `#F3F4F6` | Niebieski | `#3478F6` |
| Powierzchnia | `#FFFFFF` | Niebieski hover / wciśnięty | `#2868DD` / `#1F5FCB` |
| Powierzchnia subtelna | `#F8FAFC` | Niebieski tło / ramka | `#EEF5FF` / `#B9D2FF` |
| Ramka / mocna | `#E4E7EC` / `#D0D5DD` | Sukces / tło / ramka | `#31966A` / `#EDF9F3` / `#B9E5CF` |
| Tekst 1 / 2 / 3 | `#111827` / `#667085` / `#98A2B3` | Uwaga ikona / tło / ramka | `#F59E0B` / `#FFF7DF` / `#F2DA9E` |
| Tekst przycisku | `#344054` | Uwaga tytuł / tekst | `#513C0B` / `#735C23` |
| Nieaktywny tekst / tło | `#A9B1BD` / `#F2F4F7` | Błąd / tło / ramka | `#D84A4A` / `#FFF1F0` / `#F3B0AC` |

## Typografia (SF Pro → Inter → systemowy)
| Styl | Rozmiar / interlinia | Grubość |
|---|---|---|
| H1 (każdy ekran) | 32 / 40 px | 700 |
| Tytuł sekcji | 18 / 26 px | 600 |
| Tytuł karty | 15–16 / 22–24 px | 600 |
| Podtytuł | 16 / 24 px | 400 |
| Tekst pól, przyciski | 14 / 20 px | 400 / 600 |
| Etykieta | 13 / 18 px | 500 |
| Podpowiedź | 12 / 17 px | 400 |

## Odstępy, zaokrąglenia, cienie
- Skala odstępów: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 px. Etykieta → pole 8, pola i sekcje 16,
  padding sekcji 24, karty inwestora 20, pasek kroków → H1 40, H1 → podtytuł 8.
- Zaokrąglenia: panel 20, sekcja i pole uploadu 16, alert i karty 12, pola i przyciski 10, checkbox 5 px.
- Cienie: panel `0 18px 50px rgba(16,24,40,.08), 0 2px 8px rgba(16,24,40,.04)`; karta `0 1px 3px rgba(16,24,40,.04)`;
  przycisk `0 1px 2px rgba(16,24,40,.08)`, hover `0 4px 12px rgba(52,120,246,.18)`; focus `0 0 0 3px rgba(52,120,246,.14)`.

## Szerokości
Obramowanie aplikacji maks. 1280 px (margines 32 px) → formularz i upload 820 (pole uploadu 760) →
ekran „Gotowe” 640 → ekran wyłączenia 520. Nagłówek 72 px, pasek kroków maks. 640 px.

## Komponenty
- **Pola:** wysokość 44, ramka `#E4E7EC`, focus: ramka niebieska i obwódka. Sekcja z ostrzeżeniem:
  żółta ramka, pasek z lewej i znacznik „Do sprawdzenia”.
- **Przyciski:** 44 px wysokości. Główny niebieski; drugorzędny biały z ramką `#D0D5DD`; neutralny („Wybierz…”)
  biały z niebieskim tekstem; tekstowy bez tła, hover `#EEF5FF`.
- **Pasek kroków:** kółka 36 px; aktywny i ukończony niebieskie (ukończony z ptaszkiem), przyszły `#EEF0F4`.
- **Karta inwestora:** „Usuń” szare, czerwone dopiero po najechaniu; ukryte, gdy jest jeden inwestor.
- **Pole uploadu:** 1.5 px przerywana ramka `#B9D2FF`. Stany: spoczynek, plik nad polem (tło `#F5F9FF`,
  ramka niebieska), wczytywanie (kółko ładowania i nazwa pliku), błąd (czerwony alert nad polem).

## Decyzje (odejścia od makiet)
1. Województwo, powiat i gmina to pola tekstowe (wypełniane z TERYT), nie listy rozwijane.
2. Bez checkboxów wyboru dokumentów: program zawsze tworzy pełnomocnictwo i PB-5.
   Sekcja „Dokumenty” ma datę pełnomocnictwa i opcję osoby upoważnionej w PB-5.
3. Po wybraniu pliku program od razu go wczytuje (stan „Wczytuję obiegówkę…”), bez stanu „Zmień plik”.
4. Logo z makiety (niebieski dom) jest tymczasowe, do czasu właściwego logo biura.
5. Ekran wyłączenia nie ma przycisku „Uruchom ponownie” (serwer już nie działa), tylko wskazówkę
   o ikonie na pulpicie.
6. Formularz pokazuje wszystkie prawdziwe pola (adres w częściach, jednostka administracyjna)
   pogrupowane podtytułami. Ostrzeżenia to lista w jednym żółtym bloku, bez przyklejania przy przewijaniu.

## Animacje
| Gdzie | Wyzwalacz | Ruch | Czas, krzywa |
|---|---|---|---|
| Treść ekranu | wejście na stronę | pojawienie + 8 px w górę | 400 ms, `cubic-bezier(.2,.8,.2,1)` |
| Sekcje formularza | wejście | jak wyżej, kolejno co 50 ms | 400 ms |
| Alert | wejście | pojawienie + 6 px w dół | 350 ms, opóźnienie 150 ms |
| Pasek kroków | wejście | aktywne kółko: jeden puls; ptaszek: wskoczenie | 1,2 s / 400 ms, sprężyna |
| Pole uploadu | najechanie | ikona 3 px w górę, ramka ciemnieje | 200–300 ms |
| Pole uploadu | plik nad polem | tło, ramka, powiększenie 1%, ikona unosi się | 200 ms, ikona 1 s w pętli |
| Pole uploadu | upuszczenie | kółko ładowania | 800 ms w pętli |
| Karta inwestora | dodanie / usunięcie | pojawienie z góry / zanik i zmniejszenie | 300 / 250 ms |
| Checkbox | zaznaczenie | ptaszek wskakuje | 200 ms, sprężyna |
| „Zapisz dokumenty” | kliknięcie | kółko ładowania, „Zapisuję…” | do przejścia strony |
| Ekran „Gotowe” | wejście | kółko sukcesu wskakuje, ptaszek się rysuje, pliki kolejno, statusy wskakują | 500 + 400 ms, pliki co 70 ms |
| Przyciski, pola | hover / focus | kolor, cień, obwódka | 150 ms |

Sprężyna: `cubic-bezier(.34,1.56,.64,1)`. Przy włączonym „Ogranicz ruch” w macOS animacje są wyłączone
(zostaje tylko wolniejsze kółko ładowania).
