# Dokumenty FILAR — system interfejsu v2

Zaakceptowany przez użytkownika kierunek: docs/projekt-ui/propozycja-v2/PLAN-I-DESIGN.md. Bieżące tokeny i reguły v2: app/static/ui-v2.css; podstawowe komponenty i starsze moduły formularzy: app/static/styl.css. Dokumentacja v1 w docs/projekt-ui/specyfikacja.md jest historyczna i nie rozstrzyga konfliktów z v2.

Spokojny, rzeczowy, precyzyjny interfejs biura projektowego. Niebieski #245BDB dla głównej akcji i wyboru; neutralne powierzchnie. Jasny: #F5F6F8 / #FFFFFF, tekst #182230 / #526071. Ciemny: #101216 / #191D24, tekst #F0F3F8 / #AAB6C8, link i focus #8AB4FF. Uwaga, błąd i sukces mają opis i znaczenie, nie służą dekoracji.

Jedna rodzina systemowa: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif. H1 28/36 600, H2 20/28 600, tytuły dokumentów 16/24 500, treść 14/22, etykiety 14/20 500, opisy 13/20. Odstępy 4/8/12/16/24/32/48 px. Pola i przyciski 44 px, promień 8 px, sekcje 12 px. Bez wersalików w podgrupach i dekoracyjnego glow. Logo dostarczone przez użytkownika jest zachowane.

Rama do 1440 px; szeroki obszar roboczy i panel kontekstu 280 px. Poniżej 1100 px jedna kolumna. Poniżej 600 px pasek generowania wraca do przepływu, aby nie zasłaniać pól i klawiatury. Focus wyraźny, dostępny skrót do treści, semantyczne kontrolki i etykiety.

Animacje pokazują zmianę stanu: hover 120–150 ms, spinner wyłącznie podczas odczytu/generowania, brak animowania wszystkich sekcji na wejściu. Reduced motion wyłącza ruch i płynne przewijanie. Nie pokazujemy niezmierzonego postępu ani statusów, których backend nie dostarcza.

Kolejność pracy: Impeccable → Web Design Guidelines → Unslop. Unslop: Damir Sokolovsky, CC BY 4.0, https://github.com/heydamir/unslop. Zaakceptowana specyfikacja ma pierwszeństwo przed ogólnymi sugestiami skilli.

Zmiana zaakceptowana przez użytkownika: sekcja „Wygląd uzupełnionych danych” otwiera formularz trzeciego ekranu, przed kontrolą braków. Wyróżnia ją niebieska ikona formatowania tekstu.

Upload: osobna karta każdego pliku z pełną nazwą, rozmiarem, godziną i sposobem dodania, wyborem rodzaju, rzeczywistym statusem odczytu i licznikiem 0–3. Wielkość tekstu interfejsu: standard / +15% / +30%, zapamiętywana lokalnie; nie zmienia dokumentów DOCX.

Aktualizacja responsywności: rama aplikacji na pełną szerokość, obszar roboczy do 1920 px z płynnymi marginesami 16–64 px. Upload wykorzystuje całą dostępną szerokość; jego wysokość dopasowuje się do okna. Formularze przechodzą do jednej kolumny na mniejszych ekranach, bez wymuszonego poziomego przewijania.
