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
from docx import Document
from docx.shared import Pt

from app.konfiguracja import BRAK_LOKALU, PELNOMOCNIK, PUSTE_POLE
from app import dokumenty, dziennik, ewidencja, egib_wypis, formularz_p, formatowanie, os616, pelnomocnictwo_egib, zakonczenie_dokumenty, pb1, pb2, pb2a, pb7, pb9

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
            "identyfikator_dzialki": (adres.get("identyfikator_dzialki") or "").split(",")[0].strip(),
        }),
    }


def kontekst_pb2(dane: dict, inwestor: dict, nr: int) -> dict:
    """PB-2: jeden formularz na inwestora, z ręcznie uzupełnianymi opcjami pełnomocnika."""
    adres=dane.get("adres_inwestycji",{}); nier=dane.get("nieruchomosc",{}); dodat=dane.get("pb2",{}).get("dodatkowe",{}).get(str(nr),{})
    def puste(obj, klucz): return obj.get(klucz) or "……………………"
    kor=dodat.get("korespondencja",{}); proxy=dodat.get("proxy",{}) if dodat.get("typ_pelnomocnika") else {}
    inwestor_pb={"imie_nazwisko":inwestor.get("imie_nazwisko"),"kraj":"Polska","wojewodztwo":inwestor.get("wojewodztwo"),"powiat":inwestor.get("powiat"),"gmina":inwestor.get("gmina"),"ulica":_bez_prefiksu_ulicy(inwestor.get("ulica")),"nr_domu":inwestor.get("nr_domu"),"nr_lokalu":inwestor.get("nr_lokalu"),"miejscowosc":inwestor.get("miejscowosc"),"kod_pocztowy":inwestor.get("kod_pocztowy")}
    inwestor_pb=_albo_kropki(inwestor_pb)
    def adres_wartosci(a): return {k:puste(a,k) for k in pb2.ADRES}
    return {"inwestor":inwestor_pb,"email":puste(dodat,"email"),"telefon":puste(dodat,"telefon"),"korespondencja":adres_wartosci(kor),"proxy":adres_wartosci(proxy),"proxy_nazwa":puste(dodat,"proxy_nazwa") if dodat.get("typ_pelnomocnika") else "……………………","roboty":dane.get("pb2",{}).get("roboty") or "……………………………………","termin":dane.get("pb2",{}).get("termin") or "……………………",
      "nieruchomosc":_albo_kropki({"wojewodztwo":nier.get("wojewodztwo"),"powiat":nier.get("powiat"),"gmina":nier.get("gmina"),"ulica":_bez_prefiksu_ulicy(adres.get("ulica")),"nr_domu":adres.get("nr_domu"),"miejscowosc":adres.get("miejscowosc"),"kod_pocztowy":adres.get("kod_pocztowy"),"identyfikator_dzialki":(adres.get("identyfikator_dzialki") or "").split(",")[0].strip()})}


def kontekst_pb2a(dane: dict, inwestor: dict, nr: int) -> dict:
    """PB-2a: jedno zgłoszenie na inwestora; adres korespondencyjny i pełnomocnik są opcjonalne."""
    adres=dane.get("adres_inwestycji",{});nier=dane.get("nieruchomosc",{});dodat=dane.get("pb2a",{}).get("dodatkowe",{}).get(str(nr),{})
    def puste(obj,k): return obj.get(k) or "……………………"
    kor=dodat.get("korespondencja",{});proxy=dodat.get("proxy",{}) if dodat.get("typ_pelnomocnika") else {}
    inwestor_pb=_albo_kropki({"imie_nazwisko":inwestor.get("imie_nazwisko"),"kraj":"Polska","wojewodztwo":inwestor.get("wojewodztwo"),"powiat":inwestor.get("powiat"),"gmina":inwestor.get("gmina"),"ulica":_bez_prefiksu_ulicy(inwestor.get("ulica")),"nr_domu":inwestor.get("nr_domu"),"nr_lokalu":_nr_lokalu(inwestor),"miejscowosc":inwestor.get("miejscowosc"),"kod_pocztowy":inwestor.get("kod_pocztowy")})
    return {"inwestor":inwestor_pb,"email":puste(dodat,"email"),"telefon":puste(dodat,"telefon"),"korespondencja":{k:puste(kor,k) for k in pb2a.ADRES},"proxy":{k:puste(proxy,k) for k in pb2a.ADRES},"proxy_nazwa":puste(dodat,"proxy_nazwa") if dodat.get("typ_pelnomocnika") else "……………………","termin":dane.get("pb2a",{}).get("termin") or "……………………",
      "rodzaje":dane.get("pb2a",{}).get("rodzaje",[]),"nieruchomosc":_albo_kropki({"wojewodztwo":nier.get("wojewodztwo"),"powiat":nier.get("powiat"),"gmina":nier.get("gmina"),"ulica":_bez_prefiksu_ulicy(adres.get("ulica")),"nr_domu":adres.get("nr_domu"),"miejscowosc":adres.get("miejscowosc"),"kod_pocztowy":adres.get("kod_pocztowy"),"identyfikator_dzialki":(adres.get("identyfikator_dzialki") or "").split(",")[0].strip()})}


def kontekst_pb7(dane: dict, inwestor: dict, nr: int) -> dict:
    """PB-7: dane jednej osoby składającej wniosek o zmianę pozwolenia."""
    dodat = dane.get("pb7", {}).get("dodatkowe", {}).get(str(nr), {})
    def puste(obj, klucz): return obj.get(klucz) or "……………………"
    kor = dodat.get("korespondencja", {})
    proxy = dodat.get("proxy", {}) if dodat.get("typ_pelnomocnika") else {}
    inwestor_pb = _albo_kropki({
        "imie_nazwisko": inwestor.get("imie_nazwisko"), "kraj": "Polska",
        "wojewodztwo": inwestor.get("wojewodztwo"), "powiat": inwestor.get("powiat"),
        "gmina": inwestor.get("gmina"), "ulica": _bez_prefiksu_ulicy(inwestor.get("ulica")),
        "nr_domu": inwestor.get("nr_domu"), "nr_lokalu": _nr_lokalu(inwestor),
        "miejscowosc": inwestor.get("miejscowosc"), "kod_pocztowy": inwestor.get("kod_pocztowy"),
    })
    return {
        "organ": puste(dodat, "organ"), "inwestor": inwestor_pb,
        "email": puste(dodat, "email"), "telefon": puste(dodat, "telefon"),
        "korespondencja": {k: puste(kor, k) for k in pb7.ADRES},
        "proxy": {k: puste(proxy, k) for k in pb7.ADRES},
        "proxy_nazwa": puste(dodat, "proxy_nazwa") if dodat.get("typ_pelnomocnika") else "……………………",
        "data_decyzji": puste(dodat, "data_decyzji"), "nr_decyzji": puste(dodat, "nr_decyzji"),
        "znak_sprawy": puste(dodat, "znak_sprawy"), "nazwa_zamierzenia": puste(dodat, "nazwa_zamierzenia"),
    }


def kontekst_pb9(dane: dict, inwestor: dict, nr: int) -> dict:
    """PB-9: dane nowego inwestora pochodzą z obiegówki; resztę dopisuje użytkownik."""
    dodat = dane.get("pb9", {}).get("dodatkowe", {}).get(str(nr), {})
    def puste(obj, klucz): return obj.get(klucz) or "……………………"
    kor = dodat.get("korespondencja", {})
    proxy = dodat.get("proxy", {}) if dodat.get("typ_pelnomocnika") else {}
    inwestor_pb = _albo_kropki({
        "imie_nazwisko": inwestor.get("imie_nazwisko"), "kraj": "Polska",
        "wojewodztwo": inwestor.get("wojewodztwo"), "powiat": inwestor.get("powiat"),
        "gmina": inwestor.get("gmina"), "ulica": _bez_prefiksu_ulicy(inwestor.get("ulica")),
        "nr_domu": inwestor.get("nr_domu"), "nr_lokalu": _nr_lokalu(inwestor),
        "miejscowosc": inwestor.get("miejscowosc"), "kod_pocztowy": inwestor.get("kod_pocztowy"),
    })
    return {
        "inwestor": inwestor_pb, "email": puste(dodat, "email"), "telefon": puste(dodat, "telefon"),
        "korespondencja": {k: puste(kor, k) for k in pb9.ADRES},
        "proxy": {k: puste(proxy, k) for k in pb9.ADRES},
        "proxy_nazwa": puste(dodat, "proxy_nazwa") if dodat.get("typ_pelnomocnika") else "……………………",
        "dotychczasowy_inwestor": puste(dodat, "dotychczasowy_inwestor"),
        "data_decyzji": puste(dodat, "data_decyzji"), "nr_decyzji": puste(dodat, "nr_decyzji"),
        "znak_sprawy": puste(dodat, "znak_sprawy"), "nazwa_zamierzenia": puste(dodat, "nazwa_zamierzenia"),
    }


def kontekst_pb1(dane: dict, inwestor: dict, nr: int) -> dict:
    """PB-1: dane osobowe i działki pobieramy z obiegówki, resztę z formularza."""
    dodat = dane.get("pb1", {}).get("dodatkowe", {}).get(str(nr), {})
    def puste(obj, klucz): return obj.get(klucz) or "……………………"
    kor = dodat.get("korespondencja", {})
    proxy = dodat.get("proxy", {}) if dodat.get("typ_pelnomocnika") else {}
    adres = dane.get("adres_inwestycji", {})
    nier = dane.get("nieruchomosc", {})
    inwestor_pb = _albo_kropki({
        "imie_nazwisko": inwestor.get("imie_nazwisko"), "kraj": "Polska",
        "wojewodztwo": inwestor.get("wojewodztwo"), "powiat": inwestor.get("powiat"),
        "gmina": inwestor.get("gmina"), "ulica": _bez_prefiksu_ulicy(inwestor.get("ulica")),
        "nr_domu": inwestor.get("nr_domu"), "nr_lokalu": _nr_lokalu(inwestor),
        "miejscowosc": inwestor.get("miejscowosc"), "kod_pocztowy": inwestor.get("kod_pocztowy"),
    })
    return {
        "inwestor": inwestor_pb, "email": puste(dodat, "email"), "telefon": puste(dodat, "telefon"),
        "korespondencja": {k: puste(kor, k) for k in pb1.ADRES},
        "proxy": {k: puste(proxy, k) for k in pb1.ADRES},
        "proxy_nazwa": puste(dodat, "proxy_nazwa") if dodat.get("typ_pelnomocnika") else "……………………",
        "zal_opis": puste(dodat, "zal_opis"),
        "nazwa": puste(dane.get("pb1", {}), "nazwa"),
        "rodzaje": dane.get("pb1", {}).get("rodzaje", []),
        "nieruchomosc": _albo_kropki({
            "wojewodztwo": nier.get("wojewodztwo"), "powiat": nier.get("powiat"),
            "gmina": nier.get("gmina"), "ulica": _bez_prefiksu_ulicy(adres.get("ulica")),
            "nr_domu": adres.get("nr_domu"), "miejscowosc": adres.get("miejscowosc"),
            "kod_pocztowy": adres.get("kod_pocztowy"),
            "identyfikator_dzialki": adres.get("identyfikator_dzialki"),
        }),
    }


def _wypelnij(szablon: Path, kontekst: dict, styl: dict) -> bytes:
    wzor = Document(szablon)
    formatowanie.przygotuj_szablon(wzor, kontekst, styl)
    wejscie = io.BytesIO()
    wzor.save(wejscie)
    wejscie.seek(0)
    dokument = DocxTemplate(wejscie)
    dokument.render(kontekst, autoescape=True)
    bufor = io.BytesIO()
    dokument.save(bufor)
    return bufor.getvalue()


def _strony_kolejnych_dzialek(wypelniony: bytes, dane: dict, inwestor: dict) -> bytes:
    """Dodatkowe nieruchomości PB-5 na osobnych stronach, zgodnie z objaśnieniem wzoru."""
    wszystkie = [x.strip() for x in (dane["adres_inwestycji"].get("identyfikator_dzialki") or "").split(",") if x.strip()]
    if len(wszystkie) < 2:
        return wypelniony
    dokument = Document(io.BytesIO(wypelniony))
    styl = formatowanie.z_danych(dane)
    for akapit in dokument.paragraphs:
        if "Liczba stron zawierających dane o kolejnych nieruchomościach" in akapit.text:
            miejsce = re.search(r"…+", akapit.text)
            if miejsce:
                formatowanie.zastap(akapit, miejsce.start(), miejsce.end(), str(len(wszystkie) - 1), styl)
    adres = dane["adres_inwestycji"]
    jednostka = dane.get("nieruchomosc", {})
    for numer, identyfikator in enumerate(wszystkie[1:], start=1):
        dokument.add_page_break()
        tytul = dokument.add_paragraph()
        tytul.add_run("PB-5 — dane kolejnej nieruchomości").bold = True
        tytul.runs[0].font.size = Pt(12)
        opis = dokument.add_paragraph("Załącznik ")
        formatowanie.zastosuj(opis.add_run(str(numer)), styl)
        opis.add_run(" z ")
        formatowanie.zastosuj(opis.add_run(str(len(wszystkie) - 1)), styl)
        opis.add_run(" do oświadczenia inwestora: ")
        formatowanie.zastosuj(opis.add_run(inwestor.get("imie_nazwisko", "")), styl)
        tabela = dokument.add_table(rows=0, cols=2)
        for etykieta, wartosc in (
            ("Województwo", jednostka.get("wojewodztwo", "")),
            ("Powiat", jednostka.get("powiat", "")),
            ("Gmina", jednostka.get("gmina", "")),
            ("Miejscowość", adres.get("miejscowosc", "")),
            ("Ulica", adres.get("ulica", "")),
            ("Nr domu", adres.get("nr_domu", "")),
            ("Kod pocztowy", adres.get("kod_pocztowy", "")),
            ("Identyfikator działki ewidencyjnej", identyfikator),
        ):
            komorki = tabela.add_row().cells
            komorki[0].text = etykieta
            komorki[1].text = wartosc or PUSTE_POLE
            if wartosc:
                formatowanie.zastosuj(komorki[1].paragraphs[0].runs[0], styl)
        dokument.add_paragraph("Data i podpis inwestora albo osoby upoważnionej: ................................................")
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
    styl = formatowanie.z_danych(dane)
    wybrane = dane.get("dokumenty", dokumenty.DOMYSLNE)
    nazwiska = list(dict.fromkeys(_nazwisko(i["imie_nazwisko"]) for i in inwestorzy if i["imie_nazwisko"]))
    sufiks = _do_nazwy_pliku("_".join(nazwiska) or "inwestor")
    pliki = {}
    if "pelnomocnictwo" in wybrane:
        pliki[f"Pelnomocnictwo_{sufiks}.docx"] = _wypelnij(SZABLON_PELNOMOCNICTWA,
                                                             kontekst_pelnomocnictwa(dane), styl)
    if "pb5" in wybrane:
        for nr, inwestor in enumerate(inwestorzy, start=1):
            czesci = inwestor["imie_nazwisko"].split()
            nazwa = "_".join(czesci[-1:] + czesci[:-1]) or f"inwestor_{nr}"
            plik = f"PB-5_{_do_nazwy_pliku(nazwa)}.docx"
            if plik in pliki:
                plik = plik.replace(".docx", f"_{nr}.docx")
            pliki[plik] = _strony_kolejnych_dzialek(_wypelnij(SZABLON_PB5, kontekst_pb5(dane, inwestor), styl),
                                                     dane, inwestor)
    if "pb2" in wybrane:
        for nr, inwestor in enumerate(inwestorzy):
            ctx=kontekst_pb2(dane,inwestor,nr)
            wypelniony=_wypelnij(SZABLONY / "pb2_zgloszenie.docx",ctx,styl)
            dodat=dane.get("pb2",{}).get("dodatkowe",{}).get(str(nr),{})
            plik=f"PB-2_{_do_nazwy_pliku(inwestor.get('imie_nazwisko','Inwestor'))}.docx"
            if plik in pliki: plik=plik.replace('.docx',f'_{nr+1}.docx')
            pliki[plik]=pb2.zastosuj(wypelniony,dodat)
    if "pb2a" in wybrane:
        for nr,inwestor in enumerate(inwestorzy):
            ctx=kontekst_pb2a(dane,inwestor,nr)
            wypelniony=_wypelnij(SZABLONY/"pb2a_zgloszenie.docx",ctx,styl)
            dodat=dane.get("pb2a",{}).get("dodatkowe",{}).get(str(nr),{}) | {"rodzaje":dane.get("pb2a",{}).get("rodzaje",[])}
            plik=f"PB-2a_{_do_nazwy_pliku(inwestor.get('imie_nazwisko','Inwestor'))}.docx"
            if plik in pliki:plik=plik.replace('.docx',f'_{nr+1}.docx')
            pliki[plik]=pb2a.zastosuj(wypelniony,dodat)
    if "pb7" in wybrane:
        for nr, inwestor in enumerate(inwestorzy):
            ctx = kontekst_pb7(dane, inwestor, nr)
            wypelniony = _wypelnij(SZABLONY / "pb7_wniosek.docx", ctx, styl)
            dodat = dane.get("pb7", {}).get("dodatkowe", {}).get(str(nr), {})
            plik = f"PB-7_{_do_nazwy_pliku(inwestor.get('imie_nazwisko', 'Inwestor'))}.docx"
            if plik in pliki:
                plik = plik.replace(".docx", f"_{nr+1}.docx")
            pliki[plik] = pb7.zastosuj(wypelniony, dodat)
    if "pb9" in wybrane:
        for nr, inwestor in enumerate(inwestorzy):
            ctx = kontekst_pb9(dane, inwestor, nr)
            wypelniony = _wypelnij(SZABLONY / "pb9_wniosek.docx", ctx, styl)
            dodat = dane.get("pb9", {}).get("dodatkowe", {}).get(str(nr), {})
            plik = f"PB-9_{_do_nazwy_pliku(inwestor.get('imie_nazwisko', 'Nowy_inwestor'))}.docx"
            if plik in pliki:
                plik = plik.replace(".docx", f"_{nr+1}.docx")
            pliki[plik] = pb9.zastosuj(wypelniony, dodat)
    if "pb1" in wybrane:
        for nr, inwestor in enumerate(inwestorzy):
            ctx = kontekst_pb1(dane, inwestor, nr)
            wypelniony = _wypelnij(SZABLONY / "pb1_wniosek.docx", ctx, styl)
            dodat = dane.get("pb1", {}).get("dodatkowe", {}).get(str(nr), {}) | {"rodzaje": dane["pb1"]["rodzaje"]}
            plik = f"PB-1_{_do_nazwy_pliku(inwestor.get('imie_nazwisko', 'Inwestor'))}.docx"
            if plik in pliki: plik = plik.replace(".docx", f"_{nr+1}.docx")
            pliki[plik] = pb1.zastosuj(wypelniony, dodat)
    if "os616" in wybrane:
        wypelniony = _wypelnij(SZABLONY / "os616_zaswiadczenie.docx", os616.kontekst(dane), styl)
        pliki[f"OS-6165_Zaswiadczenie_UPUL_{sufiks}.docx"] = os616.zastosuj(wypelniony, dane["os616"])
    if "egib_wypis" in wybrane:
        wypelniony = _wypelnij(SZABLONY / "egib_wypis_wyrys.docx", egib_wypis.kontekst(dane), styl)
        pliki[f"EGiB_Wypis_Wyrys_{sufiks}.docx"] = egib_wypis.zastosuj(wypelniony, dane["egib_wypis"])
    if "formularz_p" in wybrane:
        wypelniony = _wypelnij(SZABLONY / "formularz_p.docx", formularz_p.kontekst(dane), styl)
        pliki[f"Formularz_P_PZGiK_{sufiks}.docx"] = formularz_p.zastosuj(wypelniony, dane["formularz_p"])
    if "oswiadczenie" in wybrane:
        pliki[f"Oswiadczenie_kierownika_{sufiks}.docx"] = zakonczenie_dokumenty.oswiadczenie(dane)
    if "zawiadomienie" in wybrane:
        pliki[f"Zawiadomienie_o_zakonczeniu_{sufiks}.docx"] = zakonczenie_dokumenty.zawiadomienie(dane)
    if "ba4" in wybrane:
        wypelniony = _wypelnij(SZABLONY / "ba4_dziennik.docx", dziennik.kontekst(dane), styl)
        pliki[f"BA-4_Wniosek_o_dziennik_{sufiks}.docx"] = dziennik.zastosuj_warianty(wypelniony, dane.get("ba4", {}))
    if "egib" in wybrane:
        wypelniony = _wypelnij(SZABLONY / "egib_zmiany.docx", ewidencja.kontekst(dane), styl)
        pliki[f"EGiB_Zgloszenie_zmian_{sufiks}.docx"] = ewidencja.zastosuj_warianty(wypelniony, dane.get("egib", {}))
    if "pelnomocnictwo_egib" in wybrane:
        wypelniony = _wypelnij(SZABLONY / "pelnomocnictwo_egib.docx", pelnomocnictwo_egib.kontekst(dane), styl)
        pliki[f"Pelnomocnictwo_EGiB_{sufiks}.docx"] = pelnomocnictwo_egib.zastosuj(wypelniony, dane["pelnomocnictwo_egib"])
    return pliki


def spakuj(pliki: dict[str, bytes]) -> bytes:
    bufor = io.BytesIO()
    with zipfile.ZipFile(bufor, "w", zipfile.ZIP_DEFLATED) as z:
        for nazwa, zawartosc in pliki.items():
            z.writestr(nazwa, zawartosc)
    return bufor.getvalue()
