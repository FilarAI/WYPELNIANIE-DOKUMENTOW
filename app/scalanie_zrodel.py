"""Łączenie kandydatów z kilku plików i wykrywanie obcych inwestycji."""
from __future__ import annotations

import io
import re
import unicodedata

from app import teryt
from app.odczyt_plikow import odczytaj_tekst
from app.parser_obiegowki import odczytaj_obiegowke
from app.parser_zrodel import RODZAJE_ZRODEL, _osoby, odczytaj_zrodlo

NAZWY = {
    "nazwa_inwestycji": "Nazwa inwestycji",
    "adres.miejscowosc": "Miejscowość inwestycji",
    "adres.nr_dzialki": "Numery działek",
    "adres.identyfikator_dzialki": "Identyfikatory działek",
    "zak.pozwolenie_znak": "Znak pozwolenia",
    "zak.pozwolenie_numer": "Numer decyzji",
    "zak.pozwolenie_data": "Data wydania pozwolenia",
    "zak.pozwolenie_organ": "Organ wydający pozwolenie",
    "zak.kubatura_mieszkalna": "Kubatura budynku",
    "zak.pow_zabudowy_mieszkalna": "Powierzchnia zabudowy",
    "zak.pow_uzytkowa_mieszkalna": "Powierzchnia użytkowa",
    "zak.liczba_izb": "Liczba izb",
    "zak.liczba_mieszkan": "Liczba mieszkań",
    "zak.ogrzewanie": "Ogrzewanie",
    "zak.kanalizacja": "Odprowadzenie ścieków",
}


def _norm(wartosc: str) -> str:
    tekst = unicodedata.normalize("NFKD", wartosc.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9/]+", "", tekst)


def _dzialki(wartosc: str) -> set[str]:
    return set(re.findall(r"\b\d{1,5}(?:/\d{1,5})?\b", wartosc or ""))


def _nazwy_osob(inwestorzy: list[dict]) -> set[str]:
    wynik = set()
    for osoba in inwestorzy:
        nazwa = osoba.get("imie_nazwisko", "")
        rozdzielone = _osoby(nazwa) if " i " in nazwa else []
        wynik.update(_norm(x) for x in (rozdzielone or [nazwa]) if x)
    return wynik


def _z_obiegowki(zawartosc: bytes, plik: str) -> dict:
    dane = odczytaj_obiegowke(io.BytesIO(zawartosc))
    pola = {"nazwa_inwestycji": dane["nazwa_inwestycji"]}
    for klucz, wartosc in dane["adres_inwestycji"].items():
        if klucz != "tekst" and wartosc:
            pola[f"adres.{klucz}"] = wartosc
    for klucz, wartosc in dane["nieruchomosc"].items():
        if wartosc:
            pola[f"nier.{klucz}"] = wartosc
    dowod = {"plik": plik, "miejsce": "tabele obiegówki", "fragment": "", "uwaga": ""}
    return {"typ": "obiegowka", "plik": plik, "pola": pola,
            "dowody": {klucz: {**dowod, "fragment": str(wartosc)[:260]} for klucz, wartosc in pola.items()} |
                       {"inwestorzy": {**dowod, "fragment": ", ".join(i.get("imie_nazwisko", "") for i in dane["inwestorzy"])[:260]}},
            "inwestorzy": dane["inwestorzy"], "uwagi": [x["komunikat"] for x in dane["ostrzezenia"]],
            "zrodla_obiegowki": dane["zrodla"]}


def _puste_dane() -> dict:
    return {"nazwa_inwestycji": "",
            "adres_inwestycji": {k: "" for k in ("miejscowosc", "ulica", "nr_domu", "kod_pocztowy",
                                                 "nr_dzialki", "identyfikator_dzialki")},
            "nieruchomosc": {k: "" for k in ("wojewodztwo", "powiat", "gmina")},
            "inwestorzy": [], "zakonczenie": {}, "kategoria_obiektu": "",
            "data_opracowania": "", "projektant_glowny": "", "zespol_projektowy": [],
            "zrodla": [], "ostrzezenia": [], "pochodzenie": [], "konflikty": [], "potwierdzenia": [], "blokada_zestawu": False,
            "pliki_zrodlowe": [], "dzialki_do_wyboru": []}


def _waga(typ: str, pole: str) -> int:
    if pole.startswith("zak."):
        if pole in ("zak.ogrzewanie", "zak.kanalizacja"):
            return 3 if typ == "teczka" else 0
        return 3 if typ == "decyzja" else 2 if typ == "teczka" else 0
    return 3 if typ == "obiegowka" else 2 if typ == "teczka" else 1


def _cel_formularza(pole: str) -> str:
    if pole == "nazwa_inwestycji":
        return pole
    if pole.startswith("adres."):
        return "adres-" + pole.split(".", 1)[1]
    if pole.startswith("nier."):
        return "nier-" + pole.split(".", 1)[1]
    if pole.startswith("zak.") and pole != "zak.pozwolenie_numer":
        return "zak-" + pole.split(".", 1)[1]
    return ""


def _ustaw(dane: dict, pole: str, wartosc: str) -> None:
    if pole == "nazwa_inwestycji":
        dane[pole] = wartosc
    elif pole.startswith("adres."):
        dane["adres_inwestycji"][pole.split(".", 1)[1]] = wartosc
    elif pole.startswith("nier."):
        dane["nieruchomosc"][pole.split(".", 1)[1]] = wartosc
    elif pole.startswith("zak."):
        dane["zakonczenie"][pole.split(".", 1)[1]] = wartosc


def odczytaj_zestaw(pliki: list[tuple[str, str, bytes]]) -> dict:
    if not 1 <= len(pliki) <= 3:
        raise ValueError("Wgraj od jednego do trzech plików.")
    odczytane = []
    for typ, nazwa, zawartosc in pliki:
        if typ not in RODZAJE_ZRODEL:
            raise ValueError("Wybierz poprawny typ każdego pliku.")
        linie, ocr = odczytaj_tekst(zawartosc, nazwa)
        if typ == "obiegowka" and nazwa.lower().endswith(".docx"):
            zrodlo = _z_obiegowki(zawartosc, nazwa)
        else:
            zrodlo = odczytaj_zrodlo(linie, typ, nazwa)
        if ocr:
            zrodlo["uwagi"].append("Odczyt skanu PDF wymaga szczególnie dokładnego sprawdzenia.")
        odczytane.append(zrodlo)

    dane = _puste_dane()
    dane["pliki_zrodlowe"] = [{"nazwa": s["plik"], "typ": RODZAJE_ZRODEL[s["typ"]]} for s in odczytane]
    dane["zrodla"] = [s["plik"] for s in odczytane]
    for s in odczytane:
        dane["ostrzezenia"].extend({"pole": "zrodla", "komunikat": f"{s['plik']}: {x}"} for x in s["uwagi"])

    # Konflikt całego zestawu: różne osoby, miejscowości, rozłączne działki lub znaki decyzji.
    zestawy = [_nazwy_osob(s["inwestorzy"]) for s in odczytane if s["inwestorzy"]]
    miejscowosci = {_norm(s["pola"]["adres.miejscowosc"]) for s in odczytane
                   if s["pola"].get("adres.miejscowosc")}
    dzialki = [_dzialki(s["pola"].get("adres.nr_dzialki", "")) for s in odczytane
               if s["pola"].get("adres.nr_dzialki")]
    znaki = {_norm(s["pola"]["zak.pozwolenie_znak"]) for s in odczytane
             if s["pola"].get("zak.pozwolenie_znak")}
    if (any(a and b and a.isdisjoint(b) for i, a in enumerate(zestawy) for b in zestawy[i + 1:])
            or len(miejscowosci) > 1
            or any(a and b and a.isdisjoint(b) for i, a in enumerate(dzialki) for b in dzialki[i + 1:])
            or len(znaki) > 1):
        dane["blokada_zestawu"] = True
        dane["ostrzezenia"].insert(0, {"pole": "zrodla", "komunikat":
            "Wgrane pliki wyglądają na różne inwestycje. Usuń obcy plik i wgraj zestaw ponownie."})

    kandydaci = {}
    for s in odczytane:
        for pole, wartosc in s["pola"].items():
            if wartosc and (pole in NAZWY or pole.startswith("adres.") or pole.startswith("nier.")):
                kandydaci.setdefault(pole, []).append((s, wartosc))
    for pole, propozycje in kandydaci.items():
        propozycje.sort(key=lambda x: _waga(x[0]["typ"], pole), reverse=True)
        rozne = {_norm(w) for _, w in propozycje}
        wybrana = propozycje[0]
        # Opisy inwestycji w obiegówce i decyzji często różnią się szczegółowością.
        # Wtedy zachowujemy obiegówkę, ale pokazujemy inne brzmienie.
        konflikt = len(rozne) > 1 and pole != "nazwa_inwestycji"
        if konflikt:
            dane["konflikty"].append({"pole": pole, "etykieta": NAZWY.get(pole, pole),
                                      "cel": _cel_formularza(pole),
                                      "warianty": [{"wartosc": w, **s["dowody"].get(pole, {"plik": s["plik"]})}
                                                   for s, w in propozycje]})
            dane["ostrzezenia"].append({"pole": "adres_inwestycji" if pole.startswith("adres.") else
                                        "zakonczenie" if pole.startswith("zak.") else "inwestor",
                                        "komunikat": f"Różne wartości pola „{NAZWY.get(pole, pole)}” – wybierz w formularzu."})
            continue
        if pole in {"zak.ogrzewanie", "zak.kanalizacja"}:
            dowod = wybrana[0]["dowody"].get(pole, {"plik": wybrana[0]["plik"]})
            dane["potwierdzenia"].append({"etykieta": NAZWY[pole], "cel": _cel_formularza(pole),
                                          "wartosc": wybrana[1], **dowod})
            continue
        _ustaw(dane, pole, wybrana[1])
        dowod = wybrana[0]["dowody"].get(pole)
        if dowod:
            dane["pochodzenie"].append({"etykieta": NAZWY.get(pole, pole), "wartosc": wybrana[1], **dowod})
        if len(rozne) > 1:
            dane["ostrzezenia"].append({"pole": "nazwa_inwestycji", "komunikat":
                "Nazwa inwestycji ma różne brzmienie w plikach. Przyjęto wersję z obiegówki, sprawdź ją."})

    inwestorzy = sorted((s for s in odczytane if s["inwestorzy"]),
                       key=lambda s: _waga(s["typ"], "inwestorzy"), reverse=True)
    if inwestorzy:
        dane["inwestorzy"] = inwestorzy[0]["inwestorzy"]
        for osoba in dane["inwestorzy"]:
            if osoba.get("miejscowosc") and not osoba.get("gmina"):
                jednostka = teryt.z_miejscowosci(osoba["miejscowosc"],
                                                  dane["adres_inwestycji"].get("identyfikator_dzialki", ""))
                if jednostka:
                    osoba.update(vars(jednostka))
        dowod = inwestorzy[0]["dowody"].get("inwestorzy")
        if dowod:
            dane["pochodzenie"].append({"etykieta": "Inwestorzy", "wartosc":
                ", ".join(x.get("imie_nazwisko", "") for x in dane["inwestorzy"]), **dowod})
        if len({tuple(sorted(x)) for x in zestawy}) > 1:
            dane["ostrzezenia"].append({"pole": "inwestor", "komunikat":
                "Listy inwestorów różnią się między plikami. Sprawdź każdą osobę i adres."})
    identyfikator = dane["adres_inwestycji"].get("identyfikator_dzialki", "")
    if identyfikator and not any(dane["nieruchomosc"].values()):
        jednostka = teryt.z_identyfikatora(identyfikator)
        if jednostka:
            dane["nieruchomosc"] = vars(jednostka)
    if not dane["inwestorzy"]:
        dane["ostrzezenia"].append({"pole": "inwestor", "komunikat":
            "Nie znaleziono pewnej listy inwestorów. Uzupełnij ją ręcznie."})
    identyfikatory = [x.strip() for x in identyfikator.split(",") if x.strip()]
    if len(identyfikatory) > 1:
        drogowe = {nr for s in odczytane for nr in _dzialki(s["pola"].get("adres.dzialki_drogowe", ""))}
        dane["dzialki_do_wyboru"] = [{"identyfikator": x, "numer": x.rsplit(".", 1)[-1],
                                     "droga": x.rsplit(".", 1)[-1] in drogowe} for x in identyfikatory]
        dane["adres_inwestycji"]["nr_dzialki"] = ""
        dane["adres_inwestycji"]["identyfikator_dzialki"] = ""
        dane["ostrzezenia"].append({"pole": "adres_inwestycji", "komunikat":
            "Decyzja wymienia kilka działek. Wybierz poniżej te, które mają trafić do dokumentów; działki drogi sprawdź osobno."})
    return dane
