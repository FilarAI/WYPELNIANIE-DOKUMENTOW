"""Odczyt danych z obiegówki (.docx) biura FILAR-USŁUGI.

Obiegówka ma kilka stron (strony tytułowe PZT/PB, oświadczenia projektanta). Każda zawiera tabelę
z etykietami w lewej kolumnie (NAZWA INWESTYCJI, ADRES INWESTYCJI, INWESTOR: ...). Parser czyta
wszystkie tabele, porównuje te same pola między stronami i zwraca ostrzeżenia o różnicach.

Wynik `odczytaj_obiegowke()` to zwykły słownik (dane do formularza):
    nazwa_inwestycji, adres_inwestycji{...}, nieruchomosc{wojewodztwo, powiat, gmina},
    inwestorzy[{... + wojewodztwo, powiat, gmina}], kategoria_obiektu, data_opracowania,
    zawartosc_projektu, projektant_glowny, jednostka_projektowa{...}, zespol_projektowy[{...}],
    zrodla[nazwy stron], ostrzezenia[{pole, komunikat}]
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from typing import BinaryIO

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from app import teryt

# Pole w wyniku → możliwe etykiety w obiegówce (porównywane po normalizacji, z tolerancją literówek).
ETYKIETY = {
    "jednostka_projektowa": ["JEDNOSTKA PROJEKTOWA"],
    "nazwa_inwestycji": ["NAZWA INWESTYCJI", "NAZWA ZAMIERZENIA BUDOWLANEGO"],
    "adres_inwestycji": ["ADRES INWESTYCJI", "ADRES ZAMIERZENIA BUDOWLANEGO", "LOKALIZACJA"],
    "inwestor": ["INWESTOR", "INWESTORZY"],
    "kategoria_obiektu": ["KATEGORIA OBIEKTU"],
    "data_opracowania": ["DATA OPRACOWANIA"],
    "zawartosc_projektu": ["ZAWARTOSC PROJEKTU"],
    "projektant_glowny": ["PROJEKTANT GLOWNY"],
}
NAZWY_POL = {
    "jednostka_projektowa": "Jednostka projektowa",
    "nazwa_inwestycji": "Nazwa inwestycji",
    "adres_inwestycji": "Adres inwestycji",
    "inwestor": "Inwestor",
    "kategoria_obiektu": "Kategoria obiektu",
    "data_opracowania": "Data opracowania",
    "zawartosc_projektu": "Zawartość projektu",
    "projektant_glowny": "Projektant główny",
}
# Pola, które muszą być w obiegówce – brak = ostrzeżenie.
WYMAGANE = ["nazwa_inwestycji", "adres_inwestycji", "inwestor"]
# Pola porównywane między stronami (zawartość projektu z definicji różni się na każdej stronie).
POROWNYWANE = ["nazwa_inwestycji", "adres_inwestycji", "inwestor", "kategoria_obiektu", "data_opracowania"]

PROG_PODOBIENSTWA = 0.85
KOD_POCZTOWY = re.compile(r"(\d{2}-\d{3})\s*,?\s*([^\d,]*)")
PREFIKS_ULICY = re.compile(r"^(ul|al|os|pl)\.?\s+(.*)$", re.IGNORECASE)
ULICA_W_TEKSCIE = re.compile(r"(?:^|[\s,])((?:ul|al|os|pl)\.?\s.*)$", re.IGNORECASE)
ULICA_Z_NUMEREM =re.compile(r"^(.*?)[\s,]+(\d+\s?[a-zA-Z]?)(?:\s*(?:/|m\.?|lok\.?)\s*(\w+))?\s*,?$")
DZIALKA = re.compile(r"dz(?:iałk[ai])?\.?\s*(?:ewid|ew)?\.?\s*(?:nr\.?)?\s*((?:\d+(?:/\d+)?)(?:\s*[,i]\s*\d+(?:/\d+)?)*)",
                     re.IGNORECASE)
WYJATKI_MESKIE = {"kuba", "barnaba", "bonawentura", "kosma", "jarema", "boryna"}


# ---------------------------------------------------------------- tekst pomocniczo

def _czysc(tekst: str) -> str:
    return re.sub(r"[ \t ]+", " ", tekst or "").strip()


def _normalizuj_etykiete(tekst: str) -> str:
    bez_ogonkow = unicodedata.normalize("NFKD", tekst).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z]+", " ", bez_ogonkow.upper()).strip()


def _porownywalne(tekst: str) -> str:
    """Postać tekstu do porównań między stronami: bez cudzysłowów, interpunkcji, wielkości liter."""
    return re.sub(r"[\W_]+", " ", tekst.lower()).strip()


def _rozpoznaj_etykiete(tekst: str) -> str | None:
    norm = _normalizuj_etykiete(tekst)
    if not norm or len(norm) > 40:
        return None
    najlepsze, wynik = None, 0.0
    for pole, warianty in ETYKIETY.items():
        for wariant in warianty:
            r = difflib.SequenceMatcher(None, norm, wariant).ratio()
            if r > wynik:
                najlepsze, wynik = pole, r
    return najlepsze if wynik >= PROG_PODOBIENSTWA else None


def _tekst_komorki(komorka) -> str:
    linie = [_czysc(p.text) for p in komorka.paragraphs]
    return "\n".join(linia for linia in linie if linia)


def _komorki_wiersza(wiersz) -> list:
    """Komórki wiersza bez duplikatów (python-docx powtarza komórki scalone poziomo)."""
    wynik, widziane = [], set()
    for komorka in wiersz.cells:
        if id(komorka._tc) not in widziane:
            widziane.add(id(komorka._tc))
            wynik.append(komorka)
    return wynik


# ---------------------------------------------------------------- adresy i osoby

def _jest_linia_adresu(linia: str) -> bool:
    return bool(re.search(r"\d", linia) or PREFIKS_ULICY.match(linia))


def rozbierz_ulice(linia: str) -> dict:
    """'Ul. Polna 18/3' → {ulica: 'ul. Polna', nr_domu: '18', nr_lokalu: '3'}.
    Linia bez prefiksu ulicy, będąca nazwą miejscowości ('Pcim 123'), → {miejscowosc: 'Pcim', nr_domu: '123'}."""
    linia = _czysc(linia).rstrip(",")
    wynik = {"ulica": "", "nr_domu": "", "nr_lokalu": ""}
    prefiks = PREFIKS_ULICY.match(linia)
    reszta = prefiks.group(2) if prefiks else linia
    m = ULICA_Z_NUMEREM.match(reszta)
    nazwa = m.group(1).strip(" ,") if m else reszta
    if m:
        wynik["nr_domu"] = m.group(2).replace(" ", "")
        wynik["nr_lokalu"] = m.group(3) or ""
    if prefiks:
        wynik["ulica"] = f"{prefiks.group(1).lower()}. {nazwa}"
    elif teryt.z_miejscowosci(nazwa) is not None or not m:
        wynik["miejscowosc"] = nazwa
    else:
        wynik["ulica"] = nazwa
    return wynik


def rozbierz_adres(linie: list[str]) -> dict:
    """Linie adresu (ulica, 'kod miejscowość') → ulica, nr_domu, nr_lokalu, kod_pocztowy, miejscowosc, poczta."""
    adres = {"ulica": "", "nr_domu": "", "nr_lokalu": "", "kod_pocztowy": "", "miejscowosc": "", "poczta": ""}
    for linia in linie:
        kod = KOD_POCZTOWY.search(linia)
        if kod:
            adres["kod_pocztowy"] = kod.group(1)
            adres["poczta"] = _czysc(kod.group(2)).strip(",")
            przed = _czysc(linia[: kod.start()]).strip(",")
            if przed:
                adres.update({k: v for k, v in rozbierz_ulice(przed).items() if v})
        elif linia:
            adres.update({k: v for k, v in rozbierz_ulice(linia).items() if v})
    if not adres["miejscowosc"]:
        adres["miejscowosc"] = adres["poczta"]
    return adres


def zgadnij_plec(imie_nazwisko: str) -> str:
    """'K' dla imion żeńskich (kończących się na -a), w pozostałych przypadkach 'M'."""
    imie = (imie_nazwisko.split() or [""])[0].lower()
    return "K" if imie.endswith("a") and imie not in WYJATKI_MESKIE else "M"


def _rozdziel_osoby(linia: str) -> list[str]:
    czesci = [_czysc(c) for c in re.split(r",|;| i | oraz ", linia) if _czysc(c)]
    # "Jan i Anna Kowalscy" – nie rozdzielamy, gdy któraś część to samo imię.
    if len(czesci) > 1 and any(len(c.split()) < 2 for c in czesci):
        return [_czysc(linia)]
    return czesci


def rozbierz_inwestorow(tekst: str) -> list[dict]:
    """Komórka INWESTOR → lista osób z adresami. Obsługuje kilka osób ze wspólnym adresem
    ('Jan Kowalski i Anna Kowalska') oraz kilka osób z osobnymi adresami (kolejne bloki)."""
    grupy, biezaca = [], {"osoby": [], "adres": []}
    for linia in (l for l in tekst.split("\n") if l.strip()):
        if _jest_linia_adresu(linia):
            biezaca["adres"].append(linia)
        else:
            if biezaca["adres"]:
                grupy.append(biezaca)
                biezaca = {"osoby": [], "adres": []}
            biezaca["osoby"].extend(_rozdziel_osoby(linia))
    if biezaca["osoby"] or biezaca["adres"]:
        grupy.append(biezaca)

    inwestorzy = []
    for grupa in grupy:
        adres = rozbierz_adres(grupa["adres"])
        for osoba in grupa["osoby"] or [""]:
            inwestorzy.append({"imie_nazwisko": osoba, "plec": zgadnij_plec(osoba), **adres})
    return inwestorzy


def rozbierz_adres_inwestycji(tekst: str) -> dict:
    """'dz. ewid. 1358\\n120903_4.0002.1358\\nMyślenice ul. Polna 18' → słownik pól."""
    wynik = {"nr_dzialki": "", "identyfikator_dzialki": "", "miejscowosc": "", "ulica": "", "nr_domu": "",
             "kod_pocztowy": "", "tekst": tekst}
    identyfikatory = [m.group(0) for m in teryt.WZOR_IDENTYFIKATORA.finditer(tekst)]
    wynik["identyfikator_dzialki"] = ", ".join(identyfikatory)
    reszta = teryt.WZOR_IDENTYFIKATORA.sub(" ", tekst)
    dzialka = DZIALKA.search(reszta)
    if dzialka:
        wynik["nr_dzialki"] = _czysc(dzialka.group(1))
        reszta = reszta[: dzialka.start()] + " " + reszta[dzialka.end():]
    elif identyfikatory:
        wynik["nr_dzialki"] = ", ".join(i.rsplit(".", 1)[-1] for i in identyfikatory)

    # Obsługiwane m.in.: "Myślenice ul. Polna 18", "ul. Polna 18, 32-400 Myślenice",
    # "32-400 Myślenice, ul. Polna 18", "Pcim 123".
    miasto_z_kodu = ""
    for linia in (_czysc(l).strip(" ,") for l in reszta.split("\n")):
        if not linia or _normalizuj_etykiete(linia) in {"", "OBREB"}:
            continue
        kod = KOD_POCZTOWY.search(linia)
        if kod:
            wynik["kod_pocztowy"] = kod.group(1)
            po_kodzie = linia[kod.end(1):]
            ulica_po_kodzie = ULICA_W_TEKSCIE.search(po_kodzie)
            miasto = _czysc(po_kodzie[: ulica_po_kodzie.start(1)] if ulica_po_kodzie else po_kodzie).strip(" ,")
            if miasto and not re.search(r"\d", miasto):
                miasto_z_kodu = miasto
                po_kodzie = ulica_po_kodzie.group(1) if ulica_po_kodzie else ""
            linia = _czysc(linia[: kod.start()] + " " + po_kodzie).strip(" ,")
            if not linia:
                continue
        m = ULICA_W_TEKSCIE.search(linia)
        if m:
            przed = linia[: m.start(1)].strip(" ,")
            if przed:
                wynik["miejscowosc"] = przed
            wynik.update({k: v for k, v in rozbierz_ulice(m.group(1)).items() if k in ("ulica", "nr_domu") and v})
        else:
            czesci = rozbierz_ulice(linia)
            wynik["miejscowosc"] = czesci.get("miejscowosc") or wynik["miejscowosc"] or linia
            wynik["nr_domu"] = czesci.get("nr_domu") or wynik["nr_domu"]
            if czesci.get("ulica"):
                wynik["ulica"] = czesci["ulica"]
    if not wynik["miejscowosc"]:
        wynik["miejscowosc"] = miasto_z_kodu
    return wynik


def rozbierz_jednostke(tekst: str) -> dict:
    linie = tekst.split("\n")
    wynik = {"nazwa": linie[0] if linie else "", "osoba": "", "adres": "", "telefon": "", "tekst": tekst}
    osoby = []
    for linia in linie[1:]:
        if linia.lower().startswith("tel"):
            wynik["telefon"] = _czysc(linia.split(":", 1)[-1])
        elif KOD_POCZTOWY.search(linia):
            wynik["adres"] = linia.strip(" ,")
        else:
            osoby.append(linia)
    wynik["osoba"] = " ".join(osoby)
    return wynik


def _rozbierz_czlonka_zespolu(specjalnosc: str, osoba: str, uprawnienia: str) -> dict:
    linie = osoba.split("\n")
    rola = ""
    if linie and ":" in linie[0]:
        rola, reszta = linie[0].split(":", 1)
        linie = ([reszta] if reszta.strip() else []) + linie[1:]
    return {
        "specjalnosc": specjalnosc.strip(" :"),
        "rola": rola.strip(),
        "osoba": _czysc(" ".join(linie)),
        "uprawnienia": _czysc(uprawnienia.replace("\n", " ")),
    }


# ---------------------------------------------------------------- odczyt dokumentu

def _elementy_dokumentu(dokument):
    """Akapity i tabele w kolejności występowania w treści dokumentu."""
    for el in dokument.element.body.iterchildren():
        if el.tag.endswith("}p"):
            yield Paragraph(el, dokument)
        elif el.tag.endswith("}tbl"):
            yield Table(el, dokument)


def _odczytaj_tabele(tabela: Table) -> tuple[str | None, dict, list]:
    """Zwraca (tytuł z pierwszego wiersza lub None, {pole: tekst}, zespół projektowy)."""
    pola, zespol, tytul = {}, [], None
    w_zespole, ostatnia_specjalnosc = False, ""
    for nr, wiersz in enumerate(tabela.rows):
        komorki = _komorki_wiersza(wiersz)
        teksty = [_tekst_komorki(k) for k in komorki]
        if nr == 0 and len(teksty) == 1 and teksty[0] and not _rozpoznaj_etykiete(teksty[0]):
            tytul = teksty[0].replace("\n", " ")
            continue
        if teksty and _normalizuj_etykiete(teksty[0]).startswith("SPECJALNOSC"):
            w_zespole = True
            continue
        if w_zespole and len(teksty) >= 3:
            ostatnia_specjalnosc = teksty[0] or ostatnia_specjalnosc
            zespol.append(_rozbierz_czlonka_zespolu(ostatnia_specjalnosc, teksty[1], teksty[2]))
            continue
        i = 0
        while i < len(teksty):
            pole = _rozpoznaj_etykiete(teksty[i].replace("\n", " "))
            if pole and i + 1 < len(teksty) and not _rozpoznaj_etykiete(teksty[i + 1].replace("\n", " ")):
                pola.setdefault(pole, teksty[i + 1])
                i += 2
            else:
                i += 1
    return tytul, pola, zespol


def odczytaj_obiegowke(plik: str | BinaryIO) -> dict:
    dokument = docx.Document(plik)
    strony = []  # [(nazwa źródła, {pole: tekst}, zespół)]
    ostatni_akapit = ""
    for element in _elementy_dokumentu(dokument):
        if isinstance(element, Paragraph):
            if element.text.strip():
                ostatni_akapit = _czysc(element.text)
            continue
        tytul, pola, zespol = _odczytaj_tabele(element)
        if not pola:
            continue
        nazwa = tytul or ostatni_akapit or "tabela"
        nazwa = nazwa if len(nazwa) <= 60 else nazwa[:57] + "…"
        powtorzenia = sum(1 for s in strony if s[0] == nazwa or s[0].startswith(nazwa + " ("))
        strony.append((f"{nazwa} ({powtorzenia + 1})" if powtorzenia else nazwa, pola, zespol))

    if not strony:
        raise ValueError("Nie znaleziono w pliku tabel obiegówki (NAZWA INWESTYCJI, INWESTOR…). "
                         "Sprawdź, czy wgrano właściwy plik.")

    # Główne źródło: strona tytułowa „PROJEKT BUDOWLANY”, w razie braku pierwsza strona z inwestorem.
    glowna = next((s for s in strony if _normalizuj_etykiete(s[0]).startswith("PROJEKT BUDOWLANY")), None) \
        or next((s for s in strony if "inwestor" in s[1]), strony[0])
    ostrzezenia = []

    def wartosc(pole: str) -> str:
        if pole in glowna[1]:
            return glowna[1][pole]
        return next((s[1][pole] for s in strony if pole in s[1]), "")

    for pole in WYMAGANE:
        if not wartosc(pole):
            ostrzezenia.append({"pole": pole, "komunikat": f"Nie znaleziono pola „{NAZWY_POL[pole]}” w obiegówce."})

    for pole in POROWNYWANE:
        wersje = {}
        for nazwa, pola, _ in strony:
            if pole in pola:
                wersje.setdefault(_porownywalne(pola[pole]), []).append(nazwa)
        if len(wersje) > 1:
            opis = "; ".join(
                f"{', '.join(zrodla)}: „{_czysc(next(s[1][pole] for s in strony if s[0] == zrodla[0]).replace(chr(10), ' '))}”"
                for zrodla in wersje.values())
            ostrzezenia.append({"pole": pole,
                                "komunikat": f"Pole „{NAZWY_POL[pole]}” różni się między stronami obiegówki – {opis}"})

    # Adres inwestycji: składamy najpełniejszą wersję ze wszystkich stron (np. ulica jest tylko w oświadczeniach).
    adres = rozbierz_adres_inwestycji(wartosc("adres_inwestycji"))
    for _, pola, _ in strony:
        if "adres_inwestycji" in pola:
            inny = rozbierz_adres_inwestycji(pola["adres_inwestycji"])
            for klucz, v in inny.items():
                if klucz != "tekst" and v and not adres[klucz]:
                    adres[klucz] = v
    # Gdy obiegówka podaje tylko działkę, a działka leży w mieście, miejscowość wynika z kodu TERYT.
    if not adres["miejscowosc"]:
        adres["miejscowosc"] = teryt.miasto_z_identyfikatora(adres["identyfikator_dzialki"])

    inwestorzy =rozbierz_inwestorow(wartosc("inwestor")) if wartosc("inwestor") else []
    # Kod pocztowy działki: jeśli działka leży pod adresem inwestora, bierzemy jego kod.
    for inw in inwestorzy:
        if not adres["kod_pocztowy"] and adres["miejscowosc"] and \
                (inw["miejscowosc"], inw["ulica"].lower(), inw["nr_domu"]) == \
                (adres["miejscowosc"], adres["ulica"].lower(), adres["nr_domu"]):
            adres["kod_pocztowy"] = inw["kod_pocztowy"]

    # Województwo / powiat / gmina: działka z identyfikatora TERYT, inwestorzy z nazwy miejscowości (SIMC).
    jednostka_dzialki = teryt.z_identyfikatora(adres["identyfikator_dzialki"])
    if jednostka_dzialki is None:
        jednostka_dzialki = teryt.z_miejscowosci(adres["miejscowosc"]) or teryt.Jednostka()
        ostrzezenia.append({"pole": "nieruchomosc",
                            "komunikat": "Nie rozpoznano kodu TERYT w identyfikatorze działki "
                                         f"„{adres['identyfikator_dzialki']}” – sprawdź województwo, powiat i gminę."})
    for inw in inwestorzy:
        jednostka = teryt.z_miejscowosci(inw["miejscowosc"], adres["identyfikator_dzialki"])
        if jednostka is None and inw["miejscowosc"]:
            ostrzezenia.append({"pole": "inwestor",
                                "komunikat": f"Nie udało się jednoznacznie ustalić gminy dla miejscowości "
                                             f"„{inw['miejscowosc']}” ({inw['imie_nazwisko']}) – uzupełnij ręcznie."})
        inw.update(vars(jednostka or teryt.Jednostka()))

    return {
        "nazwa_inwestycji": wartosc("nazwa_inwestycji").replace("\n", " ").strip(" „”\"'"),
        "adres_inwestycji": adres,
        "nieruchomosc": vars(jednostka_dzialki),
        "inwestorzy": inwestorzy,
        "kategoria_obiektu": wartosc("kategoria_obiektu"),
        "data_opracowania": wartosc("data_opracowania"),
        "zawartosc_projektu": wartosc("zawartosc_projektu").replace("\n", "; "),
        "projektant_glowny": wartosc("projektant_glowny").replace("\n", " "),
        "jednostka_projektowa": rozbierz_jednostke(wartosc("jednostka_projektowa")),
        "zespol_projektowy": glowna[2] or next((s[2] for s in strony if s[2]), []),
        "zrodla": [s[0] for s in strony],
        "ostrzezenia": ostrzezenia,
    }
