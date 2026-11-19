"""Wybór dokumentów tworzonych z jednej obiegówki."""
from __future__ import annotations

DOKUMENTY = {
    "pelnomocnictwo": "Pełnomocnictwo",
    "pb5": "PB-5 (osobno dla każdego inwestora)",
    "oswiadczenie": "Oświadczenie kierownika budowy",
    "zawiadomienie": "Zawiadomienie o zakończeniu budowy",
    "ba4": "BA-4 — wniosek o wydanie dziennika budowy / rozbiórki",
    "egib": "Zgłoszenie zmian danych ewidencji gruntów i budynków",
    "egib_wypis": "EGiB — wniosek o wypis lub wyrys z operatu ewidencyjnego",
    "formularz_p": "Formularz P — udostępnienie materiałów zasobu geodezyjnego",
    "pelnomocnictwo_egib": "Pełnomocnictwo do spraw EGiB (wypis / wyrys)",
    "pb2": "PB-2 — zgłoszenie budowy lub innych robót (osobno dla każdego inwestora)",
    "pb2a": "PB-2a — zgłoszenie budowy lub przebudowy domu jednorodzinnego (osobno dla każdego inwestora)",
    "pb7": "PB-7 — wniosek o zmianę pozwolenia na budowę (osobno dla każdego inwestora)",
    "pb9": "PB-9 — wniosek o przeniesienie decyzji o pozwoleniu na budowę (osobno dla każdego nowego inwestora)",
    "pb1": "PB-1 — wniosek o pozwolenie na budowę (osobno dla każdego inwestora)",
    "os616": "OŚ-6165 — zaświadczenie o objęciu gruntu uproszczonym planem urządzenia lasu",
}

DOMYSLNE = ("pelnomocnictwo", "pb5")


def odczytaj_wybor(formularz, domyslne=False) -> tuple[str, ...]:
    wybrane = formularz.getlist("dokumenty")
    if domyslne and not wybrane:
        return DOMYSLNE
    if not wybrane or len(wybrane) != len(set(wybrane)) or any(x not in DOKUMENTY for x in wybrane):
        raise ValueError("Wybierz co najmniej jeden poprawny dokument.")
    return tuple(x for x in DOKUMENTY if x in wybrane)
