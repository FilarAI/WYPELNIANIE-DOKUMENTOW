"""Słowniki TERYT (GUS) offline: identyfikator działki / miejscowość → województwo, powiat, gmina.

Pliki źródłowe: app/data/terc.csv (jednostki podziału terytorialnego) i app/data/simc.csv
(miejscowości, tylko samodzielne – bez części miejscowości). Pobrane z eteryt.stat.gov.pl.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
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


@lru_cache(maxsize=1)
def _nazwy():
    """{nazwa małymi literami: nazwa oryginalna} i {województwo: [nazwy]} z SIMC."""
    oryginalne, wg_woj = {}, {}
    with open(DANE / "simc.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            oryginalne[r["NAZWA"].lower()] = r["NAZWA"]
            wg_woj.setdefault(r["WOJ"], set()).add(r["NAZWA"])
    return oryginalne, wg_woj


def popraw_miejscowosc(nazwa: str, kod_pocztowy: str = "", tekst=(), preferowany_kod: str = "") -> tuple[str, bool]:
    """Poprawia nazwę miejscowości zniekształconą przez OCR. Zwraca (nazwa, pewna).

    1. Nazwa jest w SIMC → bez zmian.
    2. Ten sam kod pocztowy stoi w innym miejscu dokumentu przy nazwie z SIMC → ta nazwa (pewna).
    3. Najbardziej podobna nazwa z województwa działki (domyślnie małopolskiego), tylko gdy wyraźnie
       wygrywa z drugą → propozycja do sprawdzenia. Inaczej nazwa bez zmian.
    """
    oryginalne, wg_woj = _nazwy()
    if not nazwa or nazwa.strip().lower() in oryginalne:
        return nazwa, True
    if kod_pocztowy:
        znalezione = Counter()
        for linia in tekst:
            for m in re.finditer(re.escape(kod_pocztowy) + r"\s+([^\d,.;:()]+)", linia):
                slowa = m.group(1).split()[:4]
                for n in range(len(slowa), 0, -1):
                    kandydat = " ".join(slowa[:n]).lower()
                    if kandydat in oryginalne:
                        # „Mszana” z linii „34-730 Mszana Doina” to urwana zła nazwa, nie potwierdzenie.
                        if not nazwa.lower().startswith(kandydat):
                            znalezione[kandydat] += 1
                        break
        if znalezione:
            return oryginalne[znalezione.most_common(1)[0][0]], True
    m = WZOR_IDENTYFIKATORA.search(preferowany_kod or "")
    oceny = sorted(((SequenceMatcher(None, nazwa.lower(), n.lower()).ratio(), n)
                    for n in wg_woj.get(m.group(1) if m else "12", ())), reverse=True)[:2]
    # ponytail: progi dobrane na kilku przykładach (0,7 i przewaga 0,1) – korygować przy fałszywych trafieniach.
    if oceny and oceny[0][0] >= 0.7 and (len(oceny) < 2 or oceny[0][0] - oceny[1][0] >= 0.1):
        return oceny[0][1], False
    return nazwa, False


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
