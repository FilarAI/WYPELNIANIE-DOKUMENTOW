"""Dane do nowotarskiego wniosku o zaświadczenie dotyczące UPUL (OŚ-6165)."""
from __future__ import annotations

import datetime
import io
import re
from docx import Document

ODBIORY = {
    "osobiscie_dzis": "Osobiście w dniu złożenia",
    "osobiscie_inny": "Osobiście w innym dniu",
    "poczta": "Przesyłka listowna",
}
DZIALKA = re.compile(r"\d+(?:/\d+)?")


def domyslne(dane, dzisiaj):
    osoba = (dane.get("inwestorzy") or [{}])[0]
    adres = dane.get("adres_inwestycji", {})
    ulica = " ".join(x for x in (osoba.get("ulica", ""), osoba.get("nr_domu", "")) if x)
    if osoba.get("nr_lokalu"):
        ulica += "/" + osoba["nr_lokalu"]
    wiersze = [osoba.get("imie_nazwisko", ""), ulica,
               " ".join(x for x in (osoba.get("kod_pocztowy", ""), osoba.get("miejscowosc", "")) if x)]
    return {
        "wnioskodawca": "\n".join(x for x in wiersze if x),
        "telefon": "",
        "data": dzisiaj,
        "dzialki": adres.get("nr_dzialki", ""),
        "miejscowosc": adres.get("miejscowosc", ""),
    }


def odczytaj(form, dane):
    wartosci = {}
    limity = {"wnioskodawca": 500, "telefon": 40, "data": 10, "dzialki": 500, "miejscowosc": 120}
    for nazwa, limit in limity.items():
        vals = form.getlist("os616-" + nazwa)
        tekst = form.get("os616-" + nazwa, "").strip()
        if len(vals) > 1 or len(tekst) > limit or any(ord(c) < 32 and c not in "\r\n\t" for c in tekst):
            raise ValueError("OŚ-6165: sprawdź długość lub zawartość pól wniosku.")
        wartosci[nazwa] = tekst
    if not wartosci["wnioskodawca"]:
        raise ValueError("OŚ-6165: podaj imię i nazwisko oraz adres wnioskodawcy.")
    if not wartosci["dzialki"]:
        raise ValueError("OŚ-6165: podaj numery działek ewidencyjnych.")
    lista = re.split(r"[,;]\s*", wartosci["dzialki"])
    if any(not DZIALKA.fullmatch(x.strip()) for x in lista) or len(set(x.strip() for x in lista)) != len(lista):
        raise ValueError("OŚ-6165: podaj numery działek bez powtórzeń, np. 123/4, 125.")
    if not wartosci["miejscowosc"]:
        raise ValueError("OŚ-6165: podaj miejscowość położenia działki.")
    try:
        parsed = datetime.datetime.strptime(wartosci["data"], "%d.%m.%Y").date()
        if parsed.strftime("%d.%m.%Y") != wartosci["data"]:
            raise ValueError()
    except ValueError:
        raise ValueError("OŚ-6165: podaj prawidłową datę w formacie DD.MM.RRRR.")
    if wartosci["telefon"] and (not re.fullmatch(r"[+\d\s()\-]+", wartosci["telefon"]) or not 7 <= len(re.sub(r"\D", "", wartosci["telefon"])) <= 15):
        raise ValueError("OŚ-6165: sprawdź numer telefonu.")
    odbior_vals = form.getlist("os616-odbior")
    if len(odbior_vals) != 1 or odbior_vals[0] not in ODBIORY:
        raise ValueError("OŚ-6165: wybierz jeden sposób odbioru zaświadczenia.")
    return wartosci | {"odbior": odbior_vals[0]}


def kontekst(dane):
    wartosci = dane["os616"]
    return {
        **wartosci,
        "wnioskodawca": wartosci["wnioskodawca"].replace("\n", "\n"),
        "miejscowosc_data": f"Nowy Targ, dnia {wartosci['data']}",
    }


def zastosuj(zawartosc, wybrane):
    d = Document(io.BytesIO(zawartosc))
    for p in d.paragraphs:
        for r in p.runs:
            if r.style.name.startswith("OS616_ODBIOR_"):
                kod = r.style.name[len("OS616_ODBIOR_"):].lower()
                r.text = "☒" if kod == wybrane.get("odbior") else "☐"
    out = io.BytesIO()
    d.save(out)
    return out.getvalue()
