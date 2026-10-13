"""Kandydaci pól z decyzji, teczek i tekstowych obiegówek.

Parser czyta tylko fragmenty związane z czterema dokumentami wynikowymi. Każda
wartość zachowuje krótki fragment źródła; nie interpretujemy tekstu pouczeń,
instrukcji urządzeń ani liczb z map jako danych budynku.
"""
from __future__ import annotations

import re
import unicodedata

from app import teryt
from app.parser_obiegowki import rozbierz_adres_inwestycji, rozbierz_inwestorow, rozbierz_ulice, zgadnij_plec

RODZAJE_ZRODEL = {
    "obiegowka": "Obiegówka",
    "decyzja": "Decyzja o pozwoleniu na budowę",
    "teczka": "Teczka dokumentacji budowy",
}
NUMER_DZIALKI = re.compile(r"\b\d{1,5}(?:/\d{1,5})?\b")
MIARA = re.compile(r"(\d[\d\s]*[,.]\d+|\d+)\s*m\s*([23])\b", re.I)


def _norm(tekst: str) -> str:
    tekst = unicodedata.normalize("NFKD", tekst.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/]+", " ", tekst)).strip()


def _dowod(wiersz: tuple[int, str], plik: str, uwaga: str = "") -> dict:
    nr, tekst = wiersz
    return {"plik": plik, "miejsce": f"strona {nr}" if nr else "fragment dokumentu",
            "fragment": tekst[:260], "uwaga": uwaga}


def _osoby(tekst: str) -> list[str]:
    tekst = re.sub(r"^(?:dla\s*:\s*)?(?:państwo|państwa|inwestorzy\s*,?\s*tj\.?\s*państwo)\s+", "", tekst,
                   flags=re.I).strip(" ,.;")
    # Pełne imiona w mianowniku: „Jan i Anna Nowak”. Przy odmianie
    # „Barbary i Karola” bez innego źródła wolimy pustą listę niż fałszywe osoby.
    m = re.search(r"\b([A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśźż]+)\s+i\s+"
                  r"([A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśźż]+)\s+"
                  r"([A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśźż-]+)\b", tekst)
    if m:
        pierwsze, drugie, nazwisko = m.groups()
        if pierwsze.endswith("y"):
            return []
        return [f"{pierwsze} {nazwisko}", f"{drugie} {nazwisko}"]
    m = re.search(r"\b([A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśźż]+)\s+([A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśźż-]+)\b", tekst)
    return [" ".join(m.groups())] if m else []


def _adres_inwestora(tekst: str) -> dict:
    wynik = {x: "" for x in ("ulica", "nr_domu", "nr_lokalu", "kod_pocztowy", "miejscowosc", "poczta")}
    tekst = re.sub(r"^.*?\bzam\.?\s*[:.]?\s*", "", tekst, flags=re.I)
    tekst = re.split(r",\s*reprezentowan", tekst, maxsplit=1, flags=re.I)[0].strip(" ,.;")
    m = re.search(r"(\d{2}-\d{3})\s+([A-ZŁŚŻŹĆŃÓ][\wąćęłńóśźż -]+?)\s+(\d+[A-Za-z]?)\s*$", tekst)
    if m:
        wynik.update(kod_pocztowy=m.group(1), miejscowosc=m.group(2).strip(),
                     poczta=m.group(2).strip(), nr_domu=m.group(3))
        return wynik
    m = re.search(r"^(.+?)\s+(\d+[A-Za-z]?)\s*,\s*(\d{2}-\d{3})\s+(.+)$", tekst)
    if m:
        miejsce, nr, kod, poczta = m.groups()
        wynik.update(kod_pocztowy=kod, miejscowosc=miejsce.strip(), poczta=poczta.strip(), nr_domu=nr)
        if miejsce.lower().startswith("ul."):
            wynik.update(rozbierz_ulice(f"{miejsce} {nr}"))
            wynik["miejscowosc"] = poczta.strip()
        return wynik
    return wynik


def _dane_decyzji(linie: list[tuple[int, str]], plik: str) -> tuple[dict, dict, list, list]:
    pola, dowody, inwestorzy, uwagi = {}, {}, [], []
    start = next((i for i, (_, t) in enumerate(linie)
                  if re.search(r"decyzja\s+nr\b", t, re.I)
                  and any("udzielam pozwolenia na budow" in _norm(nastepny)
                          for _, nastepny in linie[i:i + 15])), -1)
    if start < 0:
        raise ValueError("Nie znaleziono decyzji o pozwoleniu na budowę. Sprawdź wybrany typ pliku.")
    koniec = next((i for i in range(start + 1, min(start + 150, len(linie)))
                   if _norm(linie[i][1]) == "uzasadnienie"), min(start + 100, len(linie)))
    sentencja = linie[start:koniec]

    def wpisz(klucz, wartosc, wiersz, uwaga=""):
        if wartosc and klucz not in pola:
            pola[klucz] = wartosc.strip(" ,.;")
            dowody[klucz] = _dowod(wiersz, plik, uwaga)

    m = re.search(r"decyzja\s+nr\s+([\w./-]+)", linie[start][1], re.I)
    if m:
        wpisz("zak.pozwolenie_numer", m.group(1), linie[start])
    for w in linie[max(0, start - 5):start + 1]:
        m = re.search(r"(?:nasz\s+znak|znak\s*:)\s*([\w./-]+)", w[1], re.I)
        if m:
            wpisz("zak.pozwolenie_znak", m.group(1), w)
        if "starosta nowotarski" in _norm(w[1]):
            wpisz("zak.pozwolenie_organ", "Starostę Nowotarskiego", w)
    for w in sentencja[:8]:
        m = re.search(r"\bdnia\s+(\d{1,2}\.\d{1,2}\.\d{4})", w[1], re.I)
        if m:
            wpisz("zak.pozwolenie_data", m.group(1), w)
            break

    for w in sentencja:
        tekst = w[1]
        if re.search(r"^dla:\s*państw", tekst, re.I):
            m = re.search(r"\bzam\.?\s*[:,.]?", tekst, re.I)
            if m:
                wpisz("inwestor.adres", tekst[m.start():], w)
        m = re.search(r"\bna dział(?:kach|ce)\s+ewid\.?\s*(?:ozn\.?)?\s*nr\s*"
                      r"([^)]{1,220}?)(?=\s*,?\s*położon|\s*\(|$)", tekst, re.I)
        if m:
            numery = NUMER_DZIALKI.findall(m.group(1))
            if numery:
                wpisz("adres.nr_dzialki", ", ".join(dict.fromkeys(numery)), w)
                droga = re.search(r"drog[^)]{0,90}?dz\.\s*ewid\.?\s*(?:ozn\.?)?\s*nr\s*(\d+(?:/\d+)?)", tekst, re.I)
                if droga:
                    wpisz("adres.dzialki_drogowe", droga.group(1), w)
            miejsce = re.search(r"położon\w*\s+w\s+miejscowości\s+([^,()]+)", tekst, re.I)
            if miejsce:
                wpisz("adres.miejscowosc", miejsce.group(1), w)
            jednostka = re.search(r"\b(\d{6}_[1-9])\b", tekst)
            obreb = re.search(r"obręb\s*:?\s*(\d{4})\b", tekst, re.I)
            if jednostka and obreb and numery:
                identyfikatory = ", ".join(f"{jednostka.group(1)}.{obreb.group(1)}.{nr}" for nr in numery)
                wpisz("adres.identyfikator_dzialki", identyfikatory, w,
                       "Sprawdź, czy wszystkie działki należą do inwestycji, a nie do drogi.")
        if re.search(r"^budowę\s+budynku|^budowa\s+budynku", tekst, re.I):
            nazwa = re.split(r"\s+wraz\s+z\s+|\s*\(|\s+na\s+działk", tekst, maxsplit=1, flags=re.I)[0].strip(" ,")
            nazwa = re.sub(r"^budowę\b", "Budowa", nazwa, flags=re.I)
            if len(nazwa) <= 180:
                wpisz("nazwa_inwestycji", nazwa[0].upper() + nazwa[1:], w)

    # Decyzje z OCR mają często osobne akapity etykiet i liczb. Ograniczamy
    # odczyt do sekcji „dane techniczne budynku” i wartości z jednostkami.
    tech = next((i for i, (_, t) in enumerate(sentencja) if "dane techniczne budynku" in _norm(t)), -1)
    if tech >= 0:
        blok = sentencja[tech + 1:tech + 19]
        miary = [(m.group(1).replace(" ", "").replace(".", ","), m.group(2), w)
                 for w in blok for m in MIARA.finditer(w[1])]
        kubatury = [x for x in miary if x[1] == "3"]
        powierzchnie = [x for x in miary if x[1] == "2"]
        if kubatury:
            wpisz("zak.kubatura_mieszkalna", kubatury[0][0], kubatury[0][2])
        if powierzchnie:
            wpisz("zak.pow_zabudowy_mieszkalna", powierzchnie[0][0], powierzchnie[0][2])
        if len(powierzchnie) >= 2:
            wpisz("zak.pow_uzytkowa_mieszkalna", powierzchnie[1][0], powierzchnie[1][2])
        # Liczby bez jednostek następują po ostatniej powierzchni. Nie bierzemy
        # rzymskiej kategorii obiektu ani numerów uprawnień projektantów.
        if len(powierzchnie) >= 2:
            po = blok.index(powierzchnie[1][2]) + 1
            liczby = [(w[1].strip(" .,"), w) for w in blok[po:]
                      if re.fullmatch(r"\s*\d{1,2}[.,]?\s*", w[1])]
            if liczby:
                wpisz("zak.liczba_izb", liczby[0][0], liczby[0][1])
            if len(liczby) >= 2:
                wpisz("zak.liczba_mieszkan", liczby[1][0], liczby[1][1])

    if len(pola.get("adres.nr_dzialki", "").split(", ")) > 1:
        uwagi.append("Decyzja wymienia kilka działek. Sprawdź, które dotyczą nieruchomości w PB-5, a które drogi lub infrastruktury.")

    # Mianownik w uzasadnieniu albo protokołach ma pierwszeństwo przed
    # odmienionym „dla Państwa ...” w sentencji.
    for w in linie[start:min(start + 110, len(linie))]:
        m = re.search(r"inwestorzy\s*,?\s*tj\.?\s*państwo\s+([^,.;]+)", w[1], re.I)
        if m:
            osoby = _osoby(m.group(1))
            if osoby:
                inwestorzy = osoby
                dowody["inwestorzy"] = _dowod(w, plik)
                break
    if not inwestorzy:
        for w in sentencja:
            if re.search(r"^dla:\s*państw", w[1], re.I):
                osoby = _osoby(w[1].split(", zam.")[0])
                if osoby:
                    inwestorzy = osoby
                    dowody["inwestorzy"] = _dowod(w, plik, "Sprawdź odmianę imion i nazwisk.")
                else:
                    uwagi.append("Nie udało się pewnie odczytać inwestorów z odmienionego tekstu decyzji.")
                break
    if inwestorzy:
        adres = _adres_inwestora(pola.get("inwestor.adres", ""))
        jednostka = teryt.z_miejscowosci(adres["miejscowosc"], pola.get("adres.identyfikator_dzialki", ""))
        inwestorzy = [{"imie_nazwisko": osoba, "plec": zgadnij_plec(osoba), **adres,
                       **vars(jednostka or teryt.Jednostka())} for osoba in inwestorzy]
    pola.pop("inwestor.adres", None)
    return pola, dowody, inwestorzy, uwagi


def odczytaj_zrodlo(linie: list[tuple[int, str]], typ: str, plik: str) -> dict:
    if typ not in RODZAJE_ZRODEL:
        raise ValueError("Nieznany typ pliku.")
    if not linie:
        raise ValueError("Plik nie zawiera tekstu możliwego do odczytania.")
    if typ == "obiegowka":
        # Używane dla PDF obiegówki; dla DOCX główną drogą pozostaje parser tabel.
        tekst = "\n".join(t for _, t in linie)
        if not re.search(r"NAZWA\s+(?:INWESTYCJI|NWESTYCJI)|ADRES\s+INWESTYCJI", tekst, re.I):
            raise ValueError("Nie znaleziono etykiet obiegówki. Sprawdź typ pliku.")
        return _odczytaj_tekst_obiegowki(linie, plik)
    pola, dowody, inwestorzy, uwagi = _dane_decyzji(linie, plik)
    if typ == "teczka":
        # Tylko protokoły odbiorcze dotyczące wykonanych instalacji, z tymi
        # samymi danymi inwestycji. Projekt i katalogi produktów nie wystarczą.
        for i, w in enumerate(linie):
            if "PROTOKÓŁ ODBIORCZY" not in w[1].upper():
                continue
            naglowek = " ".join(x[1].upper() for x in linie[i:i + 6])
            if "INSTALACJI C.O." in naglowek and "KOTŁEM GAZOWYM" in naglowek:
                pola["zak.ogrzewanie"] = "gazowe"
                dowody["zak.ogrzewanie"] = _dowod(w, plik, "Z protokołu odbiorczego, sprawdź stan faktyczny.")
            if "PRZYŁĄCZA KANALIZACJI" in naglowek and "OCZYSZCZALNI ŚCIEKÓW" in naglowek:
                pola["zak.kanalizacja"] = "oczyszczalnia"
                dowody["zak.kanalizacja"] = _dowod(w, plik, "Z protokołu odbiorczego, sprawdź stan faktyczny.")
    return {"typ": typ, "plik": plik, "pola": pola, "dowody": dowody,
            "inwestorzy": inwestorzy, "uwagi": uwagi}


def _odczytaj_tekst_obiegowki(linie: list[tuple[int, str]], plik: str) -> dict:
    pola, dowody, inwestorzy, uwagi = {}, {}, [], []
    wzor_nazwy = re.compile(r"NAZWA\s+(?:INWESTYCJI|NWESTYCJI)\s*:?", re.I)
    wzor_adresu = re.compile(r"ADRES\s+INWESTYCJI\s*:?", re.I)
    wzor_inwestora = re.compile(r"INWESTOR(?:ZY)?\s*:?", re.I)
    propozycje_nazwy = []
    propozycje_adresu = []
    propozycje_inwestora = []
    for i, w in enumerate(linie):
        strona, tekst = w
        if m := wzor_nazwy.search(tekst):
            # W PDF tabela często ma kolejność: początek wartości, etykieta,
            # koniec wartości. Szukamy od otwierającego cudzysłowu do działki.
            poczatek = next((j for j in range(i, max(-1, i - 6), -1)
                             if linie[j][0] == strona and re.search(r"[„\"]|\b(?:budowa|nadbudowa)\b", linie[j][1], re.I)), i)
            fragmenty = [linie[j][1] for j in range(poczatek, i + 1) if linie[j][0] == strona]
            fragmenty[-1] = wzor_nazwy.sub(" ", fragmenty[-1])
            for x in linie[i + 1:i + 5]:
                if x[0] != strona or re.search(r"dz\.\s*ewid|ADRES\s+INWESTYCJI|INWESTOR\s*:", x[1], re.I):
                    break
                fragmenty.append(x[1])
            nazwa = " ".join(" ".join(fragmenty).split()).strip(" „”\"':|")
            if 12 <= len(nazwa) <= 300:
                propozycje_nazwy.append((nazwa, w))
        if wzor_adresu.search(tekst):
            fragmenty = []
            for x in linie[max(0, i - 1):i + 4]:
                if x[0] != strona:
                    continue
                if x != w and re.search(r"INWESTOR\s*:", x[1], re.I):
                    break
                if x != w and re.fullmatch(r"[A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśźż]+\s+[A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśźż-]+", x[1]):
                    continue
                fragmenty.append(wzor_adresu.sub(" ", x[1]))
            adres = rozbierz_adres_inwestycji("\n".join(fragmenty))
            jakosc = sum(bool(adres.get(x)) for x in ("identyfikator_dzialki", "nr_dzialki", "miejscowosc", "ulica"))
            propozycje_adresu.append((jakosc, adres, w))
        if m := wzor_inwestora.search(tekst):
            poprzedni = linie[i - 1][1] if i and linie[i - 1][0] == strona else ""
            nastepny = linie[i + 1][1] if i + 1 < len(linie) and linie[i + 1][0] == strona else ""
            nazwa = poprzedni if re.fullmatch(r"[\wąćęłńóśźż-]+(?:\s+i\s+[\wąćęłńóśźż-]+)?\s+[\wąćęłńóśźż-]+", poprzedni) else ""
            wartosc = "\n".join(x for x in (nazwa, tekst[m.end():].strip(" :|"), nastepny) if x)
            osoby = rozbierz_inwestorow(wartosc)
            if any(x.get("imie_nazwisko") for x in osoby):
                propozycje_inwestora.append((osoby, w))
    if propozycje_nazwy:
        nazwa, w = max(propozycje_nazwy, key=lambda x: (len(x[0]), x[1][0]))
        pola["nazwa_inwestycji"] = nazwa
        dowody["nazwa_inwestycji"] = _dowod(w, plik)
    if propozycje_adresu:
        _, adres, w = max(propozycje_adresu, key=lambda x: x[0])
        for k in ("miejscowosc", "ulica", "nr_domu", "kod_pocztowy", "nr_dzialki", "identyfikator_dzialki"):
            if adres.get(k):
                pola[f"adres.{k}"] = adres[k]
                dowody[f"adres.{k}"] = _dowod(w, plik)
    if propozycje_inwestora:
        inwestorzy, w = max(propozycje_inwestora, key=lambda x: sum(bool(v) for p in x[0] for v in p.values()))
        dowody["inwestorzy"] = _dowod(w, plik)
    if not pola and not inwestorzy:
        raise ValueError("Nie udało się odczytać danych z PDF obiegówki.")
    return {"typ": "obiegowka", "plik": plik, "pola": pola, "dowody": dowody,
            "inwestorzy": inwestorzy, "uwagi": uwagi}
