# Dokumenty FILAR

Lokalna aplikacja Flask/Jinja/vanilla JS dla polskiego biura projektowego. Użytkownik wgrywa 1–3 źródła Word/PDF, wybiera spośród 15 typów dokumentów, sprawdza dane i zapisuje DOCX lub pobiera ZIP. Dane dotyczą jednej inwestycji; rozbieżności muszą pozostać widoczne. Proces działa na localhost, grafiki i fonty bez CDN.

Tryb pracy: Operate. Główne zadanie: odczytać źródła, skorygować dane i wygenerować dokumenty. Sukces oznacza prawdziwy wynik generowania, a nie samo wypełnienie inputów. Reguły wymaganych danych pochodzą z walidatorów dokumentów. Puste opcjonalne pola są dozwolone. Pliki źródłowe i szkic formularza przechowywane w pamięci procesu z godzinną ważnością; restart aplikacji je usuwa.

Zakres v2: trzy etapy robocze i wynik generowania w formularzu; niebieska identyfikacja, dostarczone logo, polskie etykiety, jasny/ciemny/systemowy motyw. Audyt bezpieczeństwa Cloudflare jest odłożony na późniejszą pracę.
