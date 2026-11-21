"""Prezentacja nazw i ostrzeżeń bez zmiany danych źródłowych."""
import re

_ALFABET = "aąbcćdeęfghijklłmnńoópqrsśtuvwxyzźż"


def klucz_nazwy(nazwa):
    return tuple(100 + _ALFABET.index(c) if c in _ALFABET else ord(c) for c in nazwa.casefold())


def ostrzezenie_ui(ostrzezenie, pliki):
    komunikat = ostrzezenie["komunikat"]
    plik = ""
    for zrodlo in pliki:
        prefix = zrodlo["nazwa"] + ": "
        if komunikat.startswith(prefix):
            plik, komunikat = zrodlo["nazwa"], komunikat[len(prefix):]
            break
    pole = re.search(r"[Pp]ol[ae] „([^”]+)”", komunikat)
    tytul = pole.group(1) if pole else "Sprawdź dane źródłowe"
    if "różni się między stronami" in komunikat:
        wskazowka = "Na stronach obiegówki są różne wartości. Porównaj je i wpisz poprawną wartość w formularzu poniżej."
        szczegoly = komunikat
    else:
        wskazowka, szczegoly = komunikat, ""
    return dict(tytul=tytul, wskazowka=wskazowka, plik=plik, szczegoly=szczegoly)
