"""Wniosek EGiB o wypis lub wyrys z operatu ewidencyjnego (Dz.U. 2026 poz. 1068)."""
from __future__ import annotations

import datetime
import io
import re
from docx import Document

PRZEDMIOTY = {
    "wypis_grunty": "Wypis z rejestru gruntów",
    "wypis_grunty_wyrys": "Wypis z rejestru gruntów oraz wyrys z mapy ewidencyjnej",
    "wyrys": "Wyrys z mapy ewidencyjnej",
    "uproszczony": "Uproszczony wypis z rejestru gruntów",
    "bez_danych": "Wypis z rejestru gruntów bez danych osobowych",
    "kartoteka_budynkow": "Wypis z kartoteki budynków",
    "kartoteka_lokali": "Wypis z kartoteki lokali",
    "rejestr_budynkow": "Wypis z rejestru budynków",
    "rejestr_lokali": "Wypis z rejestru lokali",
    "wykaz_dzialek": "Wypis z wykazu działek ewidencyjnych",
    "wykaz_podmiotow": "Wypis z wykazu podmiotów",
}
UZASADNIENIA = {
    "wlasciciel": "jest właścicielem, osobą lub jednostką organizacyjną władającą gruntami, budynkami lub lokalami, których dotyczy wniosek",
    "zadania_publiczne": "jest organem administracji publicznej albo podmiotem realizującym zadania publiczne związane z gruntami, budynkami lub lokalami",
    "operator_sieci": "jest operatorem sieci telekomunikacyjnej",
    "operator_energetyczny": "jest operatorem systemu przesyłowego, dystrybucyjnego lub połączonego",
    "interes_prawny": "ma interes prawny w dostępie do danych objętych wnioskiem",
}
POSTAC = {"papierowa": "Postać papierowa", "elektroniczna": "Postać elektroniczna"}
ODBIOR = {
    "osobiscie": "Odbiór osobisty w siedzibie organu",
    "wysylka_naglowek": "Wysyłka pod adres jak w nagłówku",
    "wysylka_inny": "Wysyłka pod inny adres",
    "inny": "Inny sposób odbioru",
}
NUMER = re.compile(r"\d+(?:/\d+)?(?:,\s*\d+(?:/\d+)?)*")


def domyslne(dane, dzisiaj):
    osoby = dane.get("inwestorzy", [])
    pierwszy = osoby[0] if osoby else {}
    linie = [", ".join(i.get("imie_nazwisko", "") for i in osoby)]
    ulica = " ".join(x for x in (pierwszy.get("ulica", ""), pierwszy.get("nr_domu", "")) if x)
    if not pierwszy.get("ulica") and pierwszy.get("nr_domu"):
        ulica = f"{pierwszy.get('miejscowosc', '')} {pierwszy['nr_domu']}".strip()
    if pierwszy.get("nr_lokalu"):
        ulica += "/" + pierwszy["nr_lokalu"]
    linie += [ulica, " ".join(x for x in (pierwszy.get("kod_pocztowy", ""), pierwszy.get("miejscowosc", "")) if x)]
    nier = dane.get("nieruchomosc", {})
    adr = dane.get("adres_inwestycji", {})
    return {
        "wnioskodawca": "\n".join(x for x in linie if x), "data": dzisiaj,
        "pesel_regon": "", "kontakt": "", "oznaczenie": "",
        "powiat": "nowotarski", "gmina": nier.get("gmina", ""),
        "obreb": adr.get("miejscowosc", ""), "jednostka": "",
        "dzialki": adr.get("nr_dzialki", ""), "budynki": "", "lokale": "", "kw": "",
        "adres_nieruchomosci": " ".join(x for x in (adr.get("ulica", ""), adr.get("nr_domu", ""), adr.get("miejscowosc", "")) if x),
        "uzasadnienie_akt": "", "uzasadnienie_okolicznosci": "",
        "kontakt_osoba": pierwszy.get("imie_nazwisko", ""), "email": pierwszy.get("email", ""),
        "telefon": "", "inny_adres": "", "uwagi": "",
    }


def odczytaj(form, dane):
    pola = {"wnioskodawca": 500, "data": 10, "pesel_regon": 20, "kontakt": 254, "oznaczenie": 100,
            "powiat": 100, "gmina": 150, "obreb": 150, "jednostka": 100, "dzialki": 500,
            "budynki": 300, "lokale": 300, "kw": 100, "adres_nieruchomosci": 300,
            "uzasadnienie_akt": 500, "uzasadnienie_okolicznosci": 500, "kontakt_osoba": 200,
            "email": 254, "telefon": 40, "inny_adres": 300, "uwagi": 1000}
    wynik = {}
    for key, limit in pola.items():
        values = form.getlist("egibw-" + key)
        value = form.get("egibw-" + key, "").strip()
        if len(values) > 1 or len(value) > limit or any(ord(c) < 32 and c not in "\r\n\t" for c in value):
            raise ValueError("EGiB — wypis/wyrys: sprawdź długość lub zawartość pól.")
        wynik[key] = value
    wynik["przedmioty"] = _wybory(form, "przedmiot", PRZEDMIOTY, wymagane=True)
    wynik["uzasadnienia"] = _wybory(form, "uzasadnienie", UZASADNIENIA)
    wynik["postacie"] = _wybory(form, "postac", POSTAC)
    wynik["odbior"] = _wybory(form, "odbior", ODBIOR)
    if not wynik["wnioskodawca"]:
        raise ValueError("EGiB — wypis/wyrys: podaj imię i nazwisko lub nazwę oraz adres wnioskodawcy.")
    if not wynik["gmina"] or not wynik["obreb"] or not wynik["dzialki"]:
        raise ValueError("EGiB — wypis/wyrys: podaj gminę, obręb ewidencyjny i numery działek.")
    if not NUMER.fullmatch(wynik["dzialki"]):
        raise ValueError("EGiB — wypis/wyrys: sprawdź numery działek, np. 123/4, 125.")
    działki = [x.strip() for x in wynik["dzialki"].split(",")]
    if len(działki) != len(set(działki)):
        raise ValueError("EGiB — wypis/wyrys: usuń powtórzone numery działek.")
    try:
        date = datetime.datetime.strptime(wynik["data"], "%d.%m.%Y").date()
        if date.strftime("%d.%m.%Y") != wynik["data"]: raise ValueError()
    except ValueError:
        raise ValueError("EGiB — wypis/wyrys: podaj prawidłową datę w formacie DD.MM.RRRR.")
    if wynik["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", wynik["email"]):
        raise ValueError("EGiB — wypis/wyrys: podaj poprawny adres e-mail.")
    if wynik["telefon"] and (not re.fullmatch(r"[+\d\s()\-]+", wynik["telefon"]) or not 7 <= len(re.sub(r"\D", "", wynik["telefon"])) <= 15):
        raise ValueError("EGiB — wypis/wyrys: sprawdź numer telefonu.")
    if not wynik["postacie"] or not wynik["odbior"]:
        raise ValueError("EGiB — wypis/wyrys: wybierz postać dokumentów i sposób udostępnienia.")
    dane_osobowe = {"wypis_grunty", "wypis_grunty_wyrys", "uproszczony", "kartoteka_budynkow", "kartoteka_lokali", "rejestr_budynkow", "rejestr_lokali", "wykaz_podmiotow"}
    if dane_osobowe.intersection(wynik["przedmioty"]) and not wynik["uzasadnienia"]:
        raise ValueError("EGiB — wypis/wyrys: wskaż podstawę dostępu do danych podmiotów.")
    if "interes_prawny" in wynik["uzasadnienia"] and (not wynik["uzasadnienie_akt"] or not wynik["uzasadnienie_okolicznosci"]):
        raise ValueError("EGiB — wypis/wyrys: opisz akt prawny i okoliczności interesu prawnego.")
    if "wysylka_inny" in wynik["odbior"] and not wynik["inny_adres"]:
        raise ValueError("EGiB — wypis/wyrys: podaj adres wysyłki.")
    return wynik


def _wybory(form, klucz, slownik, wymagane=False):
    wartosci = form.getlist("egibw-" + klucz)
    if len(wartosci) != len(set(wartosci)) or any(w not in slownik for w in wartosci):
        raise ValueError("EGiB — wypis/wyrys: niepoprawny wybór opcji formularza.")
    if wymagane and not wartosci:
        raise ValueError("EGiB — wypis/wyrys: zaznacz przedmiot wniosku.")
    return wartosci


def kontekst(dane):
    return dane["egib_wypis"]


def zastosuj(content, values):
    doc = Document(io.BytesIO(content))
    paragraphs = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
                for nested in cell.tables:
                    for nested_row in nested.rows:
                        for nested_cell in nested_row.cells:
                            paragraphs.extend(nested_cell.paragraphs)
    for p in paragraphs:
        for r in p.runs:
            name = r.style.name
            if name.startswith("EGIBW_PRZEDMIOT_"):
                r.text = "☒" if name.removeprefix("EGIBW_PRZEDMIOT_").lower() in values["przedmioty"] else "☐"
            elif name.startswith("EGIBW_UZASADNIENIE_"):
                r.text = "☒" if name.removeprefix("EGIBW_UZASADNIENIE_").lower() in values["uzasadnienia"] else "☐"
            elif name.startswith("EGIBW_POSTAC_"):
                r.text = "☒" if name.removeprefix("EGIBW_POSTAC_").lower() in values["postacie"] else "☐"
            elif name.startswith("EGIBW_ODBIOR_"):
                r.text = "☒" if name.removeprefix("EGIBW_ODBIOR_").lower() in values["odbior"] else "☐"
    out = io.BytesIO(); doc.save(out); return out.getvalue()
