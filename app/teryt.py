"""Słowniki TERYT (GUS) offline: identyfikator działki / miejscowość → województwo, powiat, gmina.

Pliki źródłowe: app/data/terc.csv (jednostki podziału terytorialnego) i app/data/simc.csv
(miejscowości, tylko samodzielne – bez części miejscowości). Pobrane z eteryt.stat.gov.pl.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DANE = Path(__file__).parent / "data"

# Identyfikator działki: WWPPGG_R.OOOO.NR, np. 120903_4.0002.1358 (NR może zawierać "/", np. 1234/5).
WZOR_IDENTYFIKATORA = re.compile(r"\b(\d{2})(\d{2})(\d{2})_(\d)\.(\d{4})\.([\w/]+)")


@dataclass
class Jednostka:
    wojewodztwo: str = ""
    powiat: str = ""
    gmina: str = ""


@lru_cache(maxsize=1)
def _terc():
    """Zwraca słownik {(woj, pow, gmi, rodz): nazwa} – klucze puste dla wyższych poziomów."""
    wynik = {}
    with open(DANE / "terc.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            wynik[(r["WOJ"], r["POW"], r["GMI"], r["RODZ"])] = r["NAZWA"]
    return wynik


@lru_cache(maxsize=1)
def _simc():
    """Zwraca słownik {nazwa miejscowości (małymi literami): [(woj, pow, gmi, rodz), ...]}."""
    wynik = {}
    with open(DANE / "simc.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            wynik.setdefault(r["NAZWA"].lower(), []).append((r["WOJ"], r["POW"], r["GMI"], r["RODZ_GMI"]))
    return wynik


def jednostka_z_kodu(woj: str, pow: str, gmi: str) -> Jednostka:
    terc = _terc()
    wojewodztwo = terc.get((woj, "", "", ""), "").lower()
    powiat = terc.get((woj, pow, "", ""), "")
    # Nazwa gminy jest taka sama dla każdego rodzaju (miasto / obszar wiejski / gmina) – bierzemy pierwszą.
    gmina = next((n for (w, p, g, _), n in terc.items() if (w, p, g) == (woj, pow, gmi)), "")
    return Jednostka(wojewodztwo, powiat, gmina)


def z_identyfikatora(identyfikator: str) -> Jednostka | None:
    """120903_4.0002.1358 → małopolskie / myślenicki / Myślenice. None, gdy kod nieznany."""
    m = WZOR_IDENTYFIKATORA.search(identyfikator or "")
    if not m:
        return None
    jednostka = jednostka_z_kodu(m.group(1), m.group(2), m.group(3))
    return jednostka if jednostka.gmina else None


def z_miejscowosci(nazwa: str, preferowany_kod: str = "") -> Jednostka | None:
    """Szuka miejscowości w SIMC. Przy kilku miejscowościach o tej samej nazwie wybiera tę
    z tej samej gminy / powiatu / województwa co `preferowany_kod` (np. identyfikator działki).
    Zwraca None, gdy nie da się jednoznacznie wskazać miejscowości."""
    kandydaci = sorted(set(_simc().get((nazwa or "").strip().lower(), [])))
    if not kandydaci:
        return None
    m = WZOR_IDENTYFIKATORA.search(preferowany_kod or "")
    if len(kandydaci) > 1 and m:
        woj, pow, gmi = m.group(1), m.group(2), m.group(3)
        for dopasowanie in (
            lambda k: k[:3] == (woj, pow, gmi),
            lambda k: k[:2] == (woj, pow),
            lambda k: k[0] == woj,
        ):
            pasujace = [k for k in kandydaci if dopasowanie(k)]
            if pasujace:
                kandydaci = pasujace
                break
    gminy = {k[:3] for k in kandydaci}
    if len(gminy) != 1:
        return None
    woj, pow, gmi = gminy.pop()
    return jednostka_z_kodu(woj, pow, gmi)


def miasto_z_identyfikatora(identyfikator: str) -> str:
    """Nazwa miasta, w którym leży działka, gdy wynika z kodu TERYT; w przeciwnym razie pusty tekst.

    Rodzaj gminy w kodzie WWPPGG_R: 1 – gmina miejska, 4 – miasto w gminie miejsko-wiejskiej (nazwa miasta = nazwa
    gminy); 8 – dzielnica Warszawy, 9 – delegatura (nazwa miasta = nazwa powiatu, np. Warszawa, Kraków).
    Dla wsi (2, 5) kod nie wskazuje miejscowości, więc zwracamy pusty tekst.
    """
    m = WZOR_IDENTYFIKATORA.search(identyfikator or "")
    if not m:
        return ""
    woj, pow, gmi, rodzaj = m.group(1), m.group(2), m.group(3), m.group(4)
    if rodzaj in ("1", "4"):
        return _terc().get((woj, pow, gmi, rodzaj), "")
    if rodzaj in ("8", "9"):
        return jednostka_z_kodu(woj, pow, gmi).powiat
    return ""
