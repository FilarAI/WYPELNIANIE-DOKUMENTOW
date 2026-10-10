"""Wybór dokumentów tworzonych z jednej obiegówki."""
from __future__ import annotations

DOKUMENTY = {
    "pelnomocnictwo": "Pełnomocnictwo",
    "pb5": "PB-5 (osobno dla każdego inwestora)",
    "oswiadczenie": "Oświadczenie kierownika budowy",
    "zawiadomienie": "Zawiadomienie o zakończeniu budowy",
}

DOMYSLNE = ("pelnomocnictwo", "pb5")


def odczytaj_wybor(formularz, domyslne=False) -> tuple[str, ...]:
    wybrane = formularz.getlist("dokumenty")
    if domyslne and not wybrane:
        return DOMYSLNE
    if not wybrane or len(wybrane) != len(set(wybrane)) or any(x not in DOKUMENTY for x in wybrane):
        raise ValueError("Wybierz co najmniej jeden poprawny dokument.")
    return tuple(x for x in DOKUMENTY if x in wybrane)
