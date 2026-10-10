"""Wypełnianie szablonów biura (docxtpl) danymi z formularza.

Dane wejściowe mają postać słownika zwracanego przez parser_obiegowki.odczytaj_obiegowke()
(po ewentualnych poprawkach w formularzu) oraz pól:
    data_pelnomocnictwa (str), upowazniony_w_pb5 (bool),
    nieruchomosc{wojewodztwo, powiat, gmina} – jednostki działki (z TERYT, poprawialne),
    inwestorzy[i]{wojewodztwo, powiat, gmina} – jednostki adresu inwestora.
"""
from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from pathlib import Path

from docxtpl import DocxTemplate

from app.konfiguracja import BRAK_LOKALU, PELNOMOCNIK, PUSTE_POLE
from app import dokumenty, zakonczenie_dokumenty

SZABLONY = Path(__file__).resolve().parent.parent / "szablony"
SZABLON_PELNOMOCNICTWA = SZABLONY / "pelnomocnictwo.docx"
SZABLON_PB5 = SZABLONY / "pb5_oswiadczenie.docx"
LINIA_PODPISU = "……………………………………"


def _albo_kropki(slownik: dict) -> dict:
    return {k: (str(v).strip() if str(v or "").strip() else PUSTE_POLE) for k, v in slownik.items()}


def _bez_prefiksu_ulicy(ulica: str) -> str:
    """W PB-5 pole nazywa się już 'Ulica:', więc 'ul. Sądecka' → 'Sądecka'."""
    return re.sub(r"^ul\.?\s+", "", ulica or "", flags=re.IGNORECASE)


def _adres_jednolinijkowy(o: dict) -> str:
    ulica = " ".join(x for x in [o.get("ulica", ""), o.get("nr_domu", "")] if x)
    if o.get("nr_lokalu"):
        ulica += f"/{o['nr_lokalu']}"
    miasto = " ".join(x for x in [o.get("kod_pocztowy", ""), o.get("poczta") or o.get("miejscowosc", "")] if x)
    # Adres wiejski bez ulicy: "Pcim 123, 32-432 Pcim"
    if not o.get("ulica") and o.get("nr_domu"):
        ulica = f"{o.get('miejscowosc', '')} {o['nr_domu']}".strip()
    return ", ".join(x for x in [ulica, miasto] if x)


def _wylicz(nazwy: list[str]) -> str:
    return nazwy[0] if len(nazwy) == 1 else ", ".join(nazwy[:-1]) + " i " + nazwy[-1]


def kontekst_pelnomocnictwa(dane: dict) -> dict:
    inwestorzy = dane["inwestorzy"]
    wielu = len(inwestorzy) > 1
    same_kobiety = all(i.get("plec") == "K" for i in inwestorzy)
    adresy = [_adres_jednolinijkowy(i) for i in inwestorzy]
    if len(set(adresy)) <= 1:
        adres_mocodawcy = adresy[0] if adresy else ""
    else:
        adres_mocodawcy = "; ".join(f"{i['imie_nazwisko']} – {a}" for i, a in zip(inwestorzy, adresy))

    if wielu:
        zamieszkaly = "zamieszkałe" if same_kobiety else "zamieszkali"
    else:
        zamieszkaly = "zamieszkała" if inwestorzy and inwestorzy[0].get("plec") == "K" else "zamieszkały"

    adres = dane["adres_inwestycji"]
    ulica = " ".join(x for x in [adres.get("ulica", ""), adres.get("nr_domu", "")] if x)
    dzialka = f"dz. ew. {adres['nr_dzialki']}" if adres.get("nr_dzialki") else ""
    lokalizacja = " ".join(x for x in [adres.get("miejscowosc", ""), ulica, dzialka] if x)

    return {
        "data": dane.get("data_pelnomocnictwa", ""),
        "ja": "My" if wielu else "Ja",
        "mocodawcy": _wylicz([i["imie_nazwisko"] for i in inwestorzy]) if inwestorzy else PUSTE_POLE,
        "zamieszkaly": zamieszkaly,
        "adres_mocodawcy": adres_mocodawcy or PUSTE_POLE,
        "udzielam": "udzielamy" if wielu else "udzielam",
        "mnie": "nas" if wielu else "mnie",
        "inwestora": "inwestorów" if wielu else "inwestora",
        "moim": "naszym" if wielu else "moim",
        "upowazniam": "Upoważniamy" if wielu else "Upoważniam",
        "nazwa_inwestycji": dane.get("nazwa_inwestycji", "") or PUSTE_POLE,
        "lokalizacja": lokalizacja or PUSTE_POLE,
        # docxtpl zamienia "\n" na złamanie linii w Wordzie.
        "podpisy": "\n\n\n".join(f"{LINIA_PODPISU}\n{i['imie_nazwisko']}" for i in inwestorzy)
                   if wielu else f"{LINIA_PODPISU}\nPodpis",
    }


def _nr_lokalu(osoba: dict) -> str:
    """Kreska, gdy adres jest podany, ale bez lokalu; puste (→ kropki), gdy adresu brak."""
    if (osoba.get("nr_lokalu") or "").strip():
        return osoba["nr_lokalu"]
    ma_adres = (osoba.get("ulica") or "").strip() or (osoba.get("nr_domu") or "").strip()
    return BRAK_LOKALU if ma_adres else ""


def kontekst_pb5(dane: dict, inwestor: dict) -> dict:
    adres = dane["adres_inwestycji"]
    nieruchomosc = dane.get("nieruchomosc", {})
    upowazniony = PELNOMOCNIK if dane.get("upowazniony_w_pb5") else {k: "" for k in PELNOMOCNIK}
    return {
        "inwestor": _albo_kropki({
            "imie_nazwisko": inwestor.get("imie_nazwisko"),
            "kraj": "Polska",
            "wojewodztwo": inwestor.get("wojewodztwo"),
            "powiat": inwestor.get("powiat"),
            "gmina": inwestor.get("gmina"),
            "ulica": _bez_prefiksu_ulicy(inwestor.get("ulica")),
            "nr_domu": inwestor.get("nr_domu"),
            "nr_lokalu": _nr_lokalu(inwestor),
            "miejscowosc": inwestor.get("miejscowosc"),
            "kod_pocztowy": inwestor.get("kod_pocztowy"),
            "poczta": inwestor.get("poczta"),
        }),
        "upowazniony": _albo_kropki(upowazniony),
        "nieruchomosc": _albo_kropki({
            "wojewodztwo": nieruchomosc.get("wojewodztwo"),
            "powiat": nieruchomosc.get("powiat"),
            "gmina": nieruchomosc.get("gmina"),
            "ulica": _bez_prefiksu_ulicy(adres.get("ulica")),
            "nr_domu": adres.get("nr_domu"),
            "miejscowosc": adres.get("miejscowosc"),
            "kod_pocztowy": adres.get("kod_pocztowy"),
            "identyfikator_dzialki": adres.get("identyfikator_dzialki"),
        }),
    }


def _wypelnij(szablon: Path, kontekst: dict) -> bytes:
    dokument = DocxTemplate(szablon)
    dokument.render(kontekst, autoescape=True)
    bufor = io.BytesIO()
    dokument.save(bufor)
    return bufor.getvalue()


def _do_nazwy_pliku(tekst: str) -> str:
    tekst = tekst.replace("ł", "l").replace("Ł", "L")
    ascii_ = unicodedata.normalize("NFKD", tekst).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", ascii_).strip("_") or "dokument"


def _nazwisko(imie_nazwisko: str) -> str:
    czesci = imie_nazwisko.split()
    return czesci[-1] if czesci else ""


def generuj_dokumenty(dane: dict) -> dict[str, bytes]:
    """Zwraca tylko wybrane dokumenty; PB-5 osobno dla każdego inwestora."""
    inwestorzy = dane["inwestorzy"]
    wybrane = dane.get("dokumenty", dokumenty.DOMYSLNE)
    nazwiska = list(dict.fromkeys(_nazwisko(i["imie_nazwisko"]) for i in inwestorzy if i["imie_nazwisko"]))
    sufiks = _do_nazwy_pliku("_".join(nazwiska) or "inwestor")
    pliki = {}
    if "pelnomocnictwo" in wybrane:
        pliki[f"Pelnomocnictwo_{sufiks}.docx"] = _wypelnij(SZABLON_PELNOMOCNICTWA,
                                                             kontekst_pelnomocnictwa(dane))
    if "pb5" in wybrane:
        for nr, inwestor in enumerate(inwestorzy, start=1):
            czesci = inwestor["imie_nazwisko"].split()
            nazwa = "_".join(czesci[-1:] + czesci[:-1]) or f"inwestor_{nr}"
            plik = f"PB-5_{_do_nazwy_pliku(nazwa)}.docx"
            if plik in pliki:
                plik = plik.replace(".docx", f"_{nr}.docx")
            pliki[plik] = _wypelnij(SZABLON_PB5, kontekst_pb5(dane, inwestor))
    if "oswiadczenie" in wybrane:
        pliki[f"Oswiadczenie_kierownika_{sufiks}.docx"] = zakonczenie_dokumenty.oswiadczenie(dane)
    if "zawiadomienie" in wybrane:
        pliki[f"Zawiadomienie_o_zakonczeniu_{sufiks}.docx"] = zakonczenie_dokumenty.zawiadomienie(dane)
    return pliki


def spakuj(pliki: dict[str, bytes]) -> bytes:
    bufor = io.BytesIO()
    with zipfile.ZipFile(bufor, "w", zipfile.ZIP_DEFLATED) as z:
        for nazwa, zawartosc in pliki.items():
            z.writestr(nazwa, zawartosc)
    return bufor.getvalue()
