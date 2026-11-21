"""Dane i warianty formularza zgłoszenia budowy PB-2."""
from __future__ import annotations
import datetime
import io
from docx import Document

POLA = {
    "roboty": ("Rodzaj, zakres i sposób wykonywania robót", 1200),
    "termin": ("Planowany termin rozpoczęcia", 10),
}
ADRES = ("kraj", "wojewodztwo", "powiat", "gmina", "ulica", "nr_domu", "nr_lokalu", "miejscowosc", "kod_pocztowy", "adres_elektroniczny", "email", "telefon")

def odczytaj(f, dane):
    wynik = {k: f.get("pb2-" + k, "").strip() for k in POLA}
    for k, (_, limit) in POLA.items():
        if len(f.getlist("pb2-" + k)) > 1 or len(wynik[k]) > limit:
            raise ValueError("PB-2: niepoprawna lub za długa wartość pola.")
    if not wynik["roboty"]:
        raise ValueError("PB-2: opisz rodzaj, zakres i sposób wykonywania robót.")
    if wynik["termin"]:
        try:
            dt = datetime.datetime.strptime(wynik["termin"], "%d.%m.%Y")
            if dt.strftime("%d.%m.%Y") != wynik["termin"]:
                raise ValueError()
        except ValueError:
            raise ValueError("PB-2: planowany termin rozpoczęcia musi mieć format DD.MM.RRRR i być poprawną datą.")
    dodatkowe = {}
    for i, _ in enumerate(dane["inwestorzy"]):
        pref = f"pb2-{i}-"
        for k, limit in (("email", 254), ("telefon", 40)):
            if len(f.getlist(pref+k)) > 1 or len(f.get(pref+k, "").strip()) > limit:
                raise ValueError("PB-2: niepoprawny lub za długi e-mail albo numer telefonu.")
        typ = f.get(pref + "typ_pelnomocnika", "")
        if len(f.getlist(pref + "typ_pelnomocnika")) > 1 or typ not in {"", "pelnomocnik", "do_doreczen"}:
            raise ValueError("PB-2: wybierz poprawny rodzaj pełnomocnika.")
        def adres(prefix):
            out = {k: f.get(prefix + k, "").strip() for k in ADRES}
            if any(len(f.getlist(prefix + k)) > 1 or len(v) > (300 if k in {"adres_elektroniczny", "email"} else 120) for k,v in out.items()):
                raise ValueError("PB-2: niepoprawne lub za długie dane adresowe.")
            return out
        koresp = adres(pref + "koresp-")
        proxy = adres(pref + "proxy-")
        proxy["imie_nazwisko"] = f.get(pref+"proxy-imie_nazwisko", "").strip()
        if typ and not proxy["imie_nazwisko"]:
            raise ValueError("PB-2: podaj imię i nazwisko pełnomocnika.")
        if len(proxy["imie_nazwisko"]) > 180:
            raise ValueError("PB-2: imię i nazwisko pełnomocnika jest za długie.")
        zal = {}
        for k in ("oswiadczenie", "pelnomocnictwo", "oplata", "inne"):
            nazwa = pref + "zal-" + k
            vals = f.getlist(nazwa)
            if len(vals) > 1 or (vals and vals[0] != "tak"):
                raise ValueError("PB-2: niepoprawny wybór załącznika.")
            zal[k] = bool(vals)
        opis = f.get(pref + "zal-opis", "").strip()
        if len(opis) > 500:
            raise ValueError("PB-2: opis załącznika jest za długi.")
        dodatkowe[str(i)] = {"typ_pelnomocnika":typ,"email":f.get(pref+"email", "").strip(),"telefon":f.get(pref+"telefon", "").strip(),"korespondencja":koresp,"proxy":proxy,"proxy_nazwa":proxy["imie_nazwisko"],"zalaczniki":zal,"zal_opis":opis}
    wynik["dodatkowe"] = dodatkowe
    return wynik

def zastosuj(wartosc: bytes, opcje: dict) -> bytes:
    d = Document(io.BytesIO(wartosc))
    for p in d.paragraphs:
        for r in p.runs:
            if r.style.name.startswith("PB2_TYP_"):
                r.text=r.text.replace("☐", "☒" if r.style.name[8:].lower()==opcje.get("typ_pelnomocnika") else "☐", 1)
            elif r.style.name.startswith("PB2_ZAL_"):
                key = r.style.name[8:].lower()
                r.text=r.text.replace("☐", "☒" if opcje.get("zalaczniki", {}).get(key) else "☐", 1)
        if "Inne (wymagane przepisami prawa):" in p.text and opcje.get("zal_opis"):
            p.add_run(" " + opcje["zal_opis"])
    out=io.BytesIO();d.save(out);return out.getvalue()
