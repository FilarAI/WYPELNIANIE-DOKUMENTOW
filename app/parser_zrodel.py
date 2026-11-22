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
    "decyzja": "Decyzja o pozwoleniu na budowę / rozbiórkę",
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


POZWOLENIE = re.compile(r"udzielam\s+pozwolen\w*\s+na\s+(?:budow|rozbior|rozbiork)")
LICZBA_DZIESIETNA = r"\d+(?:\s\d{3})*[,.]\d{1,2}"
MIESIACE = {"stycz": 1, "lut": 2, "marc": 3, "kwiet": 4, "maj": 5, "czerw": 6, "lip": 7, "sierp": 8,
            "wrzes": 9, "pazdz": 10, "listop": 11, "grud": 12}
# Siedziby starostw, gdy nagłówek z nazwą organu jest nieczytelny w skanie.
ORGAN_Z_MIEJSCOWOSCI = {"nowy targ": "Nowotarskiego", "limanowa": "Limanowskiego", "myslenice": "Myślenickiego",
                        "zakopane": "Tatrzańskiego", "sucha beskidzka": "Suskiego", "nowy sacz": "Nowosądeckiego"}
NAZWA_W_MIANOWNIKU = {"budowę": "budowa", "nadbudowę": "nadbudowa", "przebudowę": "przebudowa",
                      "rozbudowę": "rozbudowa", "odbudowę": "odbudowa", "rozbiórkę": "rozbiórka"}


def _start_decyzji(linie: list[tuple[int, str]]) -> int:
    # Zdanie „udzielam pozwolenia na budowę” bywa w skanach przełamane i z błędami OCR.
    for i, (_, t) in enumerate(linie):
        if re.search(r"\bdecyzj\w*\s+nr\b", _norm(t)) and \
                POZWOLENIE.search(" ".join(_norm(x) for _, x in linie[i:i + 15])):
            return i
    return -1


def _organ(linie: list[tuple[int, str]], start: int) -> tuple[str, tuple[int, str]] | None:
    for w in linie[max(0, start - 8):start + 1] + linie[start + 1:]:
        m = re.search(r"\bstarost\w*\s+([a-ząćęłńóśźż]+?)(sk|ck)(?:i|iego|iemu|im)\b", w[1], re.I)
        if m:
            return "Starostę " + (m.group(1) + m.group(2)).capitalize() + "iego", w
    for w in linie[max(0, start - 8):start + 4]:
        for miejscowosc, organ in ORGAN_Z_MIEJSCOWOSCI.items():
            if _norm(w[1]).startswith(miejscowosc + " "):
                return "Starostę " + organ, w
    return None


def _data_decyzji(linie: list[tuple[int, str]], start: int) -> tuple[str, tuple[int, str]] | None:
    # Data z linii „Nowy Targ, (dnia) 12.10.2020 r.” przy nagłówku, nie z treści (tam jest data wniosku).
    for w in linie[max(0, start - 8):start + 4]:
        m = re.search(r"^[A-ZŁŚŻŹĆ][^,]{2,30},\s*(?:dnia\s*)?(\d{1,2})\s*[.-]\s*(\d{1,2})\s*[.-]\s*(\d{4})", w[1].strip())
        if m:
            return f"{int(m.group(1)):02d}.{int(m.group(2)):02d}.{m.group(3)}", w
        m = re.search(r",\s*(?:dnia\s*)?(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", w[1], re.I)
        miesiac = next((nr for rdzen, nr in MIESIACE.items() if m and _norm(m.group(2)).startswith(rdzen)), 0)
        if m and miesiac:
            return f"{int(m.group(1)):02d}.{miesiac:02d}.{m.group(3)}", w
    return None


def _inwestorzy_decyzji(linie: list[tuple[int, str]]) -> tuple[list[str], tuple[int, str] | None]:
    # Mianownik („Państwo Jan i Anna Nowak”, „Pani Anna Nowak”, „Pan Jan Nowak”) zwykle jest w uzasadnieniu;
    # w sentencji imiona są odmienione („Państwa Jana i Anny”), więc ich nie zgadujemy.
    wzory = [r"\bPaństwo\s+([A-ZŁŚŻŹĆ]\w+\s+i\s+[A-ZŁŚŻŹĆ]\w+\s+[A-ZŁŚŻŹĆ][\w-]+)",
             r"\bPani\s+([A-ZŁŚŻŹĆ]\w*a\s+[A-ZŁŚŻŹĆ][\w-]+)", r"\bPan\s+([A-ZŁŚŻŹĆ]\w+\s+[A-ZŁŚŻŹĆ][\w-]+)"]
    for w in linie:
        for wzor in wzory:
            for m in re.finditer(wzor, w[1]):
                przed = _norm(w[1][max(0, m.start() - 40):m.start()])
                if re.search(r"pelnomocni|reprezent|przez", przed) or "jachimowsk" in _norm(m.group(1)):
                    continue
                osoby = _osoby(m.group(1)) if wzor.startswith(r"\bPaństwo") else [m.group(1)]
                if osoby:
                    return osoby, w
    return [], None


def _adres_z_linii(wiersze: list[tuple[int, str]]) -> tuple[str, tuple[int, str]] | None:
    for w in wiersze:
        m = re.search(r"\bzam\.?\s*[:,.]?", w[1], re.I)
        if m and re.search(r"\d{2}-\d{3}", w[1][m.start():]) and not re.match(r"\s*reprezent", w[1], re.I):
            return w[1][m.start():], w
    return None


def _popraw_miejscowosci(adres: dict, linie: list[tuple[int, str]], identyfikator: str, uwagi: list) -> None:
    """Miejscowość i pocztę zniekształcone przez OCR zamienia na nazwy z listy GUS (SIMC)."""
    tekst, stara_poczta = [t for _, t in linie], adres["poczta"]
    for pole, kod in (("poczta", adres["kod_pocztowy"]), ("miejscowosc", "")):
        stara = adres[pole]
        if pole == "miejscowosc" and stara == stara_poczta:
            adres[pole] = adres["poczta"]  # ta sama nazwa co poczta – już poprawiona
            continue
        nowa, pewna = teryt.popraw_miejscowosc(stara, kod, tekst, identyfikator)
        adres[pole] = nowa
        if nowa != stara and not pewna:
            uwagi.append(f"Ze skanu odczytano „{stara}”, przyjęto „{nowa}” (lista miejscowości GUS) – sprawdź adres inwestora.")


def _dane_decyzji(linie: list[tuple[int, str]], plik: str) -> tuple[dict, dict, list, list]:
    pola, dowody, inwestorzy, uwagi = {}, {}, [], []
    start = _start_decyzji(linie)
    if start < 0:
        raise ValueError("Nie znaleziono decyzji o pozwoleniu na budowę lub rozbiórkę. Sprawdź wybrany typ pliku.")
    koniec = next((i for i in range(start + 1, min(start + 150, len(linie)))
                   if _norm(linie[i][1]).startswith("uzasadni")), min(start + 100, len(linie)))
    sentencja = linie[start:koniec]
    naglowek = linie[max(0, start - 8):start + 4]

    def wpisz(klucz, wartosc, wiersz, uwaga=""):
        if wartosc and klucz not in pola:
            pola[klucz] = wartosc.strip(" ,.;:")
            dowody[klucz] = _dowod(wiersz, plik, uwaga)

    m = re.search(r"decyzj\w*\s+nr\.?\s*([\w.-]+(?:\s*/\s*[\w.-]+)?)", linie[start][1], re.I)
    if m:
        wpisz("zak.pozwolenie_numer", re.sub(r"\s+", "", m.group(1)), linie[start])
    for w in naglowek:
        m = re.search(r"(?:nasz\s+znak|znak\s*:)\s*:?\s*([A-ZĄ-Ż][\w./-]+)", w[1], re.I)
        if m:
            wpisz("zak.pozwolenie_znak", m.group(1), w)
    for w in naglowek:
        m = re.search(r"\b([A-Z]{2,}\w*(?:\.\w+)*\.67\d\d(?:\.\w+)+)", w[1])
        if m:
            wpisz("zak.pozwolenie_znak", m.group(1), w, "Znak odczytany ze skanu – sprawdź.")
    organ = _organ(linie, start)
    if organ:
        wpisz("zak.pozwolenie_organ", *organ)
    data = _data_decyzji(linie, start)
    if data:
        wpisz("zak.pozwolenie_data", *data)

    # Działki: linia z „działce/działkach (nr) ewid. nr …” i ciąg dalszy w kolejnych liniach skanu.
    i = next((i for i, (_, t) in enumerate(sentencja)
              if re.search(r"dzia[lł]\w*\s+(?:nr\.?\s*ewid\w*\.?|ew\w*\.?\s*(?:ozn\.?\s*)?nr\.?)", t, re.I)), -1)
    if i >= 0:
        wiersz = sentencja[i]
        czesci = [wiersz[1]]
        for _, t in sentencja[i + 1:i + 4]:
            if re.match(r"(?:parametr|o nastepuj|dane techn|kategoria|budynek|zgodnie z projekt)", _norm(t)):
                break
            czesci.append(t)
        blok = " ".join(czesci)
        m = re.search(r"dzia[lł]\w*\s+(?:nr\.?\s*ewid\w*\.?|ew\w*\.?\s*(?:ozn\.?\s*)?nr\.?)\s*:?(.{1,220}?)"
                      r"(?=w\s+miejscowo|położon|obręb|jedn|\(|;|$)", blok, re.I)
        numery = NUMER_DZIALKI.findall(m.group(1)) if m else []
        if numery:
            wpisz("adres.nr_dzialki", ", ".join(dict.fromkeys(numery)), wiersz)
            droga = re.search(r"drog[^)]{0,90}?dz\.\s*ewid\.?\s*(?:ozn\.?)?\s*nr\s*(\d+(?:/\d+)?)", blok, re.I)
            if droga:
                wpisz("adres.dzialki_drogowe", droga.group(1), wiersz)
        miejsce = re.search(r"w\s+miejscowości\s+([^,()]+?)(?=\s*,|\s+obręb|\s*\(|$)", blok, re.I)
        if miejsce:  # bez „w miejscowości” nie zgadujemy z nazwy obrębu: inna miejscowość blokuje zestaw
            wpisz("adres.miejscowosc", miejsce.group(1), wiersz)
        jednostka = re.search(r"\b(\d{6})\s*\.?\s*_\s*([1-9])\b", blok)
        obreb = re.search(r"obręb\w*\s*(?:ew\w*\.?)?\s*:?\s*(\d{4})\b", blok, re.I)
        if jednostka and obreb and numery:
            kod = f"{jednostka.group(1)}_{jednostka.group(2)}.{obreb.group(1)}"
            wpisz("adres.identyfikator_dzialki", ", ".join(f"{kod}.{nr}" for nr in dict.fromkeys(numery)), wiersz,
                  "Sprawdź, czy wszystkie działki należą do inwestycji, a nie do drogi.")

    # Nazwa: linia po „obejmujące:” (w skanach np. „obelmulace”), w mianowniku.
    for i, (_, t) in enumerate(sentencja):
        n = _norm(t)
        if re.fullmatch(r"ob[a-z]{4,8}c[ea]", n) or n.startswith("obejmuj") or \
                re.match(r"(?:budowe|budowa|rozbiorke|rozbiorka)\s+budynku", n):
            wiersz = sentencja[i] if " " in n else (sentencja[i + 1] if i + 1 < len(sentencja) else None)
            if not wiersz:
                continue
            nazwa = re.split(r"\s+wraz\s+z\s+|\s+z\s+urządzeniami|\s*\(|\s+na\s+działk", wiersz[1], maxsplit=1,
                             flags=re.I)[0].strip(" ,.;:")
            nazwa = re.sub(r"^ob\w{4,8}c[ea]\s*:?\s*", "", nazwa, flags=re.I)
            for biernik, mianownik in NAZWA_W_MIANOWNIKU.items():
                nazwa = re.sub(rf"(?<!\w){biernik}(?!\w)", mianownik, nazwa, flags=re.I)
            if 3 < len(nazwa) <= 180:
                wpisz("nazwa_inwestycji", nazwa[0].upper() + nazwa[1:], wiersz)
                break

    # Parametry w jednej linii: „pow. zabudowy - 109,19 m2, …, kubatura - 1420,00 m3”.
    for w in sentencja:
        for klucz, etykieta in (("zak.kubatura_mieszkalna", r"kubatur\w*"), ("zak.pow_zabudowy_mieszkalna", r"zabudow\w*"),
                                ("zak.pow_uzytkowa_mieszkalna", r"u\w?ytkow\w*")):
            m = re.search(etykieta + r"\s*[-–:]?\s*(" + LICZBA_DZIESIETNA + ")", w[1], re.I)
            if m:
                wpisz(klucz, re.sub(r"\s", "", m.group(1)).replace(".", ","), w)
    # Parametry w kolumnach: najpierw etykiety, potem wartości w tej samej kolejności.
    tech = next((i for i, (_, t) in enumerate(sentencja)
                 if re.search(r"dane techniczne|danych techn|parametr", _norm(t))), -1)
    if tech >= 0:
        blok = []
        for w in sentencja[tech + 1:tech + 30]:
            if re.match(r"(?:projekt|zgodnie z projekt|z zachowaniem|autorzy)", _norm(w[1])):
                break
            blok.append(w)
        etykiety, dziesietne, calkowite = [], [], []
        for w in blok:
            n = _norm(w[1])
            for nazwa, wzor in (("kub", "kubatur"), ("zab", "zabudow"), ("uz", r"u.?ytkow"), ("lok", "lokal"), ("izb", r"\bizb")):
                if re.search(wzor, n):
                    etykiety.append(nazwa)
                    break
            if re.fullmatch(r"[\d\s,.m²³23?l]+", w[1].strip()) and re.search(r"\d", w[1]):
                bez_jednostek = re.sub(r"m\s*[23²³?]|ml|m\b", "|", w[1])
                liczby = re.findall(LICZBA_DZIESIETNA, bez_jednostek)
                if liczby:
                    dziesietne += [(re.sub(r"\s", "", x).replace(".", ","), w) for x in liczby]
                elif re.fullmatch(r"\s*\d{1,2}[.,]?\s*", w[1]):
                    calkowite.append((w[1].strip(" .,"), w))
        klucze = {"kub": "zak.kubatura_mieszkalna", "zab": "zak.pow_zabudowy_mieszkalna",
                  "uz": "zak.pow_uzytkowa_mieszkalna", "lok": "zak.liczba_mieszkan", "izb": "zak.liczba_izb"}
        miary = [e for e in etykiety if e in ("kub", "zab", "uz")]
        kilka = len(dziesietne) > len(miary) or any(re.search(r"letnisk|gospodarcz|dla jednego budynku", _norm(w[1]))
                                                    for w in blok)
        for etykieta, (wartosc, w) in zip(miary, dziesietne):
            wpisz(klucze[etykieta], wartosc, w)
        if kilka:
            uwagi.append("Decyzja obejmuje kilka budynków – sprawdź parametry budynku mieszkalnego i liczbę izb/lokali.")
        else:
            for etykieta, (wartosc, w) in zip([e for e in etykiety if e in ("lok", "izb")], calkowite):
                wpisz(klucze[etykieta], wartosc, w)

    if len(pola.get("adres.nr_dzialki", "").split(", ")) > 1:
        uwagi.append("Decyzja wymienia kilka działek. Sprawdź, które dotyczą nieruchomości w PB-5, a które drogi lub infrastruktury.")

    osoby, wiersz = _inwestorzy_decyzji(linie[start:])
    if osoby:
        dowody["inwestorzy"] = _dowod(wiersz, plik)
        adres = _adres_z_linii([wiersz] + [w for w in sentencja if w is not wiersz])
        adres_pola = _adres_inwestora(adres[0]) if adres else _adres_inwestora("")
        _popraw_miejscowosci(adres_pola, linie, pola.get("adres.identyfikator_dzialki", ""), uwagi)
        jednostka = teryt.z_miejscowosci(adres_pola["miejscowosc"], pola.get("adres.identyfikator_dzialki", ""))
        inwestorzy = [{"imie_nazwisko": osoba, "plec": zgadnij_plec(osoba), **adres_pola,
                       **vars(jednostka or teryt.Jednostka())} for osoba in osoby]
        if adres_pola["miejscowosc"] and not jednostka:
            uwagi.append("Adres inwestora jest niepewny (nieczytelny skan) – sprawdź miejscowość i kod pocztowy.")
    else:
        uwagi.append("Nie udało się pewnie odczytać inwestorów z decyzji – wpisz ich w kroku 3.")
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
