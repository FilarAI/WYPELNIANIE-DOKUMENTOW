"""Obsługa danych i pól wyboru dla wniosku PB-1."""
from __future__ import annotations
import io
from docx import Document

RODZAJE = {
    "budowa": "Budowa nowego obiektu budowlanego.",
    "rozbudowa": "Rozbudowa istniejącego obiektu budowlanego.",
    "nadbudowa": "Nadbudowa istniejącego obiektu budowlanego.",
    "odbudowa": "Odbudowa obiektu budowlanego.",
    "inne_roboty": "Wykonanie robót budowlanych innych niż wymienione.",
}
ADRES = ("kraj", "wojewodztwo", "powiat", "gmina", "ulica", "nr_domu", "nr_lokalu", "miejscowosc", "kod_pocztowy", "adres_elektroniczny", "email", "telefon")
ZALACZNIKI = ("oswiadczenie", "pelnomocnictwo", "oplata", "projekt", "warunki", "inne")


def odczytaj(f, dane):
    nazwa = " ".join(f.get("pb1-nazwa", "").split())
    if not nazwa:
        raise ValueError("PB-1: podaj ogólną nazwę zamierzenia budowlanego.")
    if len(f.getlist("pb1-nazwa")) > 1 or len(nazwa) > 500:
        raise ValueError("PB-1: nazwa zamierzenia jest za długa lub niepoprawna.")
    rodzaje = [x for x in f.getlist("pb1-rodzaje") if x]
    if not rodzaje:
        raise ValueError("PB-1: zaznacz co najmniej jeden rodzaj zamierzenia budowlanego.")
    if len(rodzaje) != len(set(rodzaje)) or any(x not in RODZAJE for x in rodzaje):
        raise ValueError("PB-1: wybierz poprawne rodzaje zamierzenia budowlanego.")
    dodatkowe = {}
    for i, _ in enumerate(dane["inwestorzy"]):
        pref = f"pb1-{i}-"
        typ = f.get(pref + "typ_pelnomocnika", "")
        if len(f.getlist(pref + "typ_pelnomocnika")) > 1 or typ not in {"", "pelnomocnik", "do_doreczen"}:
            raise ValueError("PB-1: wybierz poprawny rodzaj pełnomocnika.")

        def adres(prefix):
            out = {k: f.get(prefix + k, "").strip() for k in ADRES}
            if any(len(f.getlist(prefix + k)) > 1 or len(v) > (300 if k in {"adres_elektroniczny", "email"} else 120) for k, v in out.items()):
                raise ValueError("PB-1: niepoprawne lub za długie dane adresowe.")
            return out

        proxy_name = f.get(pref + "proxy-imie_nazwisko", "").strip()
        if typ and not proxy_name:
            raise ValueError("PB-1: podaj imię i nazwisko pełnomocnika.")
        if len(proxy_name) > 180:
            raise ValueError("PB-1: imię i nazwisko pełnomocnika jest za długie.")
        for key, limit in (("email", 254), ("telefon", 40)):
            if len(f.getlist(pref + key)) > 1 or len(f.get(pref + key, "").strip()) > limit:
                raise ValueError("PB-1: niepoprawny lub za długi e-mail albo numer telefonu.")
        zal = {}
        for key in ZALACZNIKI:
            vals = f.getlist(pref + "zal-" + key)
            if len(vals) > 1 or (vals and vals[0] != "tak"):
                raise ValueError("PB-1: niepoprawny wybór załącznika.")
            zal[key] = bool(vals)
        opis = f.get(pref + "zal-opis", "").strip()
        if len(opis) > 500:
            raise ValueError("PB-1: opis innych załączników jest za długi.")
        dodatkowe[str(i)] = {
            "typ_pelnomocnika": typ, "proxy_nazwa": proxy_name,
            "email": f.get(pref + "email", "").strip(), "telefon": f.get(pref + "telefon", "").strip(),
            "korespondencja": adres(pref + "koresp-"), "proxy": adres(pref + "proxy-"),
            "zalaczniki": zal, "zal_opis": opis,
        }
    return {"nazwa": nazwa, "rodzaje": rodzaje, "dodatkowe": dodatkowe}


def zastosuj(wartosc: bytes, opcje: dict) -> bytes:
    d = Document(io.BytesIO(wartosc))
    for p in d.paragraphs:
        for r in p.runs:
            styl = r.style.name
            if styl.startswith("PB1_TYP_"):
                r.text = r.text.replace("☐", "☒" if styl[8:].lower() in opcje.get("rodzaje", []) else "☐", 1)
            elif styl.startswith("PB1_PEL_"):
                r.text = r.text.replace("☐", "☒" if styl[8:].lower() == opcje.get("typ_pelnomocnika") else "☐", 1)
            elif styl.startswith("PB1_ZAL_"):
                r.text = r.text.replace("☐", "☒" if opcje.get("zalaczniki", {}).get(styl[8:].lower()) else "☐", 1)
        if "Inne (wymagane przepisami prawa):" in p.text and opcje.get("zal_opis"):
            p.add_run(" " + opcje["zal_opis"])
    out = io.BytesIO()
    d.save(out)
    return out.getvalue()
