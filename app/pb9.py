"""Obsługa pól i zaznaczeń dla wniosku PB-9."""
from __future__ import annotations
import datetime
import io
from docx import Document

ADRES = ("kraj", "wojewodztwo", "powiat", "gmina", "ulica", "nr_domu", "nr_lokalu", "miejscowosc", "kod_pocztowy", "adres_elektroniczny", "email", "telefon")
ZALACZNIKI = ("oswiadczenie", "pelnomocnictwo", "oplata", "zgoda")


def odczytaj(f, dane):
    dodatkowe = {}
    for i, _ in enumerate(dane["inwestorzy"]):
        pref = f"pb9-{i}-"
        data = f.get(pref + "data_decyzji", "").strip()
        nr = f.get(pref + "nr_decyzji", "").strip()
        znak = f.get(pref + "znak_sprawy", "").strip()
        nazwa = f.get(pref + "nazwa_zamierzenia", "").strip()
        dotychczasowy = f.get(pref + "dotychczasowy_inwestor", "").strip()
        if not all((data, nr, znak, nazwa, dotychczasowy)):
            raise ValueError("PB-9: uzupełnij dotychczasowego inwestora oraz datę, numer, znak sprawy i nazwę zamierzenia z decyzji.")
        if len(f.getlist(pref + "data_decyzji")) > 1 or len(data) > 10:
            raise ValueError("PB-9: niepoprawna data wydania pozwolenia.")
        try:
            parsed = datetime.datetime.strptime(data, "%d.%m.%Y")
            if parsed.strftime("%d.%m.%Y") != data:
                raise ValueError()
        except ValueError:
            raise ValueError("PB-9: data wydania decyzji musi mieć format DD.MM.RRRR i być poprawną datą.")
        for key, value, limit in (("nr_decyzji", nr, 120), ("znak_sprawy", znak, 120), ("nazwa_zamierzenia", nazwa, 500), ("dotychczasowy_inwestor", dotychczasowy, 180)):
            if len(f.getlist(pref + key)) > 1 or len(value) > limit:
                raise ValueError("PB-9: niepoprawne lub za długie dane decyzji albo dotychczasowego inwestora.")
        typ = f.get(pref + "typ_pelnomocnika", "")
        if len(f.getlist(pref + "typ_pelnomocnika")) > 1 or typ not in {"", "pelnomocnik", "do_doreczen"}:
            raise ValueError("PB-9: wybierz poprawny rodzaj pełnomocnika.")

        def adres(prefix):
            out = {k: f.get(prefix + k, "").strip() for k in ADRES}
            if any(len(f.getlist(prefix + k)) > 1 or len(v) > (300 if k in {"adres_elektroniczny", "email"} else 120) for k, v in out.items()):
                raise ValueError("PB-9: niepoprawne lub za długie dane adresowe.")
            return out

        proxy_name = f.get(pref + "proxy-imie_nazwisko", "").strip()
        if typ and not proxy_name:
            raise ValueError("PB-9: podaj imię i nazwisko pełnomocnika.")
        if len(proxy_name) > 180:
            raise ValueError("PB-9: imię i nazwisko pełnomocnika jest za długie.")
        zal = {}
        for key in ZALACZNIKI:
            vals = f.getlist(pref + "zal-" + key)
            if len(vals) > 1 or (vals and vals[0] != "tak"):
                raise ValueError("PB-9: niepoprawny wybór załącznika.")
            zal[key] = bool(vals)
        for key, limit in (("email", 254), ("telefon", 40)):
            if len(f.getlist(pref + key)) > 1 or len(f.get(pref + key, "").strip()) > limit:
                raise ValueError("PB-9: niepoprawny lub za długi e-mail albo numer telefonu.")
        dodatkowe[str(i)] = {
            "data_decyzji": data, "nr_decyzji": nr, "znak_sprawy": znak,
            "nazwa_zamierzenia": nazwa, "dotychczasowy_inwestor": dotychczasowy,
            "typ_pelnomocnika": typ, "proxy_nazwa": proxy_name,
            "korespondencja": adres(pref + "koresp-"), "proxy": adres(pref + "proxy-"),
            "email": f.get(pref + "email", "").strip(), "telefon": f.get(pref + "telefon", "").strip(),
            "zalaczniki": zal,
        }
    return {"dodatkowe": dodatkowe}


def zastosuj(wartosc: bytes, opcje: dict) -> bytes:
    d = Document(io.BytesIO(wartosc))
    for p in d.paragraphs:
        for r in p.runs:
            styl = r.style.name
            if styl.startswith("PB9_TYP_"):
                r.text = r.text.replace("☐", "☒" if styl[8:].lower() == opcje.get("typ_pelnomocnika") else "☐", 1)
            elif styl.startswith("PB9_ZAL_"):
                r.text = r.text.replace("☐", "☒" if opcje.get("zalaczniki", {}).get(styl[8:].lower()) else "☐", 1)
    out = io.BytesIO()
    d.save(out)
    return out.getvalue()
