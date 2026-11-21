"""Dane i warianty dwustronicowego formularza PB-2a."""
from __future__ import annotations
import datetime
import io
from docx import Document

RODZAJE = {
    "budowa": "Budowa nowego budynku/nowych budynków.",
    "rozbudowa": "Rozbudowa budynku/budynków.",
    "przebudowa": "Przebudowa budynku/budynków.",
    "nadbudowa": "Nadbudowa budynku/budynków.",
    "odbudowa": "Odbudowa budynku/budynków.",
}
ADRES = ("kraj", "wojewodztwo", "powiat", "gmina", "ulica", "nr_domu", "nr_lokalu", "miejscowosc", "kod_pocztowy", "adres_elektroniczny", "email", "telefon")
ZALACZNIKI = ("oswiadczenie", "pelnomocnictwo", "oplata", "projekt", "warunki", "inne")

def odczytaj(f, dane):
    termin=f.get("pb2a-termin", "").strip()
    if len(f.getlist("pb2a-termin"))>1 or len(termin)>10:
        raise ValueError("PB-2a: niepoprawny lub za długi termin rozpoczęcia.")
    if not termin:
        raise ValueError("PB-2a: podaj planowany termin rozpoczęcia robót.")
    try:
        data=datetime.datetime.strptime(termin,"%d.%m.%Y")
        if data.strftime("%d.%m.%Y")!=termin: raise ValueError()
    except ValueError:
        raise ValueError("PB-2a: termin rozpoczęcia musi mieć format DD.MM.RRRR i być poprawną datą.")
    rodzaje=f.getlist("pb2a-rodzaje")
    if len(rodzaje)!=len(set(rodzaje)) or any(x not in RODZAJE for x in rodzaje):
        raise ValueError("PB-2a: wybierz poprawne rodzaje zamierzenia budowlanego.")
    if not rodzaje: raise ValueError("PB-2a: zaznacz co najmniej jeden rodzaj zamierzenia budowlanego.")
    dodatkowe={}
    for i,_ in enumerate(dane["inwestorzy"]):
        pref=f"pb2a-{i}-"
        for k,limit in (("email",254),("telefon",40)):
            if len(f.getlist(pref+k))>1 or len(f.get(pref+k,"").strip())>limit:
                raise ValueError("PB-2a: niepoprawny lub za długi e-mail albo numer telefonu.")
        typ=f.get(pref+"typ_pelnomocnika","")
        if len(f.getlist(pref+"typ_pelnomocnika"))>1 or typ not in {"","pelnomocnik","do_doreczen"}:
            raise ValueError("PB-2a: wybierz poprawny rodzaj pełnomocnika.")
        def adres(prefix):
            out={k:f.get(prefix+k,"").strip() for k in ADRES}
            if any(len(f.getlist(prefix+k))>1 or len(v)>(300 if k in {"adres_elektroniczny","email"} else 120) for k,v in out.items()):
                raise ValueError("PB-2a: niepoprawne lub za długie dane adresowe.")
            return out
        koresp=adres(pref+"koresp-");proxy=adres(pref+"proxy-")
        proxy_name=f.get(pref+"proxy-imie_nazwisko","").strip()
        if typ and not proxy_name: raise ValueError("PB-2a: podaj imię i nazwisko pełnomocnika.")
        if len(proxy_name)>180: raise ValueError("PB-2a: imię i nazwisko pełnomocnika jest za długie.")
        zal={}
        for k in ZALACZNIKI:
            vals=f.getlist(pref+"zal-"+k)
            if len(vals)>1 or (vals and vals[0]!="tak"):
                raise ValueError("PB-2a: niepoprawny wybór załącznika.")
            zal[k]=bool(vals)
        opis=f.get(pref+"zal-opis","").strip()
        if len(opis)>500: raise ValueError("PB-2a: opis załącznika jest za długi.")
        dodatkowe[str(i)]={"typ_pelnomocnika":typ,"email":f.get(pref+"email","").strip(),"telefon":f.get(pref+"telefon","").strip(),"korespondencja":koresp,"proxy":proxy,"proxy_nazwa":proxy_name,"zalaczniki":zal,"zal_opis":opis}
    return {"termin":termin,"rodzaje":rodzaje,"dodatkowe":dodatkowe}

def zastosuj(wartosc:bytes, opcje:dict)->bytes:
    d=Document(io.BytesIO(wartosc))
    for p in d.paragraphs:
        for r in p.runs:
            styl=r.style.name
            if styl.startswith("PB2A_TYP_"):
                r.text=r.text.replace("☐", "☒" if styl[9:].lower()==opcje.get("typ_pelnomocnika") else "☐",1)
            elif styl.startswith("PB2A_RODZAJ_"):
                r.text=r.text.replace("☐", "☒" if styl[12:].lower() in opcje.get("rodzaje",[]) else "☐",1)
            elif styl.startswith("PB2A_ZAL_"):
                r.text=r.text.replace("☐", "☒" if opcje.get("zalaczniki",{}).get(styl[9:].lower()) else "☐",1)
        if "Inne (wymagane przepisami prawa):" in p.text and opcje.get("zal_opis"):
            p.add_run(" "+opcje["zal_opis"])
    out=io.BytesIO();d.save(out);return out.getvalue()
